"""Request validators and response serializers for the coffee API.

Serializers in this module are deliberately split by caller:
- App serializers validate field-collection writes from UniApp.
- Web serializers shape list/detail/review/export payloads for the admin UI.
- Provider serializers mask secrets before any config reaches the frontend.
"""

import hashlib
import json

from rest_framework import serializers

from apps.coffee.models import (
    CollectionEvent,
    BGradeRule,
    EventFieldValue,
    ExportJob,
    MeasurementRecord,
    MetricDefinition,
    OCRCorrection,
    OCRResult,
    PhotoAnnotation,
    PhotoAsset,
    PhotoUploadChunk,
    Plot,
    Point,
    ProviderConfig,
    QualityReview,
)


class AppPlotCreateSerializer(serializers.Serializer):
    """Validate field-drawn plot payloads from the App map workflow."""

    task_id = serializers.CharField(max_length=64)
    plot_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    name = serializers.CharField(max_length=128)
    boundary_geojson = serializers.JSONField()
    area_mu = serializers.DecimalField(max_digits=12, decimal_places=4)
    area_calc_method = serializers.ChoiceField(choices=Plot.AREA_METHOD_CHOICES, default=Plot.AREA_GEODESIC)
    coordinate_system = serializers.ChoiceField(choices=Plot.COORD_CHOICES, default=Plot.COORD_GCJ02)
    source_type = serializers.ChoiceField(choices=Plot.SOURCE_CHOICES, default=Plot.SOURCE_APP_DRAWN)
    idempotency_key = serializers.CharField(max_length=128, write_only=True)

    def validate_boundary_geojson(self, value):
        if value.get("type") != "Polygon" or not value.get("coordinates"):
            raise serializers.ValidationError("boundary_geojson must be a Polygon")
        return value


class AppPointCreateSerializer(serializers.Serializer):
    """Validate sampling point creation inside an existing plot."""

    task_id = serializers.CharField(max_length=64)
    plot_id = serializers.CharField(max_length=64)
    point_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    longitude = serializers.DecimalField(max_digits=12, decimal_places=8)
    latitude = serializers.DecimalField(max_digits=12, decimal_places=8)
    altitude = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    coordinate_system = serializers.ChoiceField(choices=Point.COORD_CHOICES, default=Point.COORD_GCJ02)
    source_type = serializers.ChoiceField(choices=Point.SOURCE_CHOICES, default=Point.SOURCE_APP_SELECTED)
    idempotency_key = serializers.CharField(max_length=128, write_only=True)


class AppEventCreateSerializer(serializers.Serializer):
    """Validate draft collection-event creation before photos/OCR are uploaded."""

    task_id = serializers.CharField(max_length=64)
    plot_id = serializers.CharField(max_length=64)
    point_id = serializers.CharField(max_length=64)
    event_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128)
    manifest_hash = serializers.CharField(max_length=128)
    location_snapshot = serializers.JSONField(required=False)
    weather_snapshot = serializers.JSONField(required=False)


class AppFieldValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventFieldValue
        fields = (
            "field_code",
            "field_label",
            "value_text",
            "value_number",
            "value_json",
            "unit",
            "source_type",
            "source_photo_id",
            "ocr_result_id",
            "ocr_raw_value",
            "ocr_confidence",
            "corrected_from",
            "correction_reason",
        )


class AppMeasurementSerializer(serializers.ModelSerializer):
    client_measurement_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
    retake_of_client_id = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = MeasurementRecord
        fields = (
            "client_measurement_id",
            "retake_of_client_id",
            "device_no",
            "measured_at",
            "wind_speed",
            "wind_direction",
            "air_temperature",
            "air_humidity",
            "atmospheric_pressure",
            "rainfall",
            "soil_moisture",
            "soil_temperature",
            "soil_salinity",
            "soil_ph",
            "source_photo_id",
            "ocr_result_id",
            "is_abnormal",
            "remark",
        )


class AppEventSubmitSerializer(serializers.Serializer):
    """Validate the final App manifest, corrected fields and measurements."""

    idempotency_key = serializers.CharField(max_length=128)
    manifest = serializers.JSONField(required=False)
    field_values = AppFieldValueSerializer(many=True, required=False)
    measurements = AppMeasurementSerializer(many=True, required=False)
    ocr_corrections = serializers.ListField(child=serializers.DictField(), required=False)
    submit_note = serializers.CharField(required=False, allow_blank=True)


class AppPhotoInitSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=64)
    photo_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=PhotoAsset.CATEGORY_CHOICES)
    sha256 = serializers.CharField(max_length=128)
    metadata = serializers.JSONField(required=False)


class AppPhotoCompleteSerializer(serializers.Serializer):
    original_file = serializers.CharField(max_length=512)
    watermarked_file = serializers.CharField(max_length=512, required=False, allow_blank=True)
    sha256 = serializers.CharField(max_length=128)
    precheck_status = serializers.ChoiceField(choices=PhotoAsset.PRECHECK_CHOICES, default=PhotoAsset.PRECHECK_PASS)
    chunk_count = serializers.IntegerField(required=False, min_value=1)
    chunk_hashes = serializers.ListField(child=serializers.CharField(max_length=128), required=False)


class AppPhotoChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoUploadChunk
        fields = ("chunk_hash", "chunk_size")


class AppOCRStartSerializer(serializers.Serializer):
    photo_id = serializers.CharField(max_length=64)
    provider = serializers.ChoiceField(choices=OCRResult.PROVIDER_CHOICES)
    structured_json = serializers.JSONField(required=False)
    raw_response = serializers.JSONField(required=False)
    confidence = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, allow_null=True)


class AppOCRCorrectionSerializer(serializers.Serializer):
    field_name = serializers.CharField(max_length=64)
    raw_value = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    corrected_value = serializers.CharField(max_length=255)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)


class ReviewApproveSerializer(serializers.Serializer):
    review_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ReviewReturnSerializer(serializers.Serializer):
    return_reason = serializers.CharField(max_length=128)
    return_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    return_items = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=False)


class BulkApproveSerializer(ReviewApproveSerializer):
    event_ids = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=False)


class BulkReturnSerializer(ReviewReturnSerializer):
    event_ids = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=False)


class PhotoReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=(
            (PhotoAsset.REVIEW_APPROVED, "审核通过"),
            (PhotoAsset.REVIEW_RETURNED, "退回补拍"),
        )
    )
    review_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    return_reason = serializers.CharField(max_length=128, required=False, allow_blank=True, allow_null=True)
    return_items = serializers.ListField(child=serializers.CharField(max_length=64), required=False)

    def validate(self, attrs):
        if attrs["status"] == PhotoAsset.REVIEW_RETURNED and not attrs.get("return_items"):
            raise serializers.ValidationError({"return_items": "退回补拍必须至少包含一个退回项"})
        return attrs


class PhotoAnnotationCreateSerializer(serializers.Serializer):
    annotation_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    label = serializers.CharField(max_length=64)
    shape_type = serializers.ChoiceField(choices=PhotoAnnotation.SHAPE_CHOICES, default=PhotoAnnotation.SHAPE_BBOX)
    geometry = serializers.JSONField()
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    def validate_geometry(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("geometry must be a non-empty object")
        return value


class ProviderConfigSerializer(serializers.ModelSerializer):
    """Validate Provider configuration while allowing later output masking."""

    class Meta:
        model = ProviderConfig
        fields = (
            "provider_type",
            "provider_name",
            "display_name",
            "enabled",
            "priority",
            "timeout_ms",
            "rate_limit_per_minute",
            "config_json",
            "secret_fields",
        )

    def validate_secret_fields(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("secret_fields must be a list")
        return value


class ExportJobCreateSerializer(serializers.Serializer):
    export_type = serializers.ChoiceField(choices=ExportJob.TYPE_CHOICES)
    filters = serializers.JSONField(required=False)


class BGradeRuleCreateSerializer(serializers.ModelSerializer):
    task_id = serializers.CharField(source="task_code", max_length=64)

    class Meta:
        model = BGradeRule
        fields = (
            "rule_name",
            "task_id",
            "metric",
            "min_count",
            "max_count",
            "block_level",
            "enabled",
        )

    def validate(self, attrs):
        if attrs.get("min_count") is None and attrs.get("max_count") is None:
            raise serializers.ValidationError("min_count 和 max_count 至少需要填写一个")
        return attrs


class MetricDefinitionSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = MetricDefinition
        fields = (
            "metric_code",
            "metric_name",
            "metric_group",
            "calculation_method",
            "description",
            "unit",
            "enabled",
        )


def serialize_metric_definition(metric):
    """Return one metric-definition version for statistics configuration UI."""
    return {
        "metric_code": metric.metric_code,
        "metric_name": metric.metric_name,
        "metric_group": metric.metric_group,
        "calculation_method": metric.calculation_method,
        "description": metric.description,
        "unit": metric.unit,
        "enabled": metric.enabled,
        "version": metric.version,
        "created_at": metric.create_datetime.isoformat() if metric.create_datetime else None,
        "updated_at": metric.update_datetime.isoformat() if metric.update_datetime else None,
    }


def serialize_plot(plot):
    return {
        "plot_id": plot.plot_id,
        "task_id": plot.task_code,
        "name": plot.name,
        "area_mu": str(plot.area_mu),
        "area_calc_method": plot.area_calc_method,
        "coordinate_system": plot.coordinate_system,
        "source_type": plot.source_type,
        "created_in_field": plot.created_in_field,
        "review_status": plot.review_status,
        "area_check_status": plot.area_check_status,
    }


def serialize_point(point):
    return {
        "point_id": point.point_id,
        "task_id": point.task_code,
        "plot_id": point.plot.plot_id,
        "longitude": str(point.longitude),
        "latitude": str(point.latitude),
        "altitude": str(point.altitude) if point.altitude is not None else None,
        "coordinate_system": point.coordinate_system,
        "source_type": point.source_type,
        "created_in_field": point.created_in_field,
        "review_status": point.review_status,
    }


def serialize_event(event):
    return {
        "event_id": event.event_id,
        "task_id": event.task_code,
        "plot_id": event.plot.plot_id,
        "point_id": event.point.point_id,
        "status": event.status,
        "version": event.version,
        "manifest_hash": event.manifest_hash,
        "field_value_count": event.field_values.count(),
        "measurement_count": event.measurements.count(),
    }


def serialize_event_list_item(event):
    latest_review = event.quality_reviews.order_by("-version").first()
    ocr_statuses = set(event.photos.values_list("ocr_results__status", flat=True))
    ocr_statuses.discard(None)
    if not ocr_statuses:
        ocr_status = "none"
    elif len(ocr_statuses) == 1:
        ocr_status = next(iter(ocr_statuses))
    else:
        ocr_status = "mixed"
    return {
        "event_id": event.event_id,
        "task_id": event.task_code,
        "plot_id": event.plot.plot_id,
        "point_id": event.point.point_id,
        "collector_id": event.collector_id,
        "status": event.status,
        "version": event.version,
        "photo_count": event.photos.count(),
        "ocr_status": ocr_status,
        "quality_status": latest_review.status if latest_review else "pending",
        "submitted_at": event.submitted_at.isoformat() if event.submitted_at else None,
    }


def serialize_field_value(field_value):
    return {
        "field_code": field_value.field_code,
        "field_label": field_value.field_label,
        "value_text": field_value.value_text,
        "value_number": str(field_value.value_number) if field_value.value_number is not None else None,
        "value_json": field_value.value_json,
        "unit": field_value.unit,
        "source_type": field_value.source_type,
        "source_photo_id": field_value.source_photo_id,
        "ocr_result_id": field_value.ocr_result_id,
        "ocr_raw_value": field_value.ocr_raw_value,
        "ocr_confidence": str(field_value.ocr_confidence) if field_value.ocr_confidence is not None else None,
        "corrected_from": field_value.corrected_from,
        "correction_reason": field_value.correction_reason,
        "version": field_value.version,
    }


def serialize_measurement(measurement):
    return {
        "device_no": measurement.device_no,
        "measured_at": measurement.measured_at.isoformat() if measurement.measured_at else None,
        "wind_speed": str(measurement.wind_speed) if measurement.wind_speed is not None else None,
        "wind_direction": measurement.wind_direction,
        "air_temperature": str(measurement.air_temperature) if measurement.air_temperature is not None else None,
        "air_humidity": str(measurement.air_humidity) if measurement.air_humidity is not None else None,
        "atmospheric_pressure": str(measurement.atmospheric_pressure) if measurement.atmospheric_pressure is not None else None,
        "rainfall": str(measurement.rainfall) if measurement.rainfall is not None else None,
        "soil_moisture": str(measurement.soil_moisture) if measurement.soil_moisture is not None else None,
        "soil_temperature": str(measurement.soil_temperature) if measurement.soil_temperature is not None else None,
        "soil_salinity": str(measurement.soil_salinity) if measurement.soil_salinity is not None else None,
        "soil_ph": str(measurement.soil_ph) if measurement.soil_ph is not None else None,
        "source_photo_id": measurement.source_photo_id,
        "ocr_result_id": measurement.ocr_result_id,
        "is_abnormal": measurement.is_abnormal,
        "remark": measurement.remark,
    }


def serialize_photo(photo):
    upload_session_id = photo.metadata_json.get("upload_session_id") if isinstance(photo.metadata_json, dict) else None
    return {
        "photo_id": photo.photo_id,
        "event_id": photo.event.event_id,
        "category": photo.category,
        "original_file": photo.original_file,
        "watermarked_file": photo.watermarked_file,
        "sha256": photo.sha256,
        "metadata": photo.metadata_json,
        "precheck_status": photo.precheck_status,
        "review_status": photo.review_status,
        "immutable_status": photo.immutable_status,
        "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else None,
        "upload_session_id": upload_session_id,
        "uploaded_chunk_count": photo.upload_chunks.count(),
    }


def serialize_photo_list_item(photo):
    latest_ocr = photo.ocr_results.order_by("-create_datetime", "-id").first()
    return {
        **serialize_photo(photo),
        "plot_id": photo.event.plot.plot_id,
        "point_id": photo.event.point.point_id,
        "task_id": photo.event.task_code,
        "ocr_count": photo.ocr_results.count(),
        "latest_ocr_status": latest_ocr.status if latest_ocr else "none",
        "latest_ocr_confidence": str(latest_ocr.confidence) if latest_ocr and latest_ocr.confidence is not None else None,
    }


def serialize_photo_annotation(annotation):
    return {
        "annotation_id": annotation.annotation_id,
        "photo_id": annotation.photo.photo_id,
        "label": annotation.label,
        "shape_type": annotation.shape_type,
        "geometry": annotation.geometry_json,
        "version": annotation.version,
        "is_latest": annotation.is_latest,
        "source": annotation.source,
        "annotated_by": annotation.annotated_by,
        "note": annotation.note,
        "created_at": annotation.create_datetime.isoformat() if annotation.create_datetime else None,
    }


def serialize_ocr_correction(correction):
    return {
        "field_name": correction.field_name,
        "raw_value": correction.raw_value,
        "corrected_value": correction.corrected_value,
        "reason": correction.reason,
        "version": correction.version,
        "corrected_by": correction.corrected_by,
        "corrected_at": correction.corrected_at.isoformat() if correction.corrected_at else None,
    }


def serialize_ocr_result(ocr_result):
    return {
        "ocr_result_id": ocr_result.ocr_result_id,
        "photo_id": ocr_result.photo.photo_id,
        "provider": ocr_result.provider,
        "status": ocr_result.status,
        "structured_json": ocr_result.structured_json,
        "confidence": str(ocr_result.confidence) if ocr_result.confidence is not None else None,
        "error_code": ocr_result.error_code,
        "error_message": ocr_result.error_message,
        "corrections": [serialize_ocr_correction(item) for item in ocr_result.corrections.order_by("field_name", "version")],
    }


def serialize_ocr_job_item(ocr_result):
    return {
        **serialize_ocr_result(ocr_result),
        "event_id": ocr_result.photo.event.event_id,
        "plot_id": ocr_result.photo.event.plot.plot_id,
        "point_id": ocr_result.photo.event.point.point_id,
        "correction_count": ocr_result.corrections.count(),
        "started_at": ocr_result.started_at.isoformat() if ocr_result.started_at else None,
        "finished_at": ocr_result.finished_at.isoformat() if ocr_result.finished_at else None,
    }


def serialize_provider_call_log(log):
    return {
        "provider_type": log.provider_type,
        "provider_name": log.provider_name,
        "request_id": log.request_id,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "status": log.status,
        "latency_ms": log.latency_ms,
        "raw_response_ref": log.raw_response_ref,
        "error_code": log.error_code,
        "called_at": log.called_at.isoformat() if log.called_at else None,
    }


def mask_provider_config(config):
    """Mask sensitive Provider config values before returning them to Web."""
    config_json = config.config_json if isinstance(config.config_json, dict) else {}
    secret_fields = set(config.secret_fields if isinstance(config.secret_fields, list) else [])
    return {
        key: "********" if key in secret_fields and value not in (None, "") else value
        for key, value in config_json.items()
    }


def serialize_provider_config(config):
    return {
        "id": config.id,
        "provider_type": config.provider_type,
        "provider_name": config.provider_name,
        "display_name": config.display_name,
        "enabled": config.enabled,
        "priority": config.priority,
        "timeout_ms": config.timeout_ms,
        "rate_limit_per_minute": config.rate_limit_per_minute,
        "config_status": config.config_status,
        "masked_config": mask_provider_config(config),
        "secret_fields": config.secret_fields,
        "version": config.version,
        "updated_at": config.update_datetime.isoformat() if config.update_datetime else None,
    }


def serialize_export_job(job):
    return {
        "job_code": job.job_code,
        "export_type": job.export_type,
        "filters": job.filters_json,
        "status": job.status,
        "progress": job.progress,
        "file_path": job.file_path,
        "file_sha256": job.file_sha256,
        "created_by": job.created_by,
        "expires_at": job.expires_at.isoformat() if job.expires_at else None,
        "error_message": job.error_message,
        "created_at": job.create_datetime.isoformat() if job.create_datetime else None,
    }


def serialize_b_grade_rule(rule):
    return {
        "rule_code": rule.rule_code,
        "rule_name": rule.rule_name,
        "task_id": rule.task_code,
        "metric": rule.metric,
        "min_count": rule.min_count,
        "max_count": rule.max_count,
        "block_level": rule.block_level,
        "enabled": rule.enabled,
        "version": rule.version,
    }


def serialize_quality_review(review):
    return {
        "review_type": review.review_type,
        "status": review.status,
        "reviewer_id": review.reviewer_id,
        "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
        "result_json": review.result_json,
        "return_reason": review.return_reason,
        "return_items": review.return_items,
        "version": review.version,
    }


def serialize_offline_package_index(event, provider_logs):
    """Build a deterministic index used by event detail and offline packages."""
    photos = list(event.photos.order_by("create_datetime", "id"))
    field_values = list(event.field_values.order_by("field_code", "version", "id"))
    measurements = list(event.measurements.order_by("create_datetime", "id"))
    quality_reviews = list(event.quality_reviews.order_by("version", "id"))
    ocr_results = []
    annotations = []
    photo_resources = []
    for photo in photos:
        photo_resources.append(
            {
                "photo_id": photo.photo_id,
                "category": photo.category,
                "sha256": photo.sha256,
                "files": {
                    "original": photo.original_file,
                    "watermarked": photo.watermarked_file,
                },
                "metadata": photo.metadata_json,
                "precheck_status": photo.precheck_status,
                "review_status": photo.review_status,
                "immutable_status": photo.immutable_status,
            }
        )
        for ocr_result in photo.ocr_results.order_by("create_datetime", "id"):
            ocr_results.append(serialize_ocr_result(ocr_result))
        for annotation in photo.annotations.order_by("annotation_id", "version", "id"):
            annotations.append(serialize_photo_annotation(annotation))

    index = {
        "package_version": 1,
        "event_id": event.event_id,
        "task_id": event.task_code,
        "manifest_hash": event.manifest_hash,
        "resources": {
            "event": serialize_event(event),
            "plot": serialize_plot(event.plot),
            "point": serialize_point(event.point),
            "field_values": [serialize_field_value(item) for item in field_values],
            "measurements": [serialize_measurement(item) for item in measurements],
            "photos": photo_resources,
            "ocr_results": ocr_results,
            "annotations": annotations,
            "quality_reviews": [serialize_quality_review(item) for item in quality_reviews],
            "audit_logs": [serialize_provider_call_log(item) for item in provider_logs],
        },
        "resource_counts": {
            "field_values": len(field_values),
            "measurements": len(measurements),
            "photos": len(photos),
            "ocr_results": len(ocr_results),
            "annotations": len(annotations),
            "quality_reviews": len(quality_reviews),
            "audit_logs": len(provider_logs),
        },
    }
    digest_payload = json.dumps(index, ensure_ascii=False, sort_keys=True, default=str)
    index["index_hash"] = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
    return index


def serialize_event_detail(event, provider_logs):
    """Return the full Web detail page payload for one collection event."""
    provider_logs = list(provider_logs)
    photos = []
    for photo in event.photos.order_by("create_datetime", "id"):
        photos.append(
            {
                "photo": serialize_photo(photo),
                "ocr_results": [serialize_ocr_result(item) for item in photo.ocr_results.order_by("create_datetime", "id")],
                "annotations": [serialize_photo_annotation(item) for item in photo.annotations.order_by("annotation_id", "version", "id")],
            }
        )
    return {
        "event": serialize_event(event),
        "task": {"task_id": event.task_code},
        "plot": serialize_plot(event.plot),
        "point": serialize_point(event.point),
        "field_values": [serialize_field_value(item) for item in event.field_values.order_by("field_code", "version", "id")],
        "photos": photos,
        "measurements": [serialize_measurement(item) for item in event.measurements.order_by("create_datetime", "id")],
        "quality_reviews": [serialize_quality_review(item) for item in event.quality_reviews.order_by("version", "id")],
        "audit_logs": [serialize_provider_call_log(item) for item in provider_logs],
        "offline_package_index": serialize_offline_package_index(event, provider_logs),
    }
