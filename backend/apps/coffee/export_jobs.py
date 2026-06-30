from apps.coffee.models import CollectionEvent, ExportJob
from apps.coffee.offline_package import build_event_offline_package


def _mark_failed(job, message):
    job.status = ExportJob.STATUS_FAILED
    job.progress = 100
    job.error_message = message
    job.save(update_fields=["status", "progress", "error_message", "update_datetime"])
    return None


def process_export_job(job, output_root, media_root=None):
    job.status = ExportJob.STATUS_RUNNING
    job.progress = 10
    job.error_message = None
    job.save(update_fields=["status", "progress", "error_message", "update_datetime"])

    if job.export_type != ExportJob.TYPE_DATASET_PACKAGE:
        return _mark_failed(job, f"导出类型 {job.export_type} 暂未实现本地处理器")

    event_id = (job.filters_json or {}).get("event_id")
    if not event_id:
        return _mark_failed(job, "数据集包导出缺少 event_id")

    try:
        event = CollectionEvent.objects.select_related("plot", "point").get(event_id=event_id)
    except CollectionEvent.DoesNotExist:
        return _mark_failed(job, "采集事件不存在")

    package = build_event_offline_package(event, output_root, media_root=media_root)
    job.status = ExportJob.STATUS_SUCCESS
    job.progress = 100
    job.file_path = package["package_dir"]
    job.file_sha256 = package["package_hash"]
    job.error_message = None
    job.save(update_fields=["status", "progress", "file_path", "file_sha256", "error_message", "update_datetime"])
    return package
