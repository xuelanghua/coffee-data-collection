import unittest

from paddleocr_service.parser import DEVICE_READING_FIELDS, parse_device_reading_text
from paddleocr_service.service import create_health_payload, predict_device_reading


class DeviceReadingTemplateTests(unittest.TestCase):
    def test_parse_device_reading_text_extracts_ten_measurement_fields(self):
        text = """
        风速 1.8 m/s
        风向 东南
        空气温度 23.6 ℃
        空气湿度 72 %RH
        大气压力 90.8 kPa
        雨量 0.0 mm
        土壤湿度 38.5 %
        土壤温度 21.4 ℃
        土壤盐分 0.18 ms/cm
        土壤PH值 6.4
        """

        result = parse_device_reading_text(text)

        self.assertEqual(set(result), set(DEVICE_READING_FIELDS))
        self.assertEqual(result["wind_speed"]["value"], "1.8")
        self.assertEqual(result["wind_direction"]["value"], "东南")
        self.assertEqual(result["air_temperature"]["value"], "23.6")
        self.assertEqual(result["soil_ph"]["value"], "6.4")
        self.assertEqual(result["soil_salinity"]["unit"], "ms/cm")
        self.assertGreaterEqual(result["air_humidity"]["confidence"], 0.8)

    def test_predict_device_reading_returns_provider_contract_payload(self):
        payload = predict_device_reading(
            {
                "photo_id": "PH202606260001",
                "image_ref": "mock://device-screen",
                "template": "device_reading_v1",
                "mock_text": "风速 2.1 m/s\n风向 西北\n空气温度 24.5\n空气湿度 70\n大气压力 91.2\n雨量 1.0\n土壤湿度 39\n土壤温度 22\n土壤盐分 0.2\n土壤PH 6.5",
            }
        )

        self.assertEqual(payload["provider"], "paddleocr")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["photo_id"], "PH202606260001")
        self.assertEqual(payload["template"], "device_reading_v1")
        self.assertEqual(len(payload["fields"]), 10)
        self.assertIn("raw_text", payload)

    def test_health_payload_exposes_templates_and_engine_mode(self):
        payload = create_health_payload()

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["provider"], "paddleocr")
        self.assertIn("device_reading_v1", payload["templates"])
        self.assertIn(payload["engine_mode"], {"mock", "paddleocr"})


if __name__ == "__main__":
    unittest.main()
