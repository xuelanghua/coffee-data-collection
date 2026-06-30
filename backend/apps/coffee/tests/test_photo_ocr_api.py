from decimal import Decimal
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import (
    CollectionEvent,
    OCRCorrection,
    OCRResult,
    PhotoAsset,
    Plot,
    Point,
    ProviderConfig,
    ProviderCallLog,
)


class FakeHttpResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class CoffeePhotoOcrApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="collector-ocr",
            password="collector-pass",
            name="现场采集员",
            mobile="13800000001",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606240201",
            task_code="TASK202606240002",
            name="现场圈选地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("12.34"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606240201",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.event = CollectionEvent.objects.create(
            event_id="EV202606240201",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key="event-idem-ocr-001",
            manifest_hash="draft-manifest-hash",
        )

    def _create_uploaded_photo(self, photo_id="PH202606240201"):
        PhotoAsset.objects.create(
            photo_id=photo_id,
            event=self.event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            original_file=f"uploads/original/{photo_id}.jpg",
            watermarked_file=f"uploads/watermarked/{photo_id}.jpg",
            sha256="abc123",
            metadata_json={"gps": {"longitude": 100.0005, "latitude": 22.0005}},
            precheck_status=PhotoAsset.PRECHECK_PASS,
            immutable_status=PhotoAsset.IMMUTABLE_LOCKED,
        )

    def test_paddleocr_provider_adapter_calls_configured_endpoint_and_records_result(self):
        self._create_uploaded_photo("PH202606240299")
        ProviderConfig.objects.create(
            provider_type=ProviderConfig.TYPE_OCR,
            provider_name=OCRResult.PROVIDER_PADDLE,
            display_name="本地 PaddleOCR",
            enabled=True,
            priority=10,
            timeout_ms=5000,
            config_status=ProviderConfig.STATUS_TESTED,
            config_json={"endpoint": "http://paddleocr.local/predict", "template": "device_reading_v1"},
        )
        provider_payload = {
            "provider": "paddleocr",
            "status": "success",
            "fields": [
                {"name": "wind_speed", "value": "1.8", "confidence": 0.91},
                {"name": "air_temperature", "value": "23.6", "confidence": 0.93},
                {"name": "soil_ph", "value": "6.4", "confidence": 0.88},
            ],
            "raw_ref": "mock-raw-ref",
        }

        with patch("apps.coffee.providers.urllib.request.urlopen", return_value=FakeHttpResponse(provider_payload)) as urlopen:
            response = self.client.post(
                f"/api/coffee/app/events/{self.event.event_id}/ocr/",
                {"photo_id": "PH202606240299", "provider": OCRResult.PROVIDER_PADDLE},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["provider"], OCRResult.PROVIDER_PADDLE)
        self.assertEqual(data["status"], OCRResult.STATUS_SUCCESS)
        self.assertEqual(data["structured_json"]["air_temperature"]["value"], "23.6")
        self.assertEqual(data["structured_json"]["soil_ph"]["confidence"], 0.88)
        self.assertEqual(data["confidence"], "0.9067")
        self.assertEqual(ProviderCallLog.objects.filter(provider_name=OCRResult.PROVIDER_PADDLE, status=ProviderCallLog.STATUS_SUCCESS).count(), 1)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://paddleocr.local/predict")
        request_payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request_payload["photo_id"], "PH202606240299")
        self.assertEqual(request_payload["template"], "device_reading_v1")

    def test_photo_upload_and_ocr_correction_are_recorded_before_submit(self):
        init_response = self.client.post(
            "/api/coffee/app/photos/init/",
            {
                "event_id": self.event.event_id,
                "photo_id": "PH202606240201",
                "category": "device_reading",
                "sha256": "abc123",
                "metadata": {"gps": {"longitude": 100.0005, "latitude": 22.0005}},
            },
            format="json",
        )

        self.assertEqual(init_response.status_code, 200)
        self.assertEqual(init_response.data["data"]["photo_id"], "PH202606240201")
        self.assertEqual(init_response.data["data"]["precheck_status"], PhotoAsset.PRECHECK_PENDING)

        complete_response = self.client.post(
            "/api/coffee/app/photos/PH202606240201/complete/",
            {
                "original_file": "uploads/original/PH202606240201.jpg",
                "watermarked_file": "uploads/watermarked/PH202606240201.jpg",
                "sha256": "abc123",
                "precheck_status": PhotoAsset.PRECHECK_PASS,
            },
            format="json",
        )

        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(complete_response.data["data"]["immutable_status"], PhotoAsset.IMMUTABLE_LOCKED)

        ocr_response = self.client.post(
            f"/api/coffee/app/events/{self.event.event_id}/ocr/",
            {
                "photo_id": "PH202606240201",
                "provider": OCRResult.PROVIDER_MANUAL,
                "structured_json": {"air_temperature": {"value": "23.8", "confidence": 0.91}},
                "raw_response": {"text": "空气温度 23.8"},
                "confidence": "0.91",
            },
            format="json",
        )

        self.assertEqual(ocr_response.status_code, 200)
        self.assertEqual(ocr_response.data["data"]["status"], OCRResult.STATUS_SUCCESS)
        ocr_result_id = ocr_response.data["data"]["ocr_result_id"]

        correction_response = self.client.post(
            f"/api/coffee/app/ocr-results/{ocr_result_id}/corrections/",
            {
                "field_name": "air_temperature",
                "raw_value": "23.8",
                "corrected_value": "23.6",
                "reason": "人工核对设备采集屏幕",
            },
            format="json",
        )

        self.assertEqual(correction_response.status_code, 200)
        self.assertEqual(correction_response.data["data"]["version"], 1)

        list_response = self.client.get(f"/api/coffee/app/events/{self.event.event_id}/ocr-results/")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["data"]), 1)
        self.assertEqual(list_response.data["data"][0]["corrections"][0]["corrected_value"], "23.6")
        self.assertEqual(PhotoAsset.objects.get(photo_id="PH202606240201").precheck_status, PhotoAsset.PRECHECK_PASS)
        self.assertEqual(OCRResult.objects.count(), 1)
        self.assertEqual(OCRCorrection.objects.count(), 1)
        self.assertEqual(ProviderCallLog.objects.count(), 1)
