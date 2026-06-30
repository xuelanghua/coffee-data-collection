import re


DEVICE_READING_FIELDS = {
    "wind_speed": {"label": "风速", "unit": "m/s", "aliases": ("风速",)},
    "wind_direction": {"label": "风向", "unit": "", "aliases": ("风向",)},
    "air_temperature": {"label": "空气温度", "unit": "℃", "aliases": ("空气温度", "气温")},
    "air_humidity": {"label": "空气湿度", "unit": "%RH", "aliases": ("空气湿度", "湿度")},
    "atmospheric_pressure": {"label": "大气压力", "unit": "kPa", "aliases": ("大气压力", "气压")},
    "rainfall": {"label": "雨量", "unit": "mm", "aliases": ("雨量", "降雨量")},
    "soil_moisture": {"label": "土壤湿度", "unit": "%", "aliases": ("土壤湿度", "土湿")},
    "soil_temperature": {"label": "土壤温度", "unit": "℃", "aliases": ("土壤温度", "土温")},
    "soil_salinity": {"label": "土壤盐分", "unit": "ms/cm", "aliases": ("土壤盐分", "盐分")},
    "soil_ph": {"label": "土壤 PH 值", "unit": "pH", "aliases": ("土壤PH值", "土壤PH", "土壤 PH 值", "PH值", "pH")},
}


def parse_device_reading_text(text):
    normalized = _normalize_text(text)
    parsed = {}
    for field_code, definition in DEVICE_READING_FIELDS.items():
        value, unit = _extract_field(normalized, definition)
        parsed[field_code] = {
            "name": field_code,
            "label": definition["label"],
            "value": value,
            "unit": unit or definition["unit"],
            "confidence": 0.92 if value else 0.0,
            "bbox": None,
        }
    return parsed


def _normalize_text(text):
    return (text or "").replace("：", " ").replace("℃", " ℃").replace("%RH", " %RH")


def _extract_field(text, definition):
    for alias in definition["aliases"]:
        pattern = re.compile(rf"{re.escape(alias)}\s*[:：]?\s*([+\-]?\d+(?:\.\d+)?|[东南西北中]{1,3}|东北|东南|西南|西北)\s*([a-zA-Z/%℃]+)?", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return match.group(1), match.group(2) or ""
    return "", ""

