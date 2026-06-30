from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import CollectionEvent, EventFieldValue, Plot, Point


class CoffeeResubmitApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="collector-resubmit",
            password="collector-pass",
            name="采集员",
            mobile="13800000004",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606250601",
            task_code="TASK202606250006",
            name="重提地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("10.00"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606250601",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.event = CollectionEvent.objects.create(
            event_id="EV202606250601",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            collector_id=str(self.user.id),
            idempotency_key="resubmit-original-key",
            status=CollectionEvent.STATUS_RETURNED,
            manifest_hash="manifest-v1",
            version=1,
        )
        EventFieldValue.objects.create(
            event=self.event,
            field_code="air_temperature",
            field_label="空气温度",
            value_text="21.0",
            value_number=Decimal("21.0"),
            source_type=EventFieldValue.SOURCE_OCR,
            ocr_raw_value="21.0",
            version=1,
        )

    def test_resubmit_returned_event_appends_version_without_overwriting_original_fields(self):
        response = self.client.post(
            f"/api/coffee/app/events/{self.event.event_id}/resubmit/",
            {
                "idempotency_key": "resubmit-key-v2",
                "manifest": {"manifest_hash": "manifest-v2"},
                "field_values": [
                    {
                        "field_code": "air_temperature",
                        "field_label": "空气温度",
                        "value_text": "22.5",
                        "value_number": "22.5",
                        "source_type": "ocr",
                        "ocr_raw_value": "21.0",
                        "corrected_from": "21.0",
                        "correction_reason": "退回复核后按设备屏幕修正",
                    }
                ],
                "measurements": [
                    {
                        "device_no": "ENV-001",
                        "air_temperature": "22.5",
                        "is_abnormal": False,
                    }
                ],
                "submit_note": "退回后重新提交",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, CollectionEvent.STATUS_SUBMITTED)
        self.assertEqual(self.event.version, 2)
        self.assertEqual(self.event.manifest_hash, "manifest-v2")
        self.assertEqual(
            list(self.event.field_values.order_by("version").values_list("value_text", "version")),
            [("21.0", 1), ("22.5", 2)],
        )
        self.assertEqual(self.event.measurements.count(), 1)

    def test_resubmit_rejects_events_that_are_not_returned(self):
        self.event.status = CollectionEvent.STATUS_SUBMITTED
        self.event.save(update_fields=["status"])

        response = self.client.post(
            f"/api/coffee/app/events/{self.event.event_id}/resubmit/",
            {"idempotency_key": "resubmit-key-v2"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "COFFEE_EVENT_NOT_RETURNED")
