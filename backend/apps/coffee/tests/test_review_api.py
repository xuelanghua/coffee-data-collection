from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import CollectionEvent, Plot, Point, QualityReview


class CoffeeReviewApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reviewer-api",
            password="reviewer-pass",
            name="审核员",
            mobile="13800000003",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606240501",
            task_code="TASK202606240005",
            name="审核地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("10.00"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606240501",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )

    def create_event(self, suffix):
        return CollectionEvent.objects.create(
            event_id=f"EV2026062405{suffix}",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key=f"review-idem-{suffix}",
            status=CollectionEvent.STATUS_SUBMITTED,
            manifest_hash=f"manifest-{suffix}",
        )

    def test_single_approve_and_return_create_review_records(self):
        approved_event = self.create_event("01")
        returned_event = self.create_event("02")

        approve_response = self.client.post(
            f"/api/coffee/events/{approved_event.event_id}/review/approve/",
            {"review_note": "单条审核通过"},
            format="json",
        )
        return_response = self.client.post(
            f"/api/coffee/events/{returned_event.event_id}/review/return/",
            {
                "return_reason": "OCR_OR_MEASUREMENT_ERROR",
                "return_note": "设备采集数据需重新校准",
                "return_items": ["ocr", "measurement"],
            },
            format="json",
        )

        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(return_response.status_code, 200)
        approved_event.refresh_from_db()
        returned_event.refresh_from_db()
        self.assertEqual(approved_event.status, CollectionEvent.STATUS_APPROVED)
        self.assertEqual(returned_event.status, CollectionEvent.STATUS_RETURNED)
        self.assertEqual(QualityReview.objects.get(event=approved_event).status, QualityReview.STATUS_APPROVED)
        self.assertEqual(QualityReview.objects.get(event=returned_event).return_items, ["ocr", "measurement"])

    def test_bulk_approve_and_return_create_individual_review_records(self):
        approve_events = [self.create_event("11"), self.create_event("12")]
        return_events = [self.create_event("21"), self.create_event("22")]

        bulk_approve_response = self.client.post(
            "/api/coffee/events/review/bulk-approve/",
            {"event_ids": [event.event_id for event in approve_events], "review_note": "批量审核通过"},
            format="json",
        )
        bulk_return_response = self.client.post(
            "/api/coffee/events/review/bulk-return/",
            {
                "event_ids": [event.event_id for event in return_events],
                "return_reason": "PHOTO_QUALITY_ERROR",
                "return_note": "设备屏幕照片需补拍",
                "return_items": ["photo"],
            },
            format="json",
        )

        self.assertEqual(bulk_approve_response.status_code, 200)
        self.assertEqual(bulk_return_response.status_code, 200)
        self.assertEqual(bulk_approve_response.data["data"]["success"], ["EV202606240511", "EV202606240512"])
        self.assertEqual(bulk_return_response.data["data"]["success"], ["EV202606240521", "EV202606240522"])
        self.assertEqual(QualityReview.objects.count(), 4)
        self.assertEqual(CollectionEvent.objects.filter(status=CollectionEvent.STATUS_APPROVED).count(), 2)
        self.assertEqual(CollectionEvent.objects.filter(status=CollectionEvent.STATUS_RETURNED).count(), 2)
