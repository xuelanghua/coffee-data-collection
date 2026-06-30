from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from dvadmin.system.models import Dept, Role
from apps.coffee.menu import ensure_coffee_role_matrix
from apps.coffee.models import CollectionEvent, PhotoAsset, Plot, Point


class CoffeeWebEventListApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="web-event-list",
            password="web-event-list-pass",
            name="审核员",
            mobile="13800000005",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606250801",
            task_code="TASK202606250008",
            name="列表地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("10.00"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606250801",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )

    def create_event(self, suffix, status):
        event = CollectionEvent.objects.create(
            event_id=f"EV2026062508{suffix}",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key=f"web-list-{suffix}",
            status=status,
            manifest_hash=f"manifest-{suffix}",
        )
        PhotoAsset.objects.create(
            photo_id=f"PH2026062508{suffix}",
            event=event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            sha256=f"sha-{suffix}",
        )
        return event

    def create_event_for_collector(self, suffix, collector_id):
        event = self.create_event(suffix, CollectionEvent.STATUS_SUBMITTED)
        event.collector_id = str(collector_id)
        event.save(update_fields=["collector_id"])
        return event

    def create_event_for_dept(self, suffix, dept_id):
        event = self.create_event(suffix, CollectionEvent.STATUS_SUBMITTED)
        event.dept_belong_id = str(dept_id)
        event.save(update_fields=["dept_belong_id"])
        return event

    def test_web_event_list_filters_by_status_and_returns_summary_counts(self):
        submitted = self.create_event("01", CollectionEvent.STATUS_SUBMITTED)
        self.create_event("02", CollectionEvent.STATUS_RETURNED)

        response = self.client.get("/api/coffee/events/", {"status": CollectionEvent.STATUS_SUBMITTED})

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["event_id"], submitted.event_id)
        self.assertEqual(data["results"][0]["plot_id"], self.plot.plot_id)
        self.assertEqual(data["results"][0]["point_id"], self.point.point_id)
        self.assertEqual(data["results"][0]["photo_count"], 1)
        self.assertIn("ocr_status", data["results"][0])
        self.assertIn("quality_status", data["results"][0])

    def test_collector_event_list_is_limited_to_own_events_but_reviewer_can_see_all(self):
        ensure_coffee_role_matrix()
        collector = get_user_model().objects.create_user(
            username="collector-scope",
            password="collector-scope-pass",
            name="采集员",
            mobile="13800000031",
        )
        collector.role.add(Role.objects.get(key="coffee_collector"))
        reviewer = get_user_model().objects.create_user(
            username="reviewer-scope",
            password="reviewer-scope-pass",
            name="审核员",
            mobile="13800000032",
        )
        reviewer.role.add(Role.objects.get(key="coffee_reviewer"))
        own_event = self.create_event_for_collector("11", collector.id)
        self.create_event_for_collector("12", "someone-else")

        self.client.force_authenticate(collector)
        collector_response = self.client.get("/api/coffee/events/")

        self.assertEqual(collector_response.status_code, 200)
        collector_data = collector_response.data["data"]
        self.assertEqual(collector_data["count"], 1)
        self.assertEqual(collector_data["results"][0]["event_id"], own_event.event_id)

        self.client.force_authenticate(reviewer)
        reviewer_response = self.client.get("/api/coffee/events/")

        self.assertEqual(reviewer_response.status_code, 200)
        reviewer_data = reviewer_response.data["data"]
        self.assertEqual(reviewer_data["count"], 2)

    def test_reviewer_event_list_is_limited_to_own_department_but_admin_can_see_all(self):
        ensure_coffee_role_matrix()
        north_dept = Dept.objects.create(name="北区采集组", key="coffee-north")
        south_dept = Dept.objects.create(name="南区采集组", key="coffee-south")
        reviewer = get_user_model().objects.create_user(
            username="reviewer-dept-scope",
            password="reviewer-dept-scope-pass",
            name="北区审核员",
            mobile="13800000033",
            dept=north_dept,
        )
        reviewer.role.add(Role.objects.get(key="coffee_reviewer"))
        admin = get_user_model().objects.create_user(
            username="admin-dept-scope",
            password="admin-dept-scope-pass",
            name="管理员",
            mobile="13800000034",
        )
        admin.role.add(Role.objects.get(key="coffee_admin"))
        north_event = self.create_event_for_dept("21", north_dept.id)
        self.create_event_for_dept("22", south_dept.id)

        self.client.force_authenticate(reviewer)
        reviewer_response = self.client.get("/api/coffee/events/")

        self.assertEqual(reviewer_response.status_code, 200)
        reviewer_data = reviewer_response.data["data"]
        self.assertEqual(reviewer_data["count"], 1)
        self.assertEqual(reviewer_data["results"][0]["event_id"], north_event.event_id)

        self.client.force_authenticate(admin)
        admin_response = self.client.get("/api/coffee/events/")

        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.data["data"]["count"], 2)
