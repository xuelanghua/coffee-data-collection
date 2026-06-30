from pathlib import Path

from django.conf import settings

from application.celery import app
from apps.coffee.export_jobs import process_export_job
from apps.coffee.models import ExportJob


def _default_export_root():
    configured_root = getattr(settings, "COFFEE_EXPORT_ROOT", None)
    if configured_root:
        return Path(configured_root)
    return Path(settings.BASE_DIR) / "media" / "coffee_exports"


def _default_media_root():
    configured_root = getattr(settings, "MEDIA_ROOT", None)
    if configured_root:
        return Path(configured_root)
    return None


@app.task(name="coffee.run_export_job")
def run_export_job(job_code, output_root=None, media_root=None):
    try:
        job = ExportJob.objects.get(job_code=job_code)
    except ExportJob.DoesNotExist:
        return {
            "job_code": job_code,
            "status": ExportJob.STATUS_FAILED,
            "error_message": "导出任务不存在",
        }

    package = process_export_job(
        job,
        Path(output_root) if output_root else _default_export_root(),
        media_root=Path(media_root) if media_root else _default_media_root(),
    )
    job.refresh_from_db()
    return {
        "job_code": job.job_code,
        "status": job.status,
        "progress": job.progress,
        "file_path": job.file_path,
        "file_sha256": job.file_sha256,
        "error_message": job.error_message,
        "package": package,
    }
