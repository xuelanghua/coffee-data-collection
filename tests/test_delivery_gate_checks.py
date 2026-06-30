import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class DeliveryGateCheckTests(unittest.TestCase):
    def setUp(self):
        self.script = Path("scripts/check-delivery-gates.py")

    def test_delivery_gate_check_script_outputs_security_and_real_provider_statuses(self):
        self.assertTrue(self.script.exists(), "scripts/check-delivery-gates.py must exist")
        state = json.loads(Path("automation/state.json").read_text())

        result = subprocess.run(
            ["python3", str(self.script), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["stage"], state["current_stage"])
        self.assertIn(payload["overall_status"], ["PASS", "BLOCKED", "FAIL"])
        self.assertIn("security_static_scan", payload["checks"])
        self.assertIn("real_provider_config_gate", payload["checks"])
        self.assertIn(payload["checks"]["security_static_scan"]["status"], ["PASS", "FAIL"])
        self.assertIn(payload["checks"]["real_provider_config_gate"]["status"], ["PASS", "BLOCKED"])

    def test_delivery_gate_check_reads_provider_keys_from_env_py_file(self):
        self.assertTrue(self.script.exists(), "scripts/check-delivery-gates.py must exist")

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as env_file:
            env_file.write("AMAP_KEY = 'amap-from-env-file'\n")
            env_file.write("JUHE_WEATHER_KEY = 'juhe-from-env-file'\n")
            env_path = env_file.name
        self.addCleanup(lambda: Path(env_path).unlink(missing_ok=True))

        env = os.environ.copy()
        env.pop("AMAP_KEY", None)
        env.pop("JUHE_WEATHER_KEY", None)
        env["COFFEE_PROVIDER_ENV_FILE"] = env_path

        result = subprocess.run(
            ["python3", str(self.script), "--json"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)

        provider_gate = payload["checks"]["real_provider_config_gate"]
        self.assertEqual(provider_gate["status"], "PASS")
        self.assertEqual(provider_gate["missing"], [])
        self.assertEqual(provider_gate["sources"]["AMAP_KEY"], "env_file")
        self.assertEqual(provider_gate["sources"]["JUHE_WEATHER_KEY"], "env_file")

    def test_verify_all_lists_delivery_gate_check(self):
        result = subprocess.run(
            ["scripts/verify-all.sh", "--list"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("delivery gate checks", result.stdout)


if __name__ == "__main__":
    unittest.main()
