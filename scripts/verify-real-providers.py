#!/usr/bin/env python3
import argparse
import ast
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROVIDER_ENV_FILE = ROOT / "backend" / "conf" / "env.py"
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
JUHE_WEATHER_URL = "https://apis.juhe.cn/simpleWeather/query"


def provider_env_file_path():
    return Path(os.environ.get("COFFEE_PROVIDER_ENV_FILE") or DEFAULT_PROVIDER_ENV_FILE)


def read_env_file_values(path):
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        if not isinstance(value, str) or not value:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {"AMAP_KEY", "JUHE_WEATHER_KEY"}:
                values[target.id] = value
    return values


def provider_secret(name, env_file_values):
    value = os.environ.get(name)
    if value:
        return value, "environment"
    value = env_file_values.get(name)
    if value:
        return value, "env_file"
    return None, None


def fetch_json(url, params, timeout):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "coffee-uaidf-real-provider-check/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def verify_amap(amap_key, source, city, timeout):
    raw = fetch_json(AMAP_GEOCODE_URL, {"key": amap_key, "address": city, "city": city}, timeout)
    ok = raw.get("status") == "1" and raw.get("infocode") == "10000" and bool(raw.get("geocodes"))
    geocode = (raw.get("geocodes") or [{}])[0]
    return {
        "status": "PASS" if ok else "FAIL",
        "source": source,
        "provider": "amap",
        "api": "geocode_geo",
        "city": city,
        "infocode": raw.get("infocode"),
        "count": raw.get("count"),
        "formatted_address": geocode.get("formatted_address"),
        "location": geocode.get("location"),
        "province": geocode.get("province"),
        "city_name": geocode.get("city"),
    }


def verify_juhe(juhe_key, source, city, timeout):
    raw = fetch_json(JUHE_WEATHER_URL, {"key": juhe_key, "city": city}, timeout)
    ok = raw.get("error_code") == 0 and raw.get("result") is not None
    result = raw.get("result") or {}
    realtime = result.get("realtime") or {}
    return {
        "status": "PASS" if ok else "FAIL",
        "source": source,
        "provider": "juhe_weather",
        "api": "simpleWeather_query",
        "city": city,
        "error_code": raw.get("error_code"),
        "reason": raw.get("reason"),
        "temperature": realtime.get("temperature"),
        "humidity": realtime.get("humidity"),
        "info": realtime.get("info"),
        "wid": realtime.get("wid"),
        "direct": realtime.get("direct"),
        "power": realtime.get("power"),
        "aqi": realtime.get("aqi"),
    }


def build_payload(city, timeout):
    env_file = provider_env_file_path()
    env_values = read_env_file_values(env_file)
    amap_key, amap_source = provider_secret("AMAP_KEY", env_values)
    juhe_key, juhe_source = provider_secret("JUHE_WEATHER_KEY", env_values)
    checks = {}

    if not amap_key:
        checks["amap"] = {"status": "BLOCKED", "provider": "amap", "missing": "AMAP_KEY"}
    else:
        checks["amap"] = verify_amap(amap_key, amap_source, city, timeout)

    if not juhe_key:
        checks["juhe_weather"] = {"status": "BLOCKED", "provider": "juhe_weather", "missing": "JUHE_WEATHER_KEY"}
    else:
        checks["juhe_weather"] = verify_juhe(juhe_key, juhe_source, city, timeout)

    statuses = {item["status"] for item in checks.values()}
    overall = "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"
    return {
        "schema_version": 1,
        "city": city,
        "overall_status": overall,
        "checks": checks,
        "env_file": str(env_file.relative_to(ROOT)) if env_file.is_relative_to(ROOT) else str(env_file),
        "boundary": "真实调用高德地图地理编码和聚合天气实时天气接口；输出只包含脱敏摘要，不包含 Key 明文或请求 URL",
    }


def main():
    parser = argparse.ArgumentParser(description="Verify real Amap and Juhe provider calls without printing secrets")
    parser.add_argument("--city", default="普洱市", help="城市名，默认普洱市")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()
    payload = build_payload(args.city, args.timeout)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={payload['overall_status']}")
        for name, check in payload["checks"].items():
            print(f"{name}={check['status']} source={check.get('source')}")
    return 0 if payload["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
