import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from paddleocr_service.parser import DEVICE_READING_FIELDS, parse_device_reading_text


PROVIDER_NAME = "paddleocr"
SUPPORTED_TEMPLATES = ("device_reading_v1",)


def create_health_payload():
    return {
        "status": "ok",
        "provider": PROVIDER_NAME,
        "engine_mode": os.getenv("PADDLEOCR_ENGINE_MODE", "mock"),
        "templates": list(SUPPORTED_TEMPLATES),
    }


def predict_device_reading(payload):
    template = payload.get("template", "device_reading_v1")
    if template not in SUPPORTED_TEMPLATES:
        return {
            "provider": PROVIDER_NAME,
            "status": "failed",
            "error_code": "PROVIDER_BAD_RESPONSE",
            "error_message": f"Unsupported template: {template}",
            "fields": [],
        }

    raw_text = payload.get("mock_text") or payload.get("raw_text") or ""
    structured = parse_device_reading_text(raw_text)
    fields = [structured[field_code] for field_code in DEVICE_READING_FIELDS]
    confidence_values = [item["confidence"] for item in fields if item["confidence"]]
    confidence = round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else 0.0
    return {
        "provider": PROVIDER_NAME,
        "status": "success",
        "photo_id": payload.get("photo_id"),
        "image_ref": payload.get("image_ref"),
        "template": template,
        "fields": fields,
        "confidence": confidence,
        "raw_text": raw_text,
    }


class PaddleOCRRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send_json(create_health_payload())
            return
        self._send_json({"status": "not_found"}, status=404)

    def do_POST(self):
        if self.path != "/predict":
            self._send_json({"status": "not_found"}, status=404)
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"status": "failed", "error_code": "PROVIDER_BAD_RESPONSE", "error_message": "Invalid JSON"}, status=400)
            return
        self._send_json(predict_device_reading(payload))

    def log_message(self, format, *args):
        return

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    host = os.getenv("PADDLEOCR_HOST", "0.0.0.0")
    port = int(os.getenv("PADDLEOCR_PORT", "8011"))
    HTTPServer((host, port), PaddleOCRRequestHandler).serve_forever()


if __name__ == "__main__":
    main()

