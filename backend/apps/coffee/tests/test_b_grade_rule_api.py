from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import CollectionEvent, Plot, Point, QualityReview


class CoffeeBGradeRuleApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="bgrade-admin",
            password="bgrade-pass",
            name="B级规则管理员",
            mobile="13800000006",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606250601",
            task_code="TASK202606250006",
            name="B级规则地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("6.50"),
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
        for index, status in enumerate([CollectionEvent.STATUS_APPROVED, CollectionEvent.STATUS_APPROVED, CollectionEvent.STATUS_RETURNED], start=1):
            event = CollectionEvent.objects.create(
                event_id=f"EV20260625060{index}",
                task_code=self.plot.task_code,
                plot=self.plot,
                point=self.point,
                collector_id="collector-b",
                idempotency_key=f"bgrade-idem-{index}",
                status=status,
                manifest_hash=f"bgrade-manifest-{index}",
            )
            if status == CollectionEvent.STATUS_RETURNED:
                QualityReview.objects.create(
                    event=event,
                    review_type=QualityReview.REVIEW_TYPE_EVENT,
                    status=QualityReview.STATUS_RETURNED,
                    reviewer_id=str(self.user.id),
                    return_reason="B级规则不通过",
                    return_items=["b_grade"],
                    version=1,
                )

    def test_b_grade_rule_create_list_and_check_pass(self):
        create_response = self.client.post(
            "/api/coffee/b-grade-rules/",
            {
                "rule_name": "B级通过数至少2条",
                "task_id": self.plot.task_code,
                "metric": "approved_event_count",
                "min_count": 2,
                "max_count": 5,
                "block_level": "blocking",
                "enabled": True,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)
        rule = create_response.data["data"]
        self.assertEqual(rule["version"], 1)
        self.assertEqual(rule["enabled"], True)

        list_response = self.client.get("/api/coffee/b-grade-rules/", {"task_id": self.plot.task_code})
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["data"]["count"], 1)

        check_response = self.client.post(f"/api/coffee/b-grade-rules/{rule['rule_code']}/check/", {}, format="json")
        self.assertEqual(check_response.status_code, 200)
        result = check_response.data["data"]
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["actual_count"], 2)
        self.assertEqual(result["blocking"], False)

    def test_b_grade_rule_check_blocks_when_count_below_minimum(self):
        create_response = self.client.post(
            "/api/coffee/b-grade-rules/",
            {
                "rule_name": "B级通过数至少3条",
                "task_id": self.plot.task_code,
                "metric": "approved_event_count",
                "min_count": 3,
                "block_level": "blocking",
                "enabled": True,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)
        rule = create_response.data["data"]

        check_response = self.client.post(f"/api/coffee/b-grade-rules/{rule['rule_code']}/check/", {}, format="json")

        self.assertEqual(check_response.status_code, 200)
        result = check_response.data["data"]
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["actual_count"], 2)
        self.assertEqual(result["blocking"], True)

    def test_b_grade_rule_update_toggle_and_delete_support_web_form_actions(self):
        create_response = self.client.post(
            "/api/coffee/b-grade-rules/",
            {
                "rule_name": "B级通过数至少1条",
                "task_id": self.plot.task_code,
                "metric": "approved_event_count",
                "min_count": 1,
                "block_level": "warning",
                "enabled": True,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)
        rule_code = create_response.data["data"]["rule_code"]

        update_response = self.client.put(
            f"/api/coffee/b-grade-rules/{rule_code}/",
            {
                "rule_name": "B级通过数至少2条",
                "task_id": self.plot.task_code,
                "metric": "approved_event_count",
                "min_count": 2,
                "max_count": 5,
                "block_level": "blocking",
                "enabled": True,
            },
            format="json",
        )

        self.assertEqual(update_response.status_code, 200)
        updated = update_response.data["data"]
        self.assertEqual(updated["rule_name"], "B级通过数至少2条")
        self.assertEqual(updated["min_count"], 2)
        self.assertEqual(updated["block_level"], "blocking")

        toggle_response = self.client.post(f"/api/coffee/b-grade-rules/{rule_code}/toggle/", {"enabled": False}, format="json")
        self.assertEqual(toggle_response.status_code, 200)
        self.assertEqual(toggle_response.data["data"]["enabled"], False)

        delete_response = self.client.delete(f"/api/coffee/b-grade-rules/{rule_code}/")
        self.assertEqual(delete_response.status_code, 200)
        list_response = self.client.get("/api/coffee/b-grade-rules/", {"task_id": self.plot.task_code})
        self.assertEqual(list_response.data["data"]["count"], 0)
