from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-offline-package-browser.mjs"


class OfflinePackageBrowserSmokeScriptTests(unittest.TestCase):
    def test_script_declares_playwright_manifest_and_html_evidence(self):
        self.assertTrue(SCRIPT.exists())
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("playwright", source)
        self.assertIn("offline-package-browser.png", source)
        self.assertIn("offline-package-browser.json", source)
        self.assertIn("manifest.json", source)
        self.assertIn("index.html", source)
        self.assertIn("离线数据包", source)
        self.assertIn("chromium.launch", source)
