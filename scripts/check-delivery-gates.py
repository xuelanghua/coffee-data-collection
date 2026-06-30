#!/usr/bin/env python3
import argparse
import ast
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN_PATHS = [
    "backend/apps/coffee",
    "coffee-collector-app/src",
    "web/src/api/coffee",
    "web/src/views/coffee",
    "services/paddleocr",
    "scripts",
]
SECRET_PATTERNS = [
    re.compile(r"(?i)(secret|token|password|passwd|api[_-]?key|access[_-]?key|ak|sk)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
]
REQUIRED_REAL_PROVIDER_ENV = {
    "AMAP_KEY": "高德地图真实 Key",
    "JUHE_WEATHER_KEY": "聚合天气真实 Key",
}
DEFERRED_REAL_PROVIDER_ENV = {
    "HUAWEI_OCR_ENDPOINT": "华为 OCR Endpoint",
    "HUAWEI_OCR_AK": "华为 OCR AK",
    "HUAWEI_OCR_SK": "华为 OCR SK",
}
DEFAULT_PROVIDER_ENV_FILE = ROOT / "backend" / "conf" / "env.py"


def current_stage():
    state_path = ROOT / "automation" / "state.json"
    if not state_path.exists():
        return "UNKNOWN"
    try:
        return json.loads(state_path.read_text(encoding="utf-8")).get("current_stage") or "UNKNOWN"
    except json.JSONDecodeError:
        return "UNKNOWN"


def provider_env_file_path():
    return Path(os.environ.get("COFFEE_PROVIDER_ENV_FILE") or DEFAULT_PROVIDER_ENV_FILE)


def read_env_file_values(path):
    if not path.exists():
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return {}

    values = {}
    target_names = set(REQUIRED_REAL_PROVIDER_ENV) | set(DEFERRED_REAL_PROVIDER_ENV)
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
            if isinstance(target, ast.Name) and target.id in target_names:
                values[target.id] = value
    return values


def provider_config_value(name, env_file_values):
    if os.environ.get(name):
        return "environment"
    if env_file_values.get(name):
        return "env_file"
    return None


def iter_source_files():
    for relative in SCAN_PATHS:
        base = ROOT / relative
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if "tests" in path.relative_to(base).parts:
                continue
            if path.is_file() and path.suffix in {".py", ".js", ".mjs", ".ts", ".vue", ".sh", ".yml", ".yaml"}:
                yield path


def security_static_scan():
    findings = []
    for path in iter_source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "pattern": pattern.pattern,
                        "offset": match.start(),
                    }
                )
    return {
        "status": "FAIL" if findings else "PASS",
        "summary": "业务源码未发现疑似硬编码密钥" if not findings else "业务源码存在疑似硬编码密钥",
        "findings": findings,
        "scope": SCAN_PATHS,
    }


def real_provider_config_gate():
    env_file = provider_env_file_path()
    env_file_values = read_env_file_values(env_file)
    sources = {
        name: source
        for name in REQUIRED_REAL_PROVIDER_ENV
        if (source := provider_config_value(name, env_file_values))
    }
    missing = [
        {"name": name, "description": description}
        for name, description in REQUIRED_REAL_PROVIDER_ENV.items()
        if name not in sources
    ]
    return {
        "status": "BLOCKED" if missing else "PASS",
        "summary": "真实服务配置缺失，禁止声明真实联调 PASS" if missing else "真实服务配置项已提供",
        "missing": missing,
        "sources": sources,
        "env_file": str(env_file.relative_to(ROOT)) if env_file.is_relative_to(ROOT) else str(env_file),
        "deferred": [
            {"name": name, "description": description, "reason": "用户确认华为 OCR 暂不配置和测试，先使用自研 OCR 插件"}
            for name, description in DEFERRED_REAL_PROVIDER_ENV.items()
        ],
        "current_evidence": "本地 Provider mock/contract 已验证；真实 Key 未提供时仅可进入 BLOCKED/NOT_VERIFIED",
        "unblock_condition": "提供高德和聚合天气真实配置并在 G4 后执行真实连接测试；华为 OCR 按 deferred/BLOCKED 另行处理",
    }


def build_payload():
    checks = {
        "security_static_scan": security_static_scan(),
        "real_provider_config_gate": real_provider_config_gate(),
    }
    statuses = {item["status"] for item in checks.values()}
    overall_status = "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"
    return {
        "schema_version": 1,
        "stage": current_stage(),
        "overall_status": overall_status,
        "checks": checks,
        "boundary": "本脚本只做本地静态检查和真实服务配置门禁，不执行真实服务联调",
    }


def main():
    parser = argparse.ArgumentParser(description="Coffee delivery gate checks")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    payload = build_payload()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={payload['overall_status']}")
        for name, check in payload["checks"].items():
            print(f"{name}={check['status']} {check['summary']}")
    return 1 if payload["overall_status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
