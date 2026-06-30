from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-photo-annotation-canvas.mjs"


class PhotoAnnotationVisualScriptTests(unittest.TestCase):
    def test_script_declares_playwright_screenshot_and_geometry_evidence(self):
        self.assertTrue(SCRIPT.exists())
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("playwright", source)
        self.assertIn("photo-annotation-canvas.png", source)
        self.assertIn("photo-annotation-canvas.json", source)
        self.assertIn("display_box", source)
        self.assertIn("natural_box", source)
        self.assertIn("chromium.launch", source)
