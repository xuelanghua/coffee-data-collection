import json
import tempfile
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import (
    CollectionEvent,
    EventFieldValue,
    MeasurementRecord,
    OCRCorrection,
    OCRResult,
    PhotoAsset,
    Plot,
    Point,
    ProviderCallLog,
)


class CoffeeWebEventDetailApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            password="reviewer-pass",
            name="审核员",
            mobile="13800000002",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606240301",
            task_code="TASK202606240003",
            name="Web详情地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("18.66"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606240301",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.event = CollectionEvent.objects.create(
            event_id="EV202606240301",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key="web-detail-idem-001",
            status=CollectionEvent.STATUS_SUBMITTED,
            manifest_hash="submitted-manifest-hash",
        )
        self.photo = PhotoAsset.objects.create(
            photo_id="PH202606240301",
            event=self.event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            original_file="uploads/original/PH202606240301.jpg",
            watermarked_file="uploads/watermarked/PH202606240301.jpg",
            sha256="abc123",
            metadata_json={"gps": {"longitude": 100.0005, "latitude": 22.0005}},
            precheck_status=PhotoAsset.PRECHECK_PASS,
            immutable_status=PhotoAsset.IMMUTABLE_LOCKED,
        )
        self.ocr_result = OCRResult.objects.create(
            ocr_result_id="OCR202606240301",
            photo=self.photo,
            provider=OCRResult.PROVIDER_MANUAL,
            status=OCRResult.STATUS_SUCCESS,
            raw_response_id="RAW202606240301",
            raw_response_json={"text": "空气温度 23.8"},
            structured_json={"air_temperature": {"value": "23.8", "confidence": 0.91}},
            confidence=Decimal("0.9100"),
        )
        OCRCorrection.objects.create(
            ocr_result=self.ocr_result,
            field_name="air_temperature",
            raw_value="23.8",
            corrected_value="23.6",
            reason="人工核对设备采集屏幕",
            version=1,
            corrected_by=str(self.user.id),
        )
        MeasurementRecord.objects.create(
            event=self.event,
            device_no="ENV-001",
            air_temperature=Decimal("23.60"),
            soil_ph=Decimal("6.40"),
            source_photo_id=self.photo.photo_id,
            ocr_result_id=self.ocr_result.ocr_result_id,
        )
        EventFieldValue.objects.create(
            event=self.event,
            field_code="air_temperature",
            field_label="空气温度",
            value_text="23.6",
            value_number=Decimal("23.6000"),
            unit="摄氏度",
            source_type=EventFieldValue.SOURCE_OCR,
            source_photo_id=self.photo.photo_id,
            ocr_result_id=self.ocr_result.ocr_result_id,
            ocr_raw_value="23.8",
            ocr_confidence=Decimal("0.9100"),
            corrected_from="23.8",
            correction_reason="人工核对设备采集屏幕",
        )
        ProviderCallLog.objects.create(
            provider_type="ocr",
            provider_name=OCRResult.PROVIDER_MANUAL,
            request_id=self.ocr_result.ocr_result_id,
            target_type="photo",
            target_id=self.photo.photo_id,
            status=ProviderCallLog.STATUS_SUCCESS,
        )

    def test_web_event_detail_aggregates_plot_photo_ocr_measurement_and_fields(self):
        response = self.client.get(f"/api/coffee/events/{self.event.event_id}/")

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["event"]["event_id"], self.event.event_id)
        self.assertEqual(data["plot"]["plot_id"], self.plot.plot_id)
        self.assertEqual(data["point"]["point_id"], self.point.point_id)
        self.assertEqual(data["field_values"][0]["field_code"], "air_temperature")
        self.assertEqual(data["measurements"][0]["soil_ph"], "6.40")
        self.assertEqual(data["photos"][0]["photo"]["photo_id"], self.photo.photo_id)
        self.assertEqual(data["photos"][0]["ocr_results"][0]["ocr_result_id"], self.ocr_result.ocr_result_id)
        self.assertEqual(data["photos"][0]["ocr_results"][0]["corrections"][0]["corrected_value"], "23.6")
        self.assertEqual(data["audit_logs"][0]["request_id"], self.ocr_result.ocr_result_id)
        self.assertEqual(data["quality_reviews"], [])
        package_index = data["offline_package_index"]
        self.assertEqual(package_index["package_version"], 1)
        self.assertEqual(package_index["event_id"], self.event.event_id)
        self.assertEqual(package_index["manifest_hash"], self.event.manifest_hash)
        self.assertEqual(package_index["resources"]["plot"]["plot_id"], self.plot.plot_id)
        self.assertEqual(package_index["resources"]["point"]["point_id"], self.point.point_id)
        self.assertEqual(package_index["resources"]["photos"][0]["photo_id"], self.photo.photo_id)
        self.assertEqual(package_index["resources"]["photos"][0]["sha256"], self.photo.sha256)
        self.assertEqual(package_index["resources"]["photos"][0]["files"]["original"], self.photo.original_file)
        self.assertEqual(package_index["resources"]["ocr_results"][0]["ocr_result_id"], self.ocr_result.ocr_result_id)
        self.assertEqual(package_index["resource_counts"]["photos"], 1)
        self.assertEqual(package_index["resource_counts"]["measurements"], 1)
        self.assertIn("index_hash", package_index)

    def test_event_offline_package_builder_writes_manifest_and_browser_index(self):
        from apps.coffee.offline_package import build_event_offline_package

        with tempfile.TemporaryDirectory() as temp_dir:
            package = build_event_offline_package(self.event, Path(temp_dir))
            package_dir = Path(package["package_dir"])
            manifest_path = package_dir / "manifest.json"
            index_path = package_dir / "index.html"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(index_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            index_html = index_path.read_text(encoding="utf-8")

            self.assertEqual(manifest["event_id"], self.event.event_id)
            self.assertEqual(manifest["offline_package_index"]["event_id"], self.event.event_id)
            self.assertEqual(manifest["offline_package_index"]["resources"]["photos"][0]["photo_id"], self.photo.photo_id)
            self.assertIn("manifest.json", package["files"])
            self.assertIn("index.html", package["files"])
            self.assertIn("package_hash", package)
            self.assertIn(self.event.event_id, index_html)
            self.assertIn("离线数据包", index_html)

    def test_event_offline_package_builder_copies_controlled_photo_files(self):
        from apps.coffee.offline_package import build_event_offline_package

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            media_root = root / "media"
            watermarked_path = media_root / self.photo.watermarked_file
            watermarked_path.parent.mkdir(parents=True)
            watermarked_path.write_bytes(b"controlled-watermarked-photo")

            package = build_event_offline_package(self.event, root / "packages", media_root=media_root)
            package_dir = Path(package["package_dir"])
            controlled_file = package_dir / "photos" / "controlled" / f"{self.photo.photo_id}.jpg"
            manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
            photo_resource = manifest["offline_package_index"]["resources"]["photos"][0]

            self.assertTrue(controlled_file.exists())
            self.assertEqual(controlled_file.read_bytes(), b"controlled-watermarked-photo")
            self.assertIn("photos/controlled/PH202606240301.jpg", package["files"])
            self.assertEqual(photo_resource["files"]["controlled"], "photos/controlled/PH202606240301.jpg")
            self.assertIn("photos/controlled/PH202606240301.jpg", (package_dir / "index.html").read_text(encoding="utf-8"))
