"""Build immutable offline review packages for submitted coffee events.

The Web export flow uses this module to produce a small self-contained package
with manifest.json, index.html and controlled photo copies. Raw event data still
stays in the database; the package is a review/export artifact.
"""

import hashlib
import html
import json
import shutil
from pathlib import Path

from apps.coffee.models import ProviderCallLog
from apps.coffee.serializers import serialize_offline_package_index


def _provider_logs_for_event(event):
    """Collect OCR/provider audit logs that belong to the event photos."""
    photo_ids = list(event.photos.values_list("photo_id", flat=True))
    return list(ProviderCallLog.objects.filter(target_type="photo", target_id__in=photo_ids).order_by("called_at", "id"))


def _write_json(path, payload):
    """Write deterministic JSON so package hashes stay reproducible."""
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str)
    path.write_text(text + "\n", encoding="utf-8")
    return text


def _render_index_html(manifest):
    """Render a minimal human-readable offline browser page."""
    package_index = manifest["offline_package_index"]
    resource_counts = package_index.get("resource_counts", {})
    photos = package_index.get("resources", {}).get("photos", [])
    photo_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(photo.get('photo_id') or '')}</td>"
        f"<td>{html.escape(photo.get('category') or '')}</td>"
        f"<td>{html.escape(photo.get('sha256') or '')}</td>"
        f"<td>{html.escape((photo.get('files') or {}).get('controlled') or (photo.get('files') or {}).get('watermarked') or '')}</td>"
        "</tr>"
        for photo in photos
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>离线数据包 {html.escape(manifest["event_id"])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #1f2933; }}
    h1 {{ font-size: 22px; margin-bottom: 8px; }}
    section {{ margin-top: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #d8dee4; padding: 8px; text-align: left; }}
    th {{ background: #f3f6f4; }}
    code {{ background: #f3f6f4; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>离线数据包</h1>
  <p>Event_ID：<code>{html.escape(manifest["event_id"])}</code></p>
  <p>Manifest Hash：<code>{html.escape(manifest.get("manifest_hash") or "")}</code></p>
  <p>Package Hash：<code>{html.escape(manifest.get("package_hash") or "")}</code></p>
  <section>
    <h2>资源计数</h2>
    <ul>
      <li>照片：{resource_counts.get("photos", 0)}</li>
      <li>OCR：{resource_counts.get("ocr_results", 0)}</li>
      <li>测量记录：{resource_counts.get("measurements", 0)}</li>
      <li>审计日志：{resource_counts.get("audit_logs", 0)}</li>
    </ul>
  </section>
  <section>
    <h2>照片资料</h2>
    <table>
      <thead><tr><th>Photo_ID</th><th>分类</th><th>SHA256</th><th>受控图片引用</th></tr></thead>
      <tbody>{photo_rows}</tbody>
    </table>
  </section>
</body>
</html>
"""


def _copy_controlled_photos(event, package_dir, package_index, media_root):
    """Copy watermarked/original photos into the package without mutating originals."""
    copied_files = []
    if media_root is None:
        return copied_files

    media_root = Path(media_root)
    controlled_dir = package_dir / "photos" / "controlled"
    photo_resources = package_index.get("resources", {}).get("photos", [])
    photo_resources_by_id = {item.get("photo_id"): item for item in photo_resources}
    for photo in event.photos.order_by("create_datetime", "id"):
        source_ref = photo.watermarked_file or photo.original_file
        if not source_ref:
            continue
        source_path = media_root / source_ref
        if not source_path.exists():
            continue
        suffix = source_path.suffix or ".jpg"
        relative_target = Path("photos") / "controlled" / f"{photo.photo_id}{suffix}"
        target_path = package_dir / relative_target
        controlled_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        controlled_ref = relative_target.as_posix()
        copied_files.append(controlled_ref)
        resource = photo_resources_by_id.get(photo.photo_id)
        if resource is not None:
            resource.setdefault("files", {})["controlled"] = controlled_ref
    return copied_files


def build_event_offline_package(event, output_root, media_root=None):
    """Build the offline package for one collection event and return file metadata."""
    output_root = Path(output_root)
    package_dir = output_root / event.event_id
    package_dir.mkdir(parents=True, exist_ok=True)

    package_index = serialize_offline_package_index(event, _provider_logs_for_event(event))
    copied_files = _copy_controlled_photos(event, package_dir, package_index, media_root)
    manifest = {
        "package_type": "coffee_event_offline_package",
        "package_version": 1,
        "event_id": event.event_id,
        "task_id": event.task_code,
        "manifest_hash": event.manifest_hash,
        "offline_package_index": package_index,
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True, default=str)
    package_hash = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    manifest["package_hash"] = package_hash

    _write_json(package_dir / "manifest.json", manifest)
    (package_dir / "index.html").write_text(_render_index_html(manifest), encoding="utf-8")

    return {
        "event_id": event.event_id,
        "package_dir": str(package_dir),
        "package_hash": package_hash,
        "files": ["manifest.json", "index.html", *copied_files],
    }
