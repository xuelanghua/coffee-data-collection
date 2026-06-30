import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from apps.coffee.models import OCRResult, ProviderConfig


@dataclass
class OCRProviderResult:
    status: str
    raw_response: dict
    structured_json: dict
    confidence: Decimal | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw_ref: str | None = None


MAP_PROVIDER_CAPABILITIES = {
    "tencent_map": {
        "provider_family": "tencent",
        "coordinate_system": "GCJ02",
        "capabilities": ["reverse_geocode", "boundary_polygon", "area_recheck"],
    },
    "baidu_map": {
        "provider_family": "baidu",
        "coordinate_system": "BD09",
        "capabilities": ["reverse_geocode", "boundary_polygon", "area_recheck"],
    },
}


def provider_local_contract(config):
    if config.provider_type == ProviderConfig.TYPE_MAP:
        contract = MAP_PROVIDER_CAPABILITIES.get(config.provider_name)
        if not contract:
            return {
                "provider_type": config.provider_type,
                "provider_name": config.provider_name,
                "status": "failed",
                "error_code": "MAP_PROVIDER_UNSUPPORTED",
                "local_contract_only": True,
                "capabilities": [],
            }
        return {
            "provider_type": config.provider_type,
            "provider_name": config.provider_name,
            "status": "success",
            "error_code": None,
            "local_contract_only": True,
            **contract,
        }
    return {
        "provider_type": config.provider_type,
        "provider_name": config.provider_name,
        "status": "success",
        "error_code": None,
        "local_contract_only": True,
        "capabilities": [],
    }


def _average_confidence(fields):
    values = [Decimal(str(item["confidence"])) for item in fields if item.get("confidence") is not None]
    if not values:
        return None
    return (sum(values) / Decimal(len(values))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _fields_to_structured_json(fields):
    structured = {}
    for item in fields:
        name = item.get("name")
        if not name:
            continue
        structured[name] = {
            "value": item.get("value"),
            "confidence": item.get("confidence"),
        }
        if "bbox" in item:
            structured[name]["bbox"] = item["bbox"]
    return structured


def _get_enabled_config(provider_name):
    return (
        ProviderConfig.objects.filter(
            provider_type=ProviderConfig.TYPE_OCR,
            provider_name=provider_name,
            enabled=True,
        )
        .order_by("priority", "-version", "-id")
        .first()
    )


def call_ocr_provider(*, provider_name, photo):
    config = _get_enabled_config(provider_name)
    if not config:
        return OCRProviderResult(
            status=OCRResult.STATUS_FAILED,
            raw_response={},
            structured_json={},
            error_code="PROVIDER_NOT_CONFIGURED",
            error_message="OCR Provider 未启用或未配置",
        )

    endpoint = config.config_json.get("endpoint")
    if not endpoint:
        return OCRProviderResult(
            status=OCRResult.STATUS_FAILED,
            raw_response={},
            structured_json={},
            error_code="PROVIDER_NOT_CONFIGURED",
            error_message="OCR Provider 缺少 endpoint",
        )

    payload = {
        "photo_id": photo.photo_id,
        "image_ref": photo.original_file,
        "template": config.config_json.get("template", "device_reading_v1"),
        "timeout_ms": config.timeout_ms,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=config.timeout_ms / 1000) as response:
            raw_response = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return OCRProviderResult(
            status=OCRResult.STATUS_FAILED,
            raw_response={},
            structured_json={},
            error_code="PROVIDER_BAD_RESPONSE",
            error_message=str(exc),
        )

    fields = raw_response.get("fields") or []
    provider_status = raw_response.get("status")
    status = OCRResult.STATUS_SUCCESS if provider_status == "success" else OCRResult.STATUS_FAILED
    return OCRProviderResult(
        status=status,
        raw_response=raw_response,
        structured_json=_fields_to_structured_json(fields),
        confidence=_average_confidence(fields),
        error_code=raw_response.get("error_code"),
        error_message=raw_response.get("error_message"),
        raw_ref=raw_response.get("raw_ref"),
    )
