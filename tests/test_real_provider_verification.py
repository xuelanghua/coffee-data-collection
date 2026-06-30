import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import importlib.util


SCRIPT = Path("scripts/verify-real-providers.py")
SPEC = importlib.util.spec_from_file_location("verify_real_providers", SCRIPT)
verify_real_providers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_real_providers)


class RealProviderVerificationTests(unittest.TestCase):
    def test_payload_uses_env_py_and_never_exposes_secret_values(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as env_file:
            env_file.write("AMAP_KEY = 'amap-secret-value'\n")
            env_file.write("JUHE_WEATHER_KEY = 'juhe-secret-value'\n")
            env_path = env_file.name
        self.addCleanup(lambda: Path(env_path).unlink(missing_ok=True))

        def fake_fetch(url, params, timeout):
            self.assertNotIn("key=", url)
            if "amap" in url:
                self.assertEqual(params["key"], "amap-secret-value")
                return {
                    "status": "1",
                    "infocode": "10000",
                    "count": "1",
                    "geocodes": [
                        {
                            "formatted_address": "云南省普洱市",
                            "location": "100.966011,22.825229",
                            "province": "云南省",
                            "city": "普洱市",
                        }
                    ],
                }
            self.assertEqual(params["key"], "juhe-secret-value")
            return {
                "error_code": 0,
                "reason": "查询成功",
                "result": {
                    "realtime": {
                        "temperature": "22",
                        "humidity": "88",
                        "info": "多云",
                        "direct": "东南风",
                        "power": "2级",
                    }
                },
            }

        with patch.dict("os.environ", {"COFFEE_PROVIDER_ENV_FILE": env_path}, clear=True):
            with patch.object(verify_real_providers, "fetch_json", side_effect=fake_fetch):
                payload = verify_real_providers.build_payload("普洱市", 1)

        text = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(payload["overall_status"], "PASS")
        self.assertEqual(payload["checks"]["amap"]["source"], "env_file")
        self.assertEqual(payload["checks"]["juhe_weather"]["source"], "env_file")
        self.assertNotIn("amap-secret-value", text)
        self.assertNotIn("juhe-secret-value", text)
        self.assertNotIn("key=", text)

    def test_cli_blocks_when_required_keys_are_missing(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as env_file:
            env_path = env_file.name
        self.addCleanup(lambda: Path(env_path).unlink(missing_ok=True))

        result = subprocess.run(
            ["python3", str(SCRIPT), "--json"],
            capture_output=True,
            text=True,
            env={"COFFEE_PROVIDER_ENV_FILE": env_path},
        )

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["overall_status"], "BLOCKED")
        self.assertEqual(payload["checks"]["amap"]["missing"], "AMAP_KEY")
        self.assertEqual(payload["checks"]["juhe_weather"]["missing"], "JUHE_WEATHER_KEY")


if __name__ == "__main__":
    unittest.main()
