from pathlib import Path
import os
import subprocess
import unittest


class VerifyAllScriptTests(unittest.TestCase):
    def setUp(self):
        self.script = Path("scripts/verify-all.sh")

    def test_verify_all_script_exists_and_is_executable(self):
        self.assertTrue(self.script.exists(), "scripts/verify-all.sh must exist")
        self.assertTrue(os.access(self.script, os.X_OK), "verify-all.sh must be executable")

    def test_verify_all_script_lists_p0_validation_steps(self):
        self.assertTrue(self.script.exists(), "scripts/verify-all.sh must exist")
        result = subprocess.run(
            [str(self.script), "--list"],
            check=True,
            capture_output=True,
            text=True,
        )

        output = result.stdout
        for step in (
            "backend coffee API tests",
            "app unit lint build",
            "web contract and build",
            "paddleocr service tests",
            "infra compose contract",
            "delivery gate checks",
            "docker compose static config",
        ):
            self.assertIn(step, output)


if __name__ == "__main__":
    unittest.main()
