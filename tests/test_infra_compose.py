from pathlib import Path
import unittest


class InfraComposeTests(unittest.TestCase):
    def setUp(self):
        self.compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    def test_compose_declares_p0_runtime_services_and_persistent_health_checks(self):
        for service_name in (
            "dvadmin3-mysql",
            "dvadmin3-redis",
            "dvadmin3-django",
            "dvadmin3-celery",
            "dvadmin3-celery-beat",
            "coffee-paddleocr",
        ):
            self.assertIn(f"{service_name}:", self.compose)

        self.assertIn("mysql:8.0", self.compose)
        self.assertIn("redis:6.2.6-alpine", self.compose)
        self.assertIn("services/paddleocr/Dockerfile", self.compose)
        self.assertIn("PADDLEOCR_ENGINE_MODE", self.compose)
        self.assertGreaterEqual(self.compose.count("healthcheck:"), 3)
        self.assertIn("coffee-paddleocr-data", self.compose)


if __name__ == "__main__":
    unittest.main()
