"""Coffee API views for App collection and Web management.

The view layer is the integration boundary between django-vue3-admin users/
permissions and the coffee domain models. App endpoints optimize for field
collection, idempotency and offline upload recovery; Web endpoints optimize for
review, correction, statistics and export workflows.
"""

import hashlib
import json
import time
import uuid

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from dvadmin.utils.json_response import DetailResponse, ErrorResponse
from dvadmin.system.models import Users

from apps.coffee.models import (
    BGradeRule,
    CollectionEvent,
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
    PlotBoundaryVersion,
    Point,
    ProviderConfig,
    ProviderCallLog,
    QualityReview,
)
from apps.coffee.numbering import next_business_id
from apps.coffee.providers import OCRProviderResult, call_ocr_provider, provider_local_contract
from apps.coffee.serializers import (
    AppEventCreateSerializer,
    AppEventSubmitSerializer,
    AppOCRCorrectionSerializer,
    AppOCRStartSerializer,
    AppPhotoCompleteSerializer,
    AppPhotoChunkSerializer,
    AppPhotoInitSerializer,
    AppPlotCreateSerializer,
    AppPointCreateSerializer,
    BGradeRuleCreateSerializer,
    BulkApproveSerializer,
    BulkReturnSerializer,
    ExportJobCreateSerializer,
    MetricDefinitionSerializer,
    PhotoReviewSerializer,
    PhotoAnnotationCreateSerializer,
    ProviderConfigSerializer,
    ReviewApproveSerializer,
    ReviewReturnSerializer,
    serialize_b_grade_rule,
    serialize_event,
    serialize_event_detail,
    serialize_event_list_item,
    serialize_export_job,
    serialize_metric_definition,
    serialize_ocr_correction,
    serialize_ocr_job_item,
    serialize_ocr_result,
    serialize_photo,
    serialize_photo_annotation,
    serialize_photo_list_item,
    serialize_plot,
    serialize_point,
    serialize_provider_config,
    serialize_quality_review,
)
from apps.coffee.tasks import run_export_job


def _collector_id(request):
    user_id = getattr(request.user, "id", None)
    return str(user_id) if user_id is not None else None


def _event_owner_error(request, event):
    """Return a 403 response when an App user tries to mutate another event."""
    if event.collector_id == _collector_id(request):
        return None
    return ErrorResponse(msg="无权操作该采集事件", code="COFFEE_EVENT_FORBIDDEN", status=403)


def _validation_error(serializer):
    return ErrorResponse(data=serializer.errors, msg="字段校验失败", code="COFFEE_VALIDATION_ERROR", status=400)


def _digest(value):
    payload = json.dumps(value or {}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reviewer_id(request):
    user_id = getattr(request.user, "id", None)
    return str(user_id) if user_id is not None else None


def _next_review_version(event):
    latest = event.quality_reviews.order_by("-version").first()
    return (latest.version + 1) if latest else 1


def _user_role_keys(user):
    role_manager = getattr(user, "role", None)
    if role_manager is None:
        return set()
    return set(role_manager.values_list("key", flat=True))


def _apply_event_data_scope(queryset, user):
    """Apply coffee role-based event visibility without bypassing dvadmin roles."""
    if getattr(user, "is_superuser", False):
        return queryset
    role_keys = _user_role_keys(user)
    if "coffee_admin" in role_keys:
        return queryset
    elevated_roles = {"coffee_reviewer", "coffee_viewer"}
    if "coffee_collector" in role_keys and role_keys.isdisjoint(elevated_roles):
        return queryset.filter(collector_id=str(user.id))
    dept_id = getattr(user, "dept_id", None)
    if role_keys.intersection(elevated_roles) and dept_id:
        return queryset.filter(dept_belong_id=str(dept_id))
    return queryset


def _apply_dept_data_scope(queryset, user):
    if getattr(user, "is_superuser", False):
        return queryset
    role_keys = _user_role_keys(user)
    if "coffee_admin" in role_keys:
        return queryset
    dept_id = getattr(user, "dept_id", None)
    if role_keys.intersection({"coffee_reviewer", "coffee_viewer"}) and dept_id:
        return queryset.filter(dept_belong_id=str(dept_id))
    return queryset


def _create_review(event, *, status, reviewer_id, result_json=None, return_reason=None, return_items=None):
    """Create a versioned event-level review and move the event status."""
    review = QualityReview.objects.create(
        event=event,
        review_type=QualityReview.REVIEW_TYPE_EVENT,
        status=status,
        reviewer_id=reviewer_id,
        reviewed_at=timezone.now(),
        result_json=result_json or {},
        return_reason=return_reason,
        return_items=return_items or [],
        version=_next_review_version(event),
    )
    event.status = CollectionEvent.STATUS_APPROVED if status == QualityReview.STATUS_APPROVED else CollectionEvent.STATUS_RETURNED
    event.save(update_fields=["status", "update_datetime"])
    return review


def _create_photo_review(photo, *, status, reviewer_id, result_json=None, return_reason=None, return_items=None):
    """Create a versioned photo review and update the photo review state."""
    review = QualityReview.objects.create(
        event=photo.event,
        review_type=QualityReview.REVIEW_TYPE_PHOTO,
        status=status,
        reviewer_id=reviewer_id,
        reviewed_at=timezone.now(),
        result_json={
            "photo_id": photo.photo_id,
            **(result_json or {}),
        },
        return_reason=return_reason,
        return_items=return_items or [],
        version=_next_review_version(photo.event),
    )
    photo.review_status = PhotoAsset.REVIEW_APPROVED if status == QualityReview.STATUS_APPROVED else PhotoAsset.REVIEW_RETURNED
    photo.save(update_fields=["review_status", "update_datetime"])
    return review


class CoffeeMobileLoginView(APIView):
    """Mobile login adapter using dvadmin Users and SimpleJWT tokens."""

    permission_classes = []

    def post(self, request):
        phone = request.data.get("phone") or request.data.get("username")
        password = request.data.get("password")
        if not phone or not password:
            return ErrorResponse(msg="手机号和密码不能为空", code=4000, status=400)
        try:
            user = Users.objects.get(mobile=phone)
        except Users.DoesNotExist:
            return ErrorResponse(msg="手机号或密码错误", code=4000, status=400)
        except Users.MultipleObjectsReturned:
            return ErrorResponse(msg="手机号关联多个账号，请联系管理员", code=4000, status=400)
        if not user.is_active:
            return ErrorResponse(msg="账号已禁用", code=4000, status=400)
        if not user.check_password(password):
            return ErrorResponse(msg="手机号或密码错误", code=4000, status=400)

        refresh = RefreshToken.for_user(user)
        role_info = list(user.role.values("id", "name", "key"))
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "username": user.username,
            "name": user.name,
            "userId": user.id,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "pwd_change_count": user.pwd_change_count,
            "language": getattr(user, "language", "zh-cn") or "zh-cn",
            "role_info": role_info,
        }
        return Response({"code": 2000, "msg": "请求成功", "data": data})


def _append_submission_records(event, data, *, field_version):
    """Persist submitted field values and measurement/retake relationships."""
    for field in data.get("field_values") or []:
        EventFieldValue.objects.create(event=event, version=field_version, **field)

    measurement_client_ids = {}
    pending_retake_links = []
    for measurement in data.get("measurements") or []:
        client_measurement_id = measurement.pop("client_measurement_id", None)
        retake_of_client_id = measurement.pop("retake_of_client_id", None)
        record = MeasurementRecord.objects.create(event=event, **measurement)
        if client_measurement_id:
            measurement_client_ids[client_measurement_id] = record
        if retake_of_client_id:
            pending_retake_links.append((record, retake_of_client_id))

    for record, retake_of_client_id in pending_retake_links:
        original = measurement_client_ids.get(retake_of_client_id)
        if original:
            record.retake_of = original
            record.save(update_fields=["retake_of", "update_datetime"])


def _counts_by(queryset, field_name):
    return {item[field_name] or "unknown": item["count"] for item in queryset.values(field_name).annotate(count=Count("id")).order_by(field_name)}


def _latest_metric_definitions(metric_group):
    """Return the latest enabled metric definition per metric code."""
    latest_by_code = {}
    queryset = MetricDefinition.objects.filter(metric_group=metric_group, enabled=True).order_by("metric_code", "-version", "-id")
    for metric in queryset:
        if metric.metric_code not in latest_by_code:
            latest_by_code[metric.metric_code] = metric
    return [latest_by_code[code] for code in sorted(latest_by_code)]


def _b_grade_actual_count(rule):
    queryset = CollectionEvent.objects.filter(task_code=rule.task_code)
    if rule.metric == BGradeRule.METRIC_APPROVED_EVENT_COUNT:
        return queryset.filter(status=CollectionEvent.STATUS_APPROVED).count()
    if rule.metric == BGradeRule.METRIC_RETURNED_EVENT_COUNT:
        return queryset.filter(status=CollectionEvent.STATUS_RETURNED).count()
    if rule.metric == BGradeRule.METRIC_SUBMITTED_EVENT_COUNT:
        return queryset.filter(status__in=[CollectionEvent.STATUS_SUBMITTED, CollectionEvent.STATUS_APPROVED, CollectionEvent.STATUS_RETURNED]).count()
    return 0


def _check_b_grade_rule(rule):
    """Evaluate one B-grade rule against current collection-event counts."""
    actual_count = _b_grade_actual_count(rule)
    failed_reasons = []
    if rule.min_count is not None and actual_count < rule.min_count:
        failed_reasons.append("below_min_count")
    if rule.max_count is not None and actual_count > rule.max_count:
        failed_reasons.append("above_max_count")
    status = "fail" if failed_reasons else "pass"
    return {
        "rule": serialize_b_grade_rule(rule),
        "status": status,
        "actual_count": actual_count,
        "failed_reasons": failed_reasons,
        "blocking": status == "fail" and rule.block_level == BGradeRule.LEVEL_BLOCKING,
    }


class AppPlotCreateView(APIView):
    """Create a field-drawn plot and its first boundary version."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = AppPlotCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        plot_id = data.get("plot_id") or next_business_id("PL")
        plot, created = Plot.objects.get_or_create(
            plot_id=plot_id,
            defaults={
                "task_code": data["task_id"],
                "name": data["name"],
                "boundary_geojson": data["boundary_geojson"],
                "area_mu": data["area_mu"],
                "area_calc_method": data["area_calc_method"],
                "coordinate_system": data["coordinate_system"],
                "source_type": data["source_type"],
                "created_in_field": True,
                "collector_id": _collector_id(request),
                "review_status": Plot.REVIEW_PENDING,
                "area_check_status": Plot.AREA_NOT_CHECKED,
            },
        )
        if created:
            PlotBoundaryVersion.objects.create(
                plot=plot,
                version=1,
                boundary_geojson=plot.boundary_geojson,
                area_mu=plot.area_mu,
                area_calc_method=plot.area_calc_method,
                coordinate_system=plot.coordinate_system,
                source_type=plot.source_type,
            )
        return DetailResponse(data=serialize_plot(plot), msg="创建地块成功")


class AppPointCreateView(APIView):
    """Create a sampling point under an existing field plot."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = AppPointCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        point_id = data.get("point_id") or next_business_id("PT")
        try:
            plot = Plot.objects.get(plot_id=data["plot_id"], task_code=data["task_id"])
        except Plot.DoesNotExist:
            return ErrorResponse(msg="地块不存在或不属于当前任务", code="COFFEE_PLOT_NOT_FOUND", status=404)

        point, _ = Point.objects.get_or_create(
            point_id=point_id,
            defaults={
                "task_code": data["task_id"],
                "plot": plot,
                "longitude": data["longitude"],
                "latitude": data["latitude"],
                "altitude": data.get("altitude"),
                "coordinate_system": data["coordinate_system"],
                "source_type": data["source_type"],
                "created_in_field": True,
                "collector_id": _collector_id(request),
                "review_status": Point.REVIEW_PENDING,
            },
        )
        return DetailResponse(data=serialize_point(point), msg="创建点位成功")


class AppEventCreateView(APIView):
    """Create the App draft collection event before photos and OCR."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = AppEventCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        event_id = data.get("event_id") or next_business_id("EV")
        try:
            plot = Plot.objects.get(plot_id=data["plot_id"], task_code=data["task_id"])
            point = Point.objects.get(point_id=data["point_id"], plot=plot, task_code=data["task_id"])
        except (Plot.DoesNotExist, Point.DoesNotExist):
            return ErrorResponse(msg="地块或点位不存在", code="COFFEE_TARGET_NOT_FOUND", status=404)

        event, _ = CollectionEvent.objects.get_or_create(
            idempotency_key=data["idempotency_key"],
            defaults={
                "event_id": event_id,
                "task_code": data["task_id"],
                "plot": plot,
                "point": point,
                "collector_id": _collector_id(request),
                "status": CollectionEvent.STATUS_DRAFT,
                "manifest_hash": data["manifest_hash"],
                "location_snapshot": data.get("location_snapshot") or {},
                "weather_snapshot": data.get("weather_snapshot") or {},
            },
        )
        return DetailResponse(data=serialize_event(event), msg="创建采集事件成功")


class AppEventSubmitView(APIView):
    """Submit an App event manifest with corrected fields and measurements."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, event_id):
        serializer = AppEventSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        photo_id = data.get("photo_id") or next_business_id("PH")
        try:
            event = CollectionEvent.objects.select_for_update().get(event_id=event_id)
        except CollectionEvent.DoesNotExist:
            return ErrorResponse(msg="采集事件不存在", code="COFFEE_EVENT_NOT_FOUND", status=404)

        owner_error = _event_owner_error(request, event)
        if owner_error:
            return owner_error

        if event.idempotency_key != data["idempotency_key"]:
            return ErrorResponse(msg="幂等键不匹配", code="COFFEE_IDEMPOTENCY_MISMATCH", status=409)

        if event.status == CollectionEvent.STATUS_SUBMITTED:
            return DetailResponse(data=serialize_event(event), msg="采集事件已提交")

        manifest = data.get("manifest") or {}
        event.manifest_hash = manifest.get("manifest_hash") or event.manifest_hash
        event.status = CollectionEvent.STATUS_SUBMITTED
        event.submitted_at = timezone.now()
        event.save(update_fields=["manifest_hash", "status", "submitted_at", "update_datetime"])

        _append_submission_records(event, data, field_version=event.version)

        return DetailResponse(data=serialize_event(event), msg="提交采集事件成功")


class AppEventResubmitView(APIView):
    """Resubmit an event after Web review returns it for correction."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, event_id):
        serializer = AppEventSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        try:
            event = CollectionEvent.objects.select_for_update().get(event_id=event_id)
        except CollectionEvent.DoesNotExist:
            return ErrorResponse(msg="采集事件不存在", code="COFFEE_EVENT_NOT_FOUND", status=404)

        owner_error = _event_owner_error(request, event)
        if owner_error:
            return owner_error

        if event.status != CollectionEvent.STATUS_RETURNED:
            return ErrorResponse(msg="只有退回状态的采集事件允许重新提交", code="COFFEE_EVENT_NOT_RETURNED", status=409)

        manifest = data.get("manifest") or {}
        event.version += 1
        event.manifest_hash = manifest.get("manifest_hash") or event.manifest_hash
        event.status = CollectionEvent.STATUS_SUBMITTED
        event.submitted_at = timezone.now()
        event.save(update_fields=["version", "manifest_hash", "status", "submitted_at", "update_datetime"])

        _append_submission_records(event, data, field_version=event.version)

        return DetailResponse(data=serialize_event(event), msg="重新提交采集事件成功")


class AppPhotoInitView(APIView):
    """Reserve a Photo_ID and upload session before chunked upload starts."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = AppPhotoInitSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        photo_id = data.get("photo_id") or next_business_id("PH")
        try:
            event = CollectionEvent.objects.get(event_id=data["event_id"])
        except CollectionEvent.DoesNotExist:
            return ErrorResponse(msg="采集事件不存在", code="COFFEE_EVENT_NOT_FOUND", status=404)

        photo, _ = PhotoAsset.objects.get_or_create(
            photo_id=photo_id,
            defaults={
                "event": event,
                "category": data["category"],
                "sha256": data["sha256"],
                "metadata_json": {
                    **(data.get("metadata") or {}),
                    "upload_session_id": f"UP{uuid.uuid4().hex[:16].upper()}",
                },
                "precheck_status": PhotoAsset.PRECHECK_PENDING,
                "review_status": PhotoAsset.REVIEW_PENDING,
                "immutable_status": PhotoAsset.IMMUTABLE_PENDING,
            },
        )
        return DetailResponse(data=serialize_photo(photo), msg="初始化照片上传成功")


class AppPhotoCompleteView(APIView):
    """Finalize a photo upload and lock immutable original/watermarked refs."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, photo_id):
        serializer = AppPhotoCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        try:
            photo = PhotoAsset.objects.select_for_update().get(photo_id=photo_id)
        except PhotoAsset.DoesNotExist:
            return ErrorResponse(msg="照片资产不存在", code="COFFEE_PHOTO_NOT_FOUND", status=404)

        if photo.sha256 != data["sha256"]:
            return ErrorResponse(msg="照片 Hash 不匹配", code="COFFEE_PHOTO_HASH_MISMATCH", status=409)

        chunk_count = data.get("chunk_count")
        chunk_hashes = data.get("chunk_hashes")
        if chunk_count is not None or chunk_hashes is not None:
            uploaded_chunks = list(photo.upload_chunks.order_by("chunk_index"))
            if len(uploaded_chunks) != chunk_count:
                return ErrorResponse(msg="照片分片未上传完整", code="COFFEE_PHOTO_CHUNKS_INCOMPLETE", status=409)
            uploaded_hashes = [item.chunk_hash for item in uploaded_chunks]
            if chunk_hashes is not None and uploaded_hashes != chunk_hashes:
                return ErrorResponse(msg="照片分片 Hash 不匹配", code="COFFEE_PHOTO_CHUNKS_MISMATCH", status=409)

        photo.original_file = data["original_file"]
        photo.watermarked_file = data.get("watermarked_file") or ""
        photo.precheck_status = data["precheck_status"]
        photo.immutable_status = PhotoAsset.IMMUTABLE_LOCKED
        photo.uploaded_at = timezone.now()
        photo.save(
            update_fields=[
                "original_file",
                "watermarked_file",
                "precheck_status",
                "immutable_status",
                "uploaded_at",
                "update_datetime",
            ]
        )
        return DetailResponse(data=serialize_photo(photo), msg="照片上传完成")


class AppPhotoChunkView(APIView):
    """Accept one idempotent photo chunk for resumable weak-network upload."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, photo_id, index):
        serializer = AppPhotoChunkSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        data = serializer.validated_data
        try:
            photo = PhotoAsset.objects.select_for_update().get(photo_id=photo_id)
        except PhotoAsset.DoesNotExist:
            return ErrorResponse(msg="照片资产不存在", code="COFFEE_PHOTO_NOT_FOUND", status=404)

        upload_session_id = photo.metadata_json.get("upload_session_id") if isinstance(photo.metadata_json, dict) else ""
        chunk, created = PhotoUploadChunk.objects.get_or_create(
            photo=photo,
            chunk_index=index,
            defaults={
                "upload_session_id": upload_session_id,
                "chunk_hash": data["chunk_hash"],
                "chunk_size": data["chunk_size"],
                "uploaded_at": timezone.now(),
            },
        )
        if not created and (chunk.chunk_hash != data["chunk_hash"] or chunk.chunk_size != data["chunk_size"]):
            return ErrorResponse(msg="分片重复上传内容不一致", code="COFFEE_PHOTO_CHUNK_CONFLICT", status=409)

        return DetailResponse(
            data={
                "photo_id": photo.photo_id,
                "upload_session_id": upload_session_id,
                "chunk_index": chunk.chunk_index,
                "chunk_hash": chunk.chunk_hash,
                "chunk_size": chunk.chunk_size,
                "uploaded_chunks": photo.upload_chunks.count(),
            },
            msg="照片分片上传成功",
        )


class AppEventOCRView(APIView):
    """Run OCR or accept a manual/mock OCR payload for one event photo."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, event_id):
        serializer = AppOCRStartSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        started = time.monotonic()
        data = serializer.validated_data
        try:
            event = CollectionEvent.objects.get(event_id=event_id)
            photo = PhotoAsset.objects.get(photo_id=data["photo_id"], event=event)
        except (CollectionEvent.DoesNotExist, PhotoAsset.DoesNotExist):
            return ErrorResponse(msg="采集事件或照片不存在", code="COFFEE_OCR_TARGET_NOT_FOUND", status=404)

        if data["provider"] == OCRResult.PROVIDER_MANUAL or data.get("structured_json") is not None or data.get("raw_response") is not None:
            provider_result = OCRProviderResult(
                status=OCRResult.STATUS_SUCCESS,
                raw_response=data.get("raw_response") or {},
                structured_json=data.get("structured_json") or {},
                confidence=data.get("confidence"),
            )
        else:
            provider_result = call_ocr_provider(provider_name=data["provider"], photo=photo)

        now = timezone.now()
        ocr_result = OCRResult.objects.create(
            ocr_result_id=f"OCR{uuid.uuid4().hex[:16].upper()}",
            photo=photo,
            provider=data["provider"],
            status=provider_result.status,
            raw_response_id=provider_result.raw_ref or f"RAW{uuid.uuid4().hex[:16].upper()}",
            raw_response_json=provider_result.raw_response,
            structured_json=provider_result.structured_json,
            confidence=provider_result.confidence,
            started_at=now,
            finished_at=timezone.now(),
            error_code=provider_result.error_code,
            error_message=provider_result.error_message,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        ProviderCallLog.objects.create(
            provider_type="ocr",
            provider_name=data["provider"],
            request_id=ocr_result.ocr_result_id,
            target_type="photo",
            target_id=photo.photo_id,
            status=ProviderCallLog.STATUS_SUCCESS if provider_result.status == OCRResult.STATUS_SUCCESS else ProviderCallLog.STATUS_FAILED,
            latency_ms=latency_ms,
            request_digest=_digest({"photo_id": photo.photo_id, "provider": data["provider"]}),
            response_digest=_digest(provider_result.structured_json),
            raw_response_ref=ocr_result.raw_response_id,
            error_code=provider_result.error_code,
            called_at=now,
        )
        return DetailResponse(data=serialize_ocr_result(ocr_result), msg="OCR 识别完成")


class AppEventOCRResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        results = OCRResult.objects.filter(photo__event__event_id=event_id).prefetch_related("corrections", "photo").order_by("create_datetime", "id")
        return DetailResponse(data=[serialize_ocr_result(item) for item in results], msg="获取 OCR 结果成功")


class AppOCRCorrectionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, ocr_result_id):
        serializer = AppOCRCorrectionSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        try:
            ocr_result = OCRResult.objects.get(ocr_result_id=ocr_result_id)
        except OCRResult.DoesNotExist:
            return ErrorResponse(msg="OCR 结果不存在", code="COFFEE_OCR_RESULT_NOT_FOUND", status=404)

        data = serializer.validated_data
        latest = OCRCorrection.objects.filter(
            ocr_result=ocr_result,
            field_name=data["field_name"],
        ).order_by("-version").first()
        correction = OCRCorrection.objects.create(
            ocr_result=ocr_result,
            field_name=data["field_name"],
            raw_value=data.get("raw_value"),
            corrected_value=data["corrected_value"],
            reason=data.get("reason"),
            version=(latest.version + 1) if latest else 1,
            corrected_by=_collector_id(request),
            corrected_at=timezone.now(),
        )
        return DetailResponse(data=serialize_ocr_correction(correction), msg="保存 OCR 校正成功")


class WebEventDetailView(APIView):
    """Return the Web detail page aggregate for plot, photos, OCR and reviews."""

    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            event = (
                _apply_event_data_scope(CollectionEvent.objects.select_related("plot", "point"), request.user)
                .prefetch_related("field_values", "measurements", "photos__ocr_results__corrections", "photos__annotations")
                .get(event_id=event_id)
            )
        except CollectionEvent.DoesNotExist:
            return ErrorResponse(msg="采集事件不存在", code="COFFEE_EVENT_NOT_FOUND", status=404)

        photo_ids = list(event.photos.values_list("photo_id", flat=True))
        provider_logs = ProviderCallLog.objects.filter(target_type="photo", target_id__in=photo_ids).order_by("called_at", "id")
        return DetailResponse(data=serialize_event_detail(event, provider_logs), msg="获取采集事件详情成功")


class WebEventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = CollectionEvent.objects.select_related("plot", "point").prefetch_related("photos__ocr_results", "quality_reviews").order_by("-create_datetime", "-id")
        queryset = _apply_event_data_scope(queryset, request.user)
        status = request.query_params.get("status")
        task_id = request.query_params.get("task_id")
        plot_id = request.query_params.get("plot_id")
        point_id = request.query_params.get("point_id")
        if status:
            queryset = queryset.filter(status=status)
        if task_id:
            queryset = queryset.filter(task_code=task_id)
        if plot_id:
            queryset = queryset.filter(plot__plot_id=plot_id)
        if point_id:
            queryset = queryset.filter(point__point_id=point_id)
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_event_list_item(item) for item in queryset],
            },
            msg="获取采集事件列表成功",
        )


class WebPhotoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = PhotoAsset.objects.select_related("event", "event__plot", "event__point").prefetch_related("ocr_results", "upload_chunks").order_by("-create_datetime", "-id")
        scoped_event_ids = _apply_event_data_scope(CollectionEvent.objects.all(), request.user).values("id")
        queryset = queryset.filter(event_id__in=scoped_event_ids)
        review_status = request.query_params.get("review_status")
        event_id = request.query_params.get("event_id")
        category = request.query_params.get("category")
        if review_status:
            queryset = queryset.filter(review_status=review_status)
        if event_id:
            queryset = queryset.filter(event__event_id=event_id)
        if category:
            queryset = queryset.filter(category=category)
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_photo_list_item(item) for item in queryset],
            },
            msg="获取照片资产列表成功",
        )


class WebPhotoReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, photo_id):
        serializer = PhotoReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        try:
            photo = PhotoAsset.objects.select_for_update().select_related("event").get(photo_id=photo_id)
        except PhotoAsset.DoesNotExist:
            return ErrorResponse(msg="照片资产不存在", code="COFFEE_PHOTO_NOT_FOUND", status=404)

        data = serializer.validated_data
        status = QualityReview.STATUS_APPROVED if data["status"] == PhotoAsset.REVIEW_APPROVED else QualityReview.STATUS_RETURNED
        review = _create_photo_review(
            photo,
            status=status,
            reviewer_id=_reviewer_id(request),
            result_json={"review_note": data.get("review_note") or ""},
            return_reason=data.get("return_reason"),
            return_items=data.get("return_items") or [],
        )
        return DetailResponse(data={"photo": serialize_photo(photo), "review": serialize_quality_review(review)}, msg="照片审核完成")


class WebPhotoAnnotationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_scoped_photo(self, request, photo_id, for_update=False):
        scoped_event_ids = _apply_event_data_scope(CollectionEvent.objects.all(), request.user).values("id")
        queryset = PhotoAsset.objects.select_related("event").filter(event_id__in=scoped_event_ids)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.get(photo_id=photo_id)

    def get(self, request, photo_id):
        try:
            photo = self._get_scoped_photo(request, photo_id)
        except PhotoAsset.DoesNotExist:
            return ErrorResponse(msg="照片资产不存在", code="COFFEE_PHOTO_NOT_FOUND", status=404)

        annotations = photo.annotations.order_by("annotation_id", "version", "id")
        return DetailResponse(
            data={
                "count": annotations.count(),
                "results": [serialize_photo_annotation(item) for item in annotations],
            },
            msg="获取照片标注版本成功",
        )

    @transaction.atomic
    def post(self, request, photo_id):
        serializer = PhotoAnnotationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        try:
            photo = self._get_scoped_photo(request, photo_id, for_update=True)
        except PhotoAsset.DoesNotExist:
            return ErrorResponse(msg="照片资产不存在", code="COFFEE_PHOTO_NOT_FOUND", status=404)

        data = serializer.validated_data
        annotation_id = data.get("annotation_id") or f"AN{uuid.uuid4().hex[:16].upper()}"
        latest = PhotoAnnotation.objects.filter(photo=photo, annotation_id=annotation_id).order_by("-version", "-id").first()
        next_version = (latest.version + 1) if latest else 1
        PhotoAnnotation.objects.filter(photo=photo, annotation_id=annotation_id, is_latest=True).update(is_latest=False)
        annotation = PhotoAnnotation.objects.create(
            annotation_id=annotation_id,
            photo=photo,
            label=data["label"],
            shape_type=data["shape_type"],
            geometry_json=data["geometry"],
            version=next_version,
            is_latest=True,
            source=PhotoAnnotation.SOURCE_MANUAL,
            annotated_by=_reviewer_id(request),
            note=data.get("note"),
        )
        return DetailResponse(data=serialize_photo_annotation(annotation), msg="保存照片标注版本成功")


class WebOCRJobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = OCRResult.objects.select_related("photo", "photo__event", "photo__event__plot", "photo__event__point").prefetch_related("corrections").order_by("-create_datetime", "-id")
        scoped_event_ids = _apply_event_data_scope(CollectionEvent.objects.all(), request.user).values("id")
        queryset = queryset.filter(photo__event_id__in=scoped_event_ids)
        status = request.query_params.get("status")
        provider = request.query_params.get("provider")
        photo_id = request.query_params.get("photo_id")
        event_id = request.query_params.get("event_id")
        if status:
            queryset = queryset.filter(status=status)
        if provider:
            queryset = queryset.filter(provider=provider)
        if photo_id:
            queryset = queryset.filter(photo__photo_id=photo_id)
        if event_id:
            queryset = queryset.filter(photo__event__event_id=event_id)
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_ocr_job_item(item) for item in queryset],
            },
            msg="获取 OCR 任务列表成功",
        )


class WebOCRCorrectionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, ocr_result_id):
        serializer = AppOCRCorrectionSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)

        try:
            ocr_result = OCRResult.objects.get(ocr_result_id=ocr_result_id)
        except OCRResult.DoesNotExist:
            return ErrorResponse(msg="OCR 结果不存在", code="COFFEE_OCR_RESULT_NOT_FOUND", status=404)

        data = serializer.validated_data
        latest = OCRCorrection.objects.filter(
            ocr_result=ocr_result,
            field_name=data["field_name"],
        ).order_by("-version").first()
        correction = OCRCorrection.objects.create(
            ocr_result=ocr_result,
            field_name=data["field_name"],
            raw_value=data.get("raw_value"),
            corrected_value=data["corrected_value"],
            reason=data.get("reason"),
            version=(latest.version + 1) if latest else 1,
            corrected_by=_reviewer_id(request),
            corrected_at=timezone.now(),
        )
        return DetailResponse(data=serialize_ocr_correction(correction), msg="保存 Web OCR 校正成功")


class WebProviderConfigListCreateView(APIView):
    """List and create Provider configs, masking secrets in responses."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ProviderConfig.objects.order_by("provider_type", "priority", "-version", "-id")
        provider_type = request.query_params.get("provider_type")
        enabled = request.query_params.get("enabled")
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        if enabled in ("true", "false"):
            queryset = queryset.filter(enabled=(enabled == "true"))
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_provider_config(item) for item in queryset],
            },
            msg="获取 Provider 配置成功",
        )

    @transaction.atomic
    def post(self, request):
        serializer = ProviderConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        config_status = ProviderConfig.STATUS_CONFIGURED if data.get("config_json") else ProviderConfig.STATUS_MISSING
        config = ProviderConfig.objects.create(
            provider_type=data["provider_type"],
            provider_name=data["provider_name"],
            display_name=data["display_name"],
            enabled=data.get("enabled", False),
            priority=data.get("priority", 100),
            timeout_ms=data.get("timeout_ms", 15000),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 60),
            config_status=config_status,
            config_json=data.get("config_json") or {},
            secret_fields=data.get("secret_fields") or [],
            version=1,
        )
        return DetailResponse(data=serialize_provider_config(config), msg="创建 Provider 配置成功")


class WebProviderConfigTestView(APIView):
    """Run a safe local Provider contract test and audit the result."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, provider_id):
        try:
            config = ProviderConfig.objects.select_for_update().get(id=provider_id)
        except ProviderConfig.DoesNotExist:
            return ErrorResponse(msg="Provider 配置不存在", code="COFFEE_PROVIDER_CONFIG_NOT_FOUND", status=404)

        contract = provider_local_contract(config) if config.enabled else {
            "provider_type": config.provider_type,
            "provider_name": config.provider_name,
            "status": ProviderCallLog.STATUS_FAILED,
            "error_code": "PROVIDER_NOT_ENABLED",
            "local_contract_only": True,
            "capabilities": [],
        }
        status = ProviderCallLog.STATUS_SUCCESS if contract["status"] == "success" else ProviderCallLog.STATUS_FAILED
        error_code = contract.get("error_code")
        request_id = f"PC{uuid.uuid4().hex[:16].upper()}"
        ProviderCallLog.objects.create(
            provider_type=config.provider_type,
            provider_name=config.provider_name,
            request_id=request_id,
            target_type="provider_config",
            target_id=str(config.id),
            status=status,
            latency_ms=0,
            request_digest=_digest({"provider_id": config.id, "provider_name": config.provider_name}),
            response_digest=_digest(contract),
            raw_response_ref="local-contract-test",
            error_code=error_code,
            called_at=timezone.now(),
        )
        if status == ProviderCallLog.STATUS_SUCCESS:
            config.config_status = ProviderConfig.STATUS_TESTED
            config.save(update_fields=["config_status", "update_datetime"])
        return DetailResponse(
            data={
                "provider_id": config.id,
                **contract,
            },
            msg="Provider 本地连接测试完成",
        )


class WebProviderConfigDetailView(APIView):
    """Update, toggle and delete provider configs from the Web form dialog."""

    permission_classes = [IsAuthenticated]

    def _get_config(self, provider_id):
        try:
            return ProviderConfig.objects.get(id=provider_id)
        except ProviderConfig.DoesNotExist:
            return None

    @transaction.atomic
    def put(self, request, provider_id):
        config = self._get_config(provider_id)
        if config is None:
            return ErrorResponse(msg="Provider 配置不存在", code="COFFEE_PROVIDER_CONFIG_NOT_FOUND", status=404)
        serializer = ProviderConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        config.provider_type = data["provider_type"]
        config.provider_name = data["provider_name"]
        config.display_name = data["display_name"]
        config.enabled = data.get("enabled", False)
        config.priority = data.get("priority", 100)
        config.timeout_ms = data.get("timeout_ms", 15000)
        config.rate_limit_per_minute = data.get("rate_limit_per_minute", 60)
        config.config_json = data.get("config_json") or {}
        config.secret_fields = data.get("secret_fields") or []
        config.config_status = ProviderConfig.STATUS_CONFIGURED if config.config_json else ProviderConfig.STATUS_MISSING
        config.version = config.version + 1
        config.save()
        return DetailResponse(data=serialize_provider_config(config), msg="更新 Provider 配置成功")

    @transaction.atomic
    def post(self, request, provider_id):
        config = self._get_config(provider_id)
        if config is None:
            return ErrorResponse(msg="Provider 配置不存在", code="COFFEE_PROVIDER_CONFIG_NOT_FOUND", status=404)
        config.enabled = bool(request.data.get("enabled"))
        config.save(update_fields=["enabled", "update_datetime"])
        return DetailResponse(data=serialize_provider_config(config), msg="更新 Provider 启用状态成功")

    @transaction.atomic
    def delete(self, request, provider_id):
        config = self._get_config(provider_id)
        if config is None:
            return ErrorResponse(msg="Provider 配置不存在", code="COFFEE_PROVIDER_CONFIG_NOT_FOUND", status=404)
        config.delete()
        return DetailResponse(data={"provider_id": provider_id}, msg="删除 Provider 配置成功")


class WebMetricDefinitionListCreateView(APIView):
    """Manage versioned metric definitions used by statistics endpoints."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = MetricDefinition.objects.order_by("metric_group", "metric_code", "-version", "-id")
        metric_group = request.query_params.get("metric_group")
        enabled = request.query_params.get("enabled")
        if metric_group:
            queryset = queryset.filter(metric_group=metric_group)
        if enabled in {"true", "false"}:
            queryset = queryset.filter(enabled=enabled == "true")
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_metric_definition(item) for item in queryset],
            },
            msg="获取统计口径配置成功",
        )

    @transaction.atomic
    def post(self, request):
        serializer = MetricDefinitionSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        latest_version = (
            MetricDefinition.objects.filter(metric_code=data["metric_code"])
            .order_by("-version", "-id")
            .values_list("version", flat=True)
            .first()
        )
        metric = MetricDefinition.objects.create(
            **data,
            version=(latest_version or 0) + 1,
            creator=request.user,
            dept_belong_id=str(request.user.dept_id) if getattr(request.user, "dept_id", None) else None,
        )
        return DetailResponse(data=serialize_metric_definition(metric), msg="保存统计口径配置成功")


class WebStatisticsProgressView(APIView):
    """Return collection progress metrics within the current user's data scope."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = _apply_event_data_scope(CollectionEvent.objects.all(), request.user)
        return DetailResponse(
            data={
                "total_events": events.count(),
                "total_plots": Plot.objects.filter(events__in=events).distinct().count(),
                "total_points": Point.objects.filter(events__in=events).distinct().count(),
                "status_counts": _counts_by(events, "status"),
                "submitted_or_done": events.filter(status__in=[CollectionEvent.STATUS_SUBMITTED, CollectionEvent.STATUS_APPROVED, CollectionEvent.STATUS_RETURNED]).count(),
                "metric_definitions": [serialize_metric_definition(item) for item in _latest_metric_definitions(MetricDefinition.GROUP_PROGRESS)],
            },
            msg="获取采集进度统计成功",
        )


class WebStatisticsQualityView(APIView):
    """Return photo/review quality metrics within the current user's data scope."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = _apply_event_data_scope(CollectionEvent.objects.all(), request.user)
        photos = PhotoAsset.objects.filter(event__in=events)
        reviews = QualityReview.objects.filter(event__in=events)
        return DetailResponse(
            data={
                "photo_review_counts": _counts_by(photos, "review_status"),
                "precheck_counts": _counts_by(photos, "precheck_status"),
                "quality_review_counts": _counts_by(reviews, "status"),
                "return_reason_counts": _counts_by(reviews.exclude(return_reason__isnull=True).exclude(return_reason=""), "return_reason"),
                "metric_definitions": [serialize_metric_definition(item) for item in _latest_metric_definitions(MetricDefinition.GROUP_QUALITY)],
            },
            msg="获取质量统计成功",
        )


class WebStatisticsPerformanceView(APIView):
    """Return collector performance metrics for Web reporting."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = []
        scoped_events = _apply_event_data_scope(CollectionEvent.objects.all(), request.user)
        collector_ids = (
            scoped_events.exclude(collector_id__isnull=True)
            .exclude(collector_id="")
            .values_list("collector_id", flat=True)
            .distinct()
            .order_by("collector_id")
        )
        for collector_id in collector_ids:
            events = scoped_events.filter(collector_id=collector_id)
            event_count = events.count()
            approved_count = events.filter(status=CollectionEvent.STATUS_APPROVED).count()
            returned_count = events.filter(status=CollectionEvent.STATUS_RETURNED).count()
            rows.append(
                {
                    "collector_id": collector_id,
                    "event_count": event_count,
                    "approved_count": approved_count,
                    "returned_count": returned_count,
                    "approval_rate": round(approved_count / event_count, 4) if event_count else 0,
                    "return_rate": round(returned_count / event_count, 4) if event_count else 0,
                }
            )
        rows.sort(key=lambda item: (-item["event_count"], item["collector_id"]))
        return DetailResponse(
            data={
                "collectors": rows,
                "metric_definitions": [serialize_metric_definition(item) for item in _latest_metric_definitions(MetricDefinition.GROUP_PERFORMANCE)],
            },
            msg="获取绩效统计成功",
        )


class WebExportJobListCreateView(APIView):
    """Create and list export jobs; dataset packages enqueue Celery work."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = _apply_dept_data_scope(ExportJob.objects.order_by("-create_datetime", "-id"), request.user)
        status = request.query_params.get("status")
        export_type = request.query_params.get("export_type")
        if status:
            queryset = queryset.filter(status=status)
        if export_type:
            queryset = queryset.filter(export_type=export_type)
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_export_job(item) for item in queryset],
            },
            msg="获取导出任务成功",
        )

    @transaction.atomic
    def post(self, request):
        serializer = ExportJobCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        job = ExportJob.objects.create(
            job_code=f"EX{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}",
            export_type=data["export_type"],
            filters_json=data.get("filters") or {},
            status=ExportJob.STATUS_QUEUED,
            progress=0,
            created_by=_reviewer_id(request),
            dept_belong_id=str(request.user.dept_id) if getattr(request.user, "dept_id", None) else None,
        )
        if job.export_type == ExportJob.TYPE_DATASET_PACKAGE:
            transaction.on_commit(lambda: run_export_job.delay(job.job_code))
        return DetailResponse(data=serialize_export_job(job), msg="创建导出任务成功")


class WebExportJobCancelView(APIView):
    """Cancel queued/running export jobs before they reach a terminal state."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, job_code):
        try:
            job = ExportJob.objects.select_for_update().get(job_code=job_code)
        except ExportJob.DoesNotExist:
            return ErrorResponse(msg="导出任务不存在", code="COFFEE_EXPORT_JOB_NOT_FOUND", status=404)
        if job.status in [ExportJob.STATUS_SUCCESS, ExportJob.STATUS_FAILED, ExportJob.STATUS_EXPIRED]:
            return ErrorResponse(msg="当前导出任务状态不可取消", code="COFFEE_EXPORT_JOB_NOT_CANCELABLE", status=409)
        job.status = ExportJob.STATUS_CANCELLED
        job.save(update_fields=["status", "update_datetime"])
        return DetailResponse(data=serialize_export_job(job), msg="取消导出任务成功")


class WebBGradeRuleListCreateView(APIView):
    """Manage B-grade count rules used by quality checks."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = BGradeRule.objects.order_by("task_code", "rule_name", "-version", "-id")
        task_id = request.query_params.get("task_id")
        enabled = request.query_params.get("enabled")
        if task_id:
            queryset = queryset.filter(task_code=task_id)
        if enabled in ("true", "false"):
            queryset = queryset.filter(enabled=(enabled == "true"))
        return DetailResponse(
            data={
                "count": queryset.count(),
                "results": [serialize_b_grade_rule(item) for item in queryset],
            },
            msg="获取 B 级规则成功",
        )

    @transaction.atomic
    def post(self, request):
        serializer = BGradeRuleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        rule = BGradeRule.objects.create(
            rule_code=f"BG{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}",
            rule_name=data["rule_name"],
            task_code=data["task_code"],
            metric=data["metric"],
            min_count=data.get("min_count"),
            max_count=data.get("max_count"),
            block_level=data.get("block_level") or BGradeRule.LEVEL_BLOCKING,
            enabled=data.get("enabled", True),
            version=1,
        )
        return DetailResponse(data=serialize_b_grade_rule(rule), msg="创建 B 级规则成功")


class WebBGradeRuleCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, rule_code):
        try:
            rule = BGradeRule.objects.get(rule_code=rule_code)
        except BGradeRule.DoesNotExist:
            return ErrorResponse(msg="B 级规则不存在", code="COFFEE_B_GRADE_RULE_NOT_FOUND", status=404)
        return DetailResponse(data=_check_b_grade_rule(rule), msg="B 级规则检查完成")


class WebBGradeRuleDetailView(APIView):
    """Update, toggle and delete B-grade rules from the Web rule dialog."""

    permission_classes = [IsAuthenticated]

    def _get_rule(self, rule_code):
        try:
            return BGradeRule.objects.get(rule_code=rule_code)
        except BGradeRule.DoesNotExist:
            return None

    @transaction.atomic
    def put(self, request, rule_code):
        rule = self._get_rule(rule_code)
        if rule is None:
            return ErrorResponse(msg="B 级规则不存在", code="COFFEE_B_GRADE_RULE_NOT_FOUND", status=404)
        serializer = BGradeRuleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        rule.rule_name = data["rule_name"]
        rule.task_code = data["task_code"]
        rule.metric = data["metric"]
        rule.min_count = data.get("min_count")
        rule.max_count = data.get("max_count")
        rule.block_level = data.get("block_level") or BGradeRule.LEVEL_BLOCKING
        rule.enabled = data.get("enabled", True)
        rule.version = rule.version + 1
        rule.save()
        return DetailResponse(data=serialize_b_grade_rule(rule), msg="更新 B 级规则成功")

    @transaction.atomic
    def post(self, request, rule_code):
        rule = self._get_rule(rule_code)
        if rule is None:
            return ErrorResponse(msg="B 级规则不存在", code="COFFEE_B_GRADE_RULE_NOT_FOUND", status=404)
        rule.enabled = bool(request.data.get("enabled"))
        rule.save(update_fields=["enabled", "update_datetime"])
        return DetailResponse(data=serialize_b_grade_rule(rule), msg="更新 B 级规则启用状态成功")

    @transaction.atomic
    def delete(self, request, rule_code):
        rule = self._get_rule(rule_code)
        if rule is None:
            return ErrorResponse(msg="B 级规则不存在", code="COFFEE_B_GRADE_RULE_NOT_FOUND", status=404)
        rule.delete()
        return DetailResponse(data={"rule_code": rule_code}, msg="删除 B 级规则成功")


class WebEventReviewApproveView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, event_id):
        serializer = ReviewApproveSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        try:
            event = CollectionEvent.objects.select_for_update().get(event_id=event_id)
        except CollectionEvent.DoesNotExist:
            return ErrorResponse(msg="采集事件不存在", code="COFFEE_EVENT_NOT_FOUND", status=404)
        review = _create_review(
            event,
            status=QualityReview.STATUS_APPROVED,
            reviewer_id=_reviewer_id(request),
            result_json={"review_note": serializer.validated_data.get("review_note") or ""},
        )
        return DetailResponse(data={"event": serialize_event(event), "review": serialize_quality_review(review)}, msg="审核通过")


class WebEventReviewReturnView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, event_id):
        serializer = ReviewReturnSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        try:
            event = CollectionEvent.objects.select_for_update().get(event_id=event_id)
        except CollectionEvent.DoesNotExist:
            return ErrorResponse(msg="采集事件不存在", code="COFFEE_EVENT_NOT_FOUND", status=404)
        data = serializer.validated_data
        review = _create_review(
            event,
            status=QualityReview.STATUS_RETURNED,
            reviewer_id=_reviewer_id(request),
            result_json={"return_note": data.get("return_note") or ""},
            return_reason=data["return_reason"],
            return_items=data["return_items"],
        )
        return DetailResponse(data={"event": serialize_event(event), "review": serialize_quality_review(review)}, msg="审核退回")


class WebEventBulkApproveView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = BulkApproveSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        event_ids = serializer.validated_data["event_ids"]
        events = {event.event_id: event for event in CollectionEvent.objects.select_for_update().filter(event_id__in=event_ids)}
        success = []
        failed = []
        for event_id in event_ids:
            event = events.get(event_id)
            if not event:
                failed.append({"event_id": event_id, "reason": "not_found"})
                continue
            _create_review(
                event,
                status=QualityReview.STATUS_APPROVED,
                reviewer_id=_reviewer_id(request),
                result_json={"review_note": serializer.validated_data.get("review_note") or ""},
            )
            success.append(event_id)
        return DetailResponse(data={"success": success, "failed": failed, "skipped": []}, msg="批量审核通过")


class WebEventBulkReturnView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = BulkReturnSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error(serializer)
        data = serializer.validated_data
        events = {event.event_id: event for event in CollectionEvent.objects.select_for_update().filter(event_id__in=data["event_ids"])}
        success = []
        failed = []
        for event_id in data["event_ids"]:
            event = events.get(event_id)
            if not event:
                failed.append({"event_id": event_id, "reason": "not_found"})
                continue
            _create_review(
                event,
                status=QualityReview.STATUS_RETURNED,
                reviewer_id=_reviewer_id(request),
                result_json={"return_note": data.get("return_note") or ""},
                return_reason=data["return_reason"],
                return_items=data["return_items"],
            )
            success.append(event_id)
        return DetailResponse(data={"success": success, "failed": failed, "skipped": []}, msg="批量审核退回")
