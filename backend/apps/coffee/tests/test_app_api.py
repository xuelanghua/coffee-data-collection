from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import (
    CollectionEvent,
    EventFieldValue,
    MeasurementRecord,
    Plot,
    PlotBoundaryVersion,
    Point,
)


class CoffeeAppApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="collector",
            password="collector-pass",
            name="现场采集员",
            mobile="13800000000",
        )
        self.client.force_authenticate(self.user)

    def test_app_field_collection_backend_loop_accepts_submit_once(self):
        boundary = {
            "type": "Polygon",
            "coordinates": [
                [
                    [100.0, 22.0],
                    [100.001, 22.0],
                    [100.001, 22.001],
                    [100.0, 22.001],
                    [100.0, 22.0],
                ]
            ],
        }

        plot_response = self.client.post(
            "/api/coffee/app/plots/",
            {
                "task_id": "TASK202606240001",
                "plot_id": "PL202606240101",
                "name": "现场圈选地块",
                "boundary_geojson": boundary,
                "area_mu": "12.34",
                "area_calc_method": Plot.AREA_GEODESIC,
                "coordinate_system": Plot.COORD_GCJ02,
                "source_type": Plot.SOURCE_APP_DRAWN,
                "idempotency_key": "plot-idem-001",
            },
            format="json",
        )

        self.assertEqual(plot_response.status_code, 200)
        self.assertEqual(plot_response.data["data"]["plot_id"], "PL202606240101")
        self.assertEqual(plot_response.data["data"]["review_status"], Plot.REVIEW_PENDING)
        self.assertEqual(PlotBoundaryVersion.objects.count(), 1)

        point_response = self.client.post(
            "/api/coffee/app/points/",
            {
                "task_id": "TASK202606240001",
                "plot_id": "PL202606240101",
                "point_id": "PT202606240101",
                "longitude": "100.0005",
                "latitude": "22.0005",
                "altitude": "1200.5",
                "coordinate_system": Point.COORD_GCJ02,
                "source_type": Point.SOURCE_APP_SELECTED,
                "idempotency_key": "point-idem-001",
            },
            format="json",
        )

        self.assertEqual(point_response.status_code, 200)
        self.assertEqual(point_response.data["data"]["point_id"], "PT202606240101")
        self.assertEqual(point_response.data["data"]["review_status"], Point.REVIEW_PENDING)

        event_response = self.client.post(
            "/api/coffee/app/events/",
            {
                "task_id": "TASK202606240001",
                "plot_id": "PL202606240101",
                "point_id": "PT202606240101",
                "event_id": "EV202606240101",
                "idempotency_key": "event-idem-001",
                "manifest_hash": "draft-manifest-hash",
                "location_snapshot": {"longitude": 100.0005, "latitude": 22.0005},
                "weather_snapshot": {"source": "manual"},
            },
            format="json",
        )

        self.assertEqual(event_response.status_code, 200)
        self.assertEqual(event_response.data["data"]["event_id"], "EV202606240101")
        self.assertEqual(event_response.data["data"]["status"], CollectionEvent.STATUS_DRAFT)

        submit_response = self.client.post(
            "/api/coffee/app/events/EV202606240101/submit/",
            {
                "idempotency_key": "event-idem-001",
                "manifest": {
                    "event_id": "EV202606240101",
                    "plot_id": "PL202606240101",
                    "point_id": "PT202606240101",
                    "manifest_hash": "submitted-manifest-hash",
                },
                "field_values": [
                    {
                        "field_code": "air_temperature",
                        "field_label": "空气温度",
                        "value_text": "23.6",
                        "value_number": "23.6",
                        "unit": "摄氏度",
                        "source_type": EventFieldValue.SOURCE_OCR,
                        "source_photo_id": "PH202606240101",
                        "ocr_result_id": "OCR202606240101",
                        "ocr_raw_value": "23.8",
                        "ocr_confidence": "0.91",
                        "corrected_from": "23.8",
                        "correction_reason": "人工核对设备采集屏幕",
                    }
                ],
                "measurements": [
                    {
                        "device_no": "ENV-001",
                        "wind_speed": "1.80",
                        "wind_direction": "东南",
                        "air_temperature": "23.60",
                        "air_humidity": "72.00",
                        "atmospheric_pressure": "90.80",
                        "rainfall": "0.00",
                        "soil_moisture": "38.50",
                        "soil_temperature": "21.40",
                        "soil_salinity": "0.18",
                        "soil_ph": "6.40",
                        "source_photo_id": "PH202606240101",
                        "ocr_result_id": "OCR202606240101",
                    }
                ],
                "ocr_corrections": [],
                "submit_note": "现场采集完成",
            },
            format="json",
        )

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["data"]["status"], CollectionEvent.STATUS_SUBMITTED)

        event = CollectionEvent.objects.get(event_id="EV202606240101")
        self.assertEqual(event.status, CollectionEvent.STATUS_SUBMITTED)
        self.assertEqual(event.manifest_hash, "submitted-manifest-hash")
        self.assertEqual(event.field_values.get(field_code="air_temperature").corrected_from, "23.8")
        self.assertEqual(event.measurements.get().soil_ph, Decimal("6.40"))

        duplicate_response = self.client.post(
            "/api/coffee/app/events/EV202606240101/submit/",
            {
                "idempotency_key": "event-idem-001",
                "manifest": {"manifest_hash": "submitted-manifest-hash"},
                "field_values": [],
                "measurements": [],
            },
            format="json",
        )

        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(duplicate_response.data["data"]["status"], CollectionEvent.STATUS_SUBMITTED)
        self.assertEqual(MeasurementRecord.objects.count(), 1)
        self.assertEqual(EventFieldValue.objects.count(), 1)

    def test_submit_preserves_abnormal_measurement_and_links_retake_record(self):
        plot = Plot.objects.create(
            plot_id="PL202606240201",
            task_code="TASK202606240002",
            name="复测地块",
            boundary_geojson={"type": "Polygon", "coordinates": []},
            area_mu=Decimal("1.00"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
        )
        point = Point.objects.create(
            point_id="PT202606240201",
            task_code=plot.task_code,
            plot=plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
        )
        CollectionEvent.objects.create(
            event_id="EV202606240201",
            task_code=plot.task_code,
            plot=plot,
            point=point,
            collector_id=str(self.user.id),
            idempotency_key="event-idem-retake",
            manifest_hash="draft-retake-manifest",
        )

        submit_response = self.client.post(
            "/api/coffee/app/events/EV202606240201/submit/",
            {
                "idempotency_key": "event-idem-retake",
                "manifest": {"manifest_hash": "retake-manifest-hash"},
                "field_values": [],
                "measurements": [
                    {
                        "client_measurement_id": "MEASURE-001",
                        "device_no": "ENV-001",
                        "soil_ph": "5.20",
                        "is_abnormal": True,
                        "remark": "土壤 PH 异常，现场复测",
                    },
                    {
                        "client_measurement_id": "MEASURE-001-RETAKE-001",
                        "retake_of_client_id": "MEASURE-001",
                        "device_no": "ENV-001",
                        "soil_ph": "6.70",
                        "is_abnormal": False,
                        "remark": "复测通过",
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(submit_response.status_code, 200)
        abnormal = MeasurementRecord.objects.get(is_abnormal=True)
        retake = MeasurementRecord.objects.get(is_abnormal=False)
        self.assertEqual(abnormal.soil_ph, Decimal("5.20"))
        self.assertEqual(retake.soil_ph, Decimal("6.70"))
        self.assertEqual(retake.retake_of_id, abnormal.id)

    def test_submit_rejects_event_owned_by_another_collector(self):
        plot = Plot.objects.create(
            plot_id="PL202606240301",
            task_code="TASK202606240003",
            name="权限地块",
            boundary_geojson={"type": "Polygon", "coordinates": []},
            area_mu=Decimal("1.00"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
        )
        point = Point.objects.create(
            point_id="PT202606240301",
            task_code=plot.task_code,
            plot=plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
        )
        CollectionEvent.objects.create(
            event_id="EV202606240301",
            task_code=plot.task_code,
            plot=plot,
            point=point,
            collector_id=str(self.user.id),
            idempotency_key="event-idem-owned",
            manifest_hash="draft-owned-manifest",
        )
        other_user = get_user_model().objects.create_user(
            username="other-collector",
            password="collector-pass",
            name="其他采集员",
            mobile="13800000001",
        )
        self.client.force_authenticate(other_user)

        submit_response = self.client.post(
            "/api/coffee/app/events/EV202606240301/submit/",
            {
                "idempotency_key": "event-idem-owned",
                "manifest": {"manifest_hash": "stolen-manifest-hash"},
                "field_values": [],
                "measurements": [],
            },
            format="json",
        )

        self.assertEqual(submit_response.status_code, 403)
        event = CollectionEvent.objects.get(event_id="EV202606240301")
        self.assertEqual(event.status, CollectionEvent.STATUS_DRAFT)
        self.assertEqual(event.manifest_hash, "draft-owned-manifest")
