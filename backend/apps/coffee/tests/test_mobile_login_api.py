from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.menu import ensure_coffee_role_matrix
from dvadmin.system.models import Role


class CoffeeMobileLoginApiTests(APITestCase):
    def test_mobile_login_accepts_phone_and_returns_token_and_roles(self):
        ensure_coffee_role_matrix()
        user = get_user_model().objects.create_user(
            username="collector-login",
            password="collector-pass",
            name="现场采集员",
            mobile="13800000009",
        )
        user.role.add(Role.objects.get(key="coffee_collector"))

        response = self.client.post(
            "/api/coffee/auth/mobile-login/",
            {"phone": "13800000009", "password": "collector-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 2000)
        self.assertEqual(response.data["data"]["username"], "collector-login")
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertEqual(list(response.data["data"]["role_info"])[0]["key"], "coffee_collector")
