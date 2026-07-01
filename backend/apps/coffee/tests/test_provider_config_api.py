from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import ProviderCallLog


class CoffeeProviderConfigApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="provider-admin",
            password="provider-pass",
            name="Provider管理员",
            mobile="13800000004",
        )
        self.client.force_authenticate(self.user)

    def test_web_provider_config_create_and_list_masks_secret_fields(self):
        response = self.client.post(
            "/api/coffee/provider-configs/",
            {
                "provider_type": "ocr",
                "provider_name": "huawei_ocr",
                "display_name": "华为 OCR",
                "enabled": True,
                "priority": 20,
                "timeout_ms": 15000,
                "rate_limit_per_minute": 60,
                "config_json": {
                    "endpoint": "https://ocr.example.test",
                    "ak": "real-access-key",
                    "sk": "real-secret-key",
                },
                "secret_fields": ["ak", "sk"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        created = response.data["data"]
        self.assertEqual(created["provider_name"], "huawei_ocr")
        self.assertEqual(created["config_status"], "configured")
        self.assertEqual(created["masked_config"]["endpoint"], "https://ocr.example.test")
        self.assertNotIn("real-secret-key", str(created))
        self.assertEqual(created["masked_config"]["sk"], "********")

        list_response = self.client.get("/api/coffee/provider-configs/", {"provider_type": "ocr"})
        self.assertEqual(list_response.status_code, 200)
        item = list_response.data["data"]["results"][0]
        self.assertEqual(item["provider_name"], "huawei_ocr")
        self.assertNotIn("real-access-key", str(item))
        self.assertEqual(item["masked_config"]["ak"], "********")

    def test_provider_connection_test_uses_local_contract_and_writes_call_log(self):
        create_response = self.client.post(
            "/api/coffee/provider-configs/",
            {
                "provider_type": "ocr",
                "provider_name": "manual",
                "display_name": "人工录入",
                "enabled": True,
                "priority": 99,
                "timeout_ms": 1000,
                "config_json": {},
                "secret_fields": [],
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)
        provider_id = create_response.data["data"]["id"]

        response = self.client.post(f"/api/coffee/provider-configs/{provider_id}/test/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        result = response.data["data"]
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["provider_name"], "manual")
        self.assertEqual(ProviderCallLog.objects.filter(provider_type="ocr", provider_name="manual", target_type="provider_config").count(), 1)

    def test_provider_config_update_toggle_and_delete_support_web_form_actions(self):
        create_response = self.client.post(
            "/api/coffee/provider-configs/",
            {
                "provider_type": "map",
                "provider_name": "amap",
                "display_name": "高德地图",
                "enabled": True,
                "priority": 10,
                "timeout_ms": 3000,
                "rate_limit_per_minute": 120,
                "config_json": {"api_key": "real-map-key"},
                "secret_fields": ["api_key"],
            },
            format="json",
        )
        provider_id = create_response.data["data"]["id"]

        update_response = self.client.put(
            f"/api/coffee/provider-configs/{provider_id}/",
            {
                "provider_type": "map",
                "provider_name": "amap",
                "display_name": "高德地图正式配置",
                "enabled": True,
                "priority": 5,
                "timeout_ms": 5000,
                "rate_limit_per_minute": 90,
                "config_json": {"api_key": "new-real-map-key"},
                "secret_fields": ["api_key"],
            },
            format="json",
        )

        self.assertEqual(update_response.status_code, 200)
        updated = update_response.data["data"]
        self.assertEqual(updated["display_name"], "高德地图正式配置")
        self.assertEqual(updated["priority"], 5)
        self.assertEqual(updated["masked_config"]["api_key"], "********")
        self.assertNotIn("new-real-map-key", str(updated))

        toggle_response = self.client.post(f"/api/coffee/provider-configs/{provider_id}/toggle/", {"enabled": False}, format="json")
        self.assertEqual(toggle_response.status_code, 200)
        self.assertEqual(toggle_response.data["data"]["enabled"], False)

        delete_response = self.client.delete(f"/api/coffee/provider-configs/{provider_id}/")
        self.assertEqual(delete_response.status_code, 200)
        list_response = self.client.get("/api/coffee/provider-configs/")
        self.assertEqual(list_response.data["data"]["count"], 0)

    def test_tencent_and_baidu_map_provider_contracts_are_testable_without_real_keys(self):
        created_ids = []
        for provider_name, display_name in [("tencent_map", "腾讯地图"), ("baidu_map", "百度地图")]:
            response = self.client.post(
                "/api/coffee/provider-configs/",
                {
                    "provider_type": "map",
                    "provider_name": provider_name,
                    "display_name": display_name,
                    "enabled": True,
                    "priority": 30,
                    "timeout_ms": 3000,
                    "rate_limit_per_minute": 120,
                    "config_json": {
                        "endpoint": f"https://{provider_name}.example.test",
                        "api_key": f"{provider_name}-key",
                        "coordinate_system": "GCJ02" if provider_name == "tencent_map" else "BD09",
                    },
                    "secret_fields": ["api_key"],
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["data"]["provider_type"], "map")
            self.assertEqual(response.data["data"]["masked_config"]["api_key"], "********")
            created_ids.append(response.data["data"]["id"])

        for provider_id in created_ids:
            response = self.client.post(f"/api/coffee/provider-configs/{provider_id}/test/", {}, format="json")
            self.assertEqual(response.status_code, 200)
            result = response.data["data"]
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["provider_type"], "map")
            self.assertIn(result["provider_name"], ["tencent_map", "baidu_map"])
            self.assertIn("reverse_geocode", result["capabilities"])
            self.assertIn("boundary_polygon", result["capabilities"])
            self.assertIn("area_recheck", result["capabilities"])
            self.assertEqual(result["local_contract_only"], True)

        self.assertEqual(ProviderCallLog.objects.filter(provider_type="map", target_type="provider_config").count(), 2)
