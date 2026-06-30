from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class CoffeeMetricDefinitionApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="metric-admin",
            password="metric-pass",
            name="统计口径管理员",
            mobile="13800000061",
        )
        self.client.force_authenticate(self.user)

    def test_metric_definition_versions_and_statistics_metadata(self):
        first_response = self.client.post(
            "/api/coffee/metric-definitions/",
            {
                "metric_code": "total_events",
                "metric_name": "采集事件总数",
                "metric_group": "progress",
                "calculation_method": "count(CollectionEvent.id)",
                "description": "按当前数据权限统计采集事件数量",
                "unit": "条",
                "enabled": True,
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.data["data"]["version"], 1)

        second_response = self.client.post(
            "/api/coffee/metric-definitions/",
            {
                "metric_code": "total_events",
                "metric_name": "采集事件总数",
                "metric_group": "progress",
                "calculation_method": "count(scoped CollectionEvent.id)",
                "description": "按当前用户数据权限统计采集事件数量",
                "unit": "条",
                "enabled": True,
            },
            format="json",
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.data["data"]["version"], 2)

        list_response = self.client.get("/api/coffee/metric-definitions/?metric_group=progress")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["data"]["count"], 2)

        progress_response = self.client.get("/api/coffee/statistics/progress/")
        self.assertEqual(progress_response.status_code, 200)
        metric_definitions = progress_response.data["data"]["metric_definitions"]

        self.assertEqual(len(metric_definitions), 1)
        self.assertEqual(metric_definitions[0]["metric_code"], "total_events")
        self.assertEqual(metric_definitions[0]["version"], 2)
        self.assertEqual(metric_definitions[0]["calculation_method"], "count(scoped CollectionEvent.id)")
