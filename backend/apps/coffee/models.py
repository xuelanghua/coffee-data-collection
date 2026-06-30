from django.db import models

from dvadmin.utils.models import CoreModel, table_prefix


class Plot(CoreModel):
    SOURCE_APP_DRAWN = "app_drawn"
    SOURCE_WEB_CREATED = "web_created"
    SOURCE_IMPORTED = "imported"
    SOURCE_CHOICES = (
        (SOURCE_APP_DRAWN, "App现场圈选"),
        (SOURCE_WEB_CREATED, "Web创建"),
        (SOURCE_IMPORTED, "导入"),
    )

    REVIEW_PENDING = "pending_review"
    REVIEW_CONFIRMED = "confirmed"
    REVIEW_RETURNED = "returned"
    REVIEW_ADJUSTED = "adjusted"
    REVIEW_CHOICES = (
        (REVIEW_PENDING, "待复核"),
        (REVIEW_CONFIRMED, "已确认"),
        (REVIEW_RETURNED, "退回重圈"),
        (REVIEW_ADJUSTED, "已调整"),
    )

    AREA_NOT_CHECKED = "not_checked"
    AREA_MATCHED = "matched"
    AREA_MISMATCH = "mismatch"
    AREA_ADJUSTED = "adjusted"
    AREA_CHECK_CHOICES = (
        (AREA_NOT_CHECKED, "未复核"),
        (AREA_MATCHED, "一致"),
        (AREA_MISMATCH, "不一致"),
        (AREA_ADJUSTED, "已调整"),
    )

    COORD_GCJ02 = "gcj02"
    COORD_WGS84 = "wgs84"
    COORD_CHOICES = (
        (COORD_GCJ02, "GCJ-02"),
        (COORD_WGS84, "WGS-84"),
    )

    AREA_GEODESIC = "geodesic"
    AREA_PROJECTED = "projected"
    AREA_METHOD_CHOICES = (
        (AREA_GEODESIC, "椭球面积"),
        (AREA_PROJECTED, "投影面积"),
    )

    plot_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="Plot_ID")
    task_code = models.CharField(max_length=64, db_index=True, verbose_name="任务编号")
    name = models.CharField(max_length=128, verbose_name="地块名称")
    admin_region = models.CharField(max_length=255, null=True, blank=True, verbose_name="行政区")
    boundary_geojson = models.JSONField(default=dict, verbose_name="边界GeoJSON")
    area_mu = models.DecimalField(max_digits=12, decimal_places=4, verbose_name="面积(亩)")
    area_calc_method = models.CharField(max_length=32, choices=AREA_METHOD_CHOICES, default=AREA_GEODESIC, verbose_name="面积计算方法")
    coordinate_system = models.CharField(max_length=16, choices=COORD_CHOICES, default=COORD_GCJ02, verbose_name="坐标系")
    source_type = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_APP_DRAWN, verbose_name="来源")
    created_in_field = models.BooleanField(default=True, verbose_name="现场创建")
    collector_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="采集员ID")
    area_check_status = models.CharField(max_length=32, choices=AREA_CHECK_CHOICES, default=AREA_NOT_CHECKED, verbose_name="面积复核状态")
    review_status = models.CharField(max_length=32, choices=REVIEW_CHOICES, default=REVIEW_PENDING, verbose_name="复核状态")
    reviewed_by = models.CharField(max_length=64, null=True, blank=True, verbose_name="复核人")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="复核时间")
    status = models.CharField(max_length=32, default="active", verbose_name="状态")

    class Meta:
        db_table = table_prefix + "coffee_plot"
        verbose_name = "咖啡地块"
        verbose_name_plural = verbose_name


class PlotBoundaryVersion(CoreModel):
    plot = models.ForeignKey(Plot, related_name="boundary_versions", on_delete=models.CASCADE, verbose_name="地块")
    version = models.PositiveIntegerField(verbose_name="版本")
    boundary_geojson = models.JSONField(default=dict, verbose_name="边界GeoJSON")
    area_mu = models.DecimalField(max_digits=12, decimal_places=4, verbose_name="面积(亩)")
    area_calc_method = models.CharField(max_length=32, choices=Plot.AREA_METHOD_CHOICES, default=Plot.AREA_GEODESIC, verbose_name="面积计算方法")
    coordinate_system = models.CharField(max_length=16, choices=Plot.COORD_CHOICES, default=Plot.COORD_GCJ02, verbose_name="坐标系")
    source_type = models.CharField(max_length=32, choices=Plot.SOURCE_CHOICES, default=Plot.SOURCE_APP_DRAWN, verbose_name="来源")
    review_note = models.CharField(max_length=255, null=True, blank=True, verbose_name="复核说明")

    class Meta:
        db_table = table_prefix + "coffee_plot_boundary_version"
        verbose_name = "咖啡地块边界版本"
        verbose_name_plural = verbose_name
        unique_together = (("plot", "version"),)


class Point(CoreModel):
    SOURCE_APP_SELECTED = "app_selected"
    SOURCE_WEB_CREATED = "web_created"
    SOURCE_IMPORTED = "imported"
    SOURCE_CHOICES = (
        (SOURCE_APP_SELECTED, "App现场点选"),
        (SOURCE_WEB_CREATED, "Web创建"),
        (SOURCE_IMPORTED, "导入"),
    )

    COORD_GCJ02 = Plot.COORD_GCJ02
    COORD_WGS84 = Plot.COORD_WGS84
    COORD_CHOICES = Plot.COORD_CHOICES

    REVIEW_PENDING = Plot.REVIEW_PENDING
    REVIEW_CONFIRMED = Plot.REVIEW_CONFIRMED
    REVIEW_RETURNED = Plot.REVIEW_RETURNED
    REVIEW_ADJUSTED = Plot.REVIEW_ADJUSTED
    REVIEW_CHOICES = Plot.REVIEW_CHOICES

    point_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="Point_ID")
    task_code = models.CharField(max_length=64, db_index=True, verbose_name="任务编号")
    plot = models.ForeignKey(Plot, related_name="points", on_delete=models.PROTECT, verbose_name="地块")
    longitude = models.DecimalField(max_digits=12, decimal_places=8, verbose_name="经度")
    latitude = models.DecimalField(max_digits=12, decimal_places=8, verbose_name="纬度")
    altitude = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="海拔")
    coordinate_system = models.CharField(max_length=16, choices=COORD_CHOICES, default=COORD_GCJ02, verbose_name="坐标系")
    source_type = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_APP_SELECTED, verbose_name="来源")
    created_in_field = models.BooleanField(default=True, verbose_name="现场创建")
    collector_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="采集员ID")
    review_status = models.CharField(max_length=32, choices=REVIEW_CHOICES, default=REVIEW_PENDING, verbose_name="复核状态")
    status = models.CharField(max_length=32, default="active", verbose_name="状态")

    class Meta:
        db_table = table_prefix + "coffee_point"
        verbose_name = "咖啡采集点"
        verbose_name_plural = verbose_name


class CollectionEvent(CoreModel):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_REVIEWING = "reviewing"
    STATUS_APPROVED = "approved"
    STATUS_RETURNED = "returned"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "草稿"),
        (STATUS_SUBMITTED, "已提交"),
        (STATUS_REVIEWING, "审核中"),
        (STATUS_APPROVED, "通过"),
        (STATUS_RETURNED, "退回"),
    )

    event_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="Event_ID")
    task_code = models.CharField(max_length=64, db_index=True, verbose_name="任务编号")
    plot = models.ForeignKey(Plot, related_name="events", on_delete=models.PROTECT, verbose_name="地块")
    point = models.ForeignKey(Point, related_name="events", on_delete=models.PROTECT, verbose_name="采集点")
    collector_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="采集员ID")
    idempotency_key = models.CharField(max_length=128, unique=True, verbose_name="幂等键")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name="状态")
    collected_at = models.DateTimeField(null=True, blank=True, verbose_name="采集时间")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="提交时间")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")
    manifest_hash = models.CharField(max_length=128, verbose_name="Manifest Hash")
    location_snapshot = models.JSONField(default=dict, blank=True, verbose_name="定位快照")
    weather_snapshot = models.JSONField(default=dict, blank=True, verbose_name="天气快照")

    class Meta:
        db_table = table_prefix + "coffee_collection_event"
        verbose_name = "咖啡采集事件"
        verbose_name_plural = verbose_name


class MeasurementRecord(CoreModel):
    event = models.ForeignKey(CollectionEvent, related_name="measurements", on_delete=models.CASCADE, verbose_name="采集事件")
    device_no = models.CharField(max_length=64, verbose_name="设备编号")
    measured_at = models.DateTimeField(null=True, blank=True, verbose_name="采集时间")
    wind_speed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="风速")
    wind_direction = models.CharField(max_length=32, null=True, blank=True, verbose_name="风向")
    air_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="空气温度")
    air_humidity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="空气湿度")
    atmospheric_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="大气压力")
    rainfall = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="雨量")
    soil_moisture = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="土壤湿度")
    soil_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="土壤温度")
    soil_salinity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="土壤盐分")
    soil_ph = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="土壤PH值")
    source_photo_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="来源Photo_ID")
    ocr_result_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="OCR结果ID")
    is_abnormal = models.BooleanField(default=False, verbose_name="异常")
    retake_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="复测原记录")
    remark = models.CharField(max_length=255, null=True, blank=True, verbose_name="备注")

    class Meta:
        db_table = table_prefix + "coffee_measurement_record"
        verbose_name = "咖啡设备采集数据"
        verbose_name_plural = verbose_name


class EventFieldValue(CoreModel):
    SOURCE_MANUAL = "manual"
    SOURCE_OCR = "ocr"
    SOURCE_DEVICE = "device"
    SOURCE_SYSTEM = "system"
    SOURCE_CHOICES = (
        (SOURCE_MANUAL, "人工输入"),
        (SOURCE_OCR, "OCR回填"),
        (SOURCE_DEVICE, "设备采集"),
        (SOURCE_SYSTEM, "系统生成"),
    )

    event = models.ForeignKey(CollectionEvent, related_name="field_values", on_delete=models.CASCADE, verbose_name="采集事件")
    field_code = models.CharField(max_length=64, verbose_name="字段编码")
    field_label = models.CharField(max_length=64, verbose_name="字段名称")
    value_text = models.CharField(max_length=255, null=True, blank=True, verbose_name="文本值")
    value_number = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, verbose_name="数值")
    value_json = models.JSONField(default=dict, blank=True, verbose_name="JSON值")
    unit = models.CharField(max_length=32, null=True, blank=True, verbose_name="单位")
    source_type = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_MANUAL, verbose_name="来源")
    source_photo_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="来源Photo_ID")
    ocr_result_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="OCR结果ID")
    ocr_raw_value = models.CharField(max_length=255, null=True, blank=True, verbose_name="OCR原值")
    ocr_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, verbose_name="OCR置信度")
    corrected_from = models.CharField(max_length=255, null=True, blank=True, verbose_name="修正前值")
    correction_reason = models.CharField(max_length=255, null=True, blank=True, verbose_name="修正原因")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")

    class Meta:
        db_table = table_prefix + "coffee_event_field_value"
        verbose_name = "咖啡采集字段值"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["event", "field_code", "version"]),
            models.Index(fields=["event", "source_type"]),
        ]


class PhotoAsset(CoreModel):
    CATEGORY_DEVICE_READING = "device_reading"
    CATEGORY_ENVIRONMENT = "environment"
    CATEGORY_PLANT = "plant"
    CATEGORY_FRUIT = "fruit"
    CATEGORY_LABEL = "label"
    CATEGORY_EXTRA = "extra"
    CATEGORY_CHOICES = (
        (CATEGORY_DEVICE_READING, "设备采集屏幕"),
        (CATEGORY_ENVIRONMENT, "地块环境"),
        (CATEGORY_PLANT, "植株"),
        (CATEGORY_FRUIT, "果实"),
        (CATEGORY_LABEL, "样品袋/标签"),
        (CATEGORY_EXTRA, "异常补充"),
    )

    PRECHECK_PENDING = "pending"
    PRECHECK_PASS = "precheck_pass"
    PRECHECK_WARNING = "precheck_warning"
    PRECHECK_BLOCKED = "precheck_blocked"
    PRECHECK_CHOICES = (
        (PRECHECK_PENDING, "待预检"),
        (PRECHECK_PASS, "预检通过"),
        (PRECHECK_WARNING, "预检警告"),
        (PRECHECK_BLOCKED, "预检阻断"),
    )

    REVIEW_PENDING = "review_pending"
    REVIEW_APPROVED = "approved"
    REVIEW_RETURNED = "returned"
    REVIEW_VOIDED = "voided"
    REVIEW_CHOICES = (
        (REVIEW_PENDING, "待审核"),
        (REVIEW_APPROVED, "已通过"),
        (REVIEW_RETURNED, "退回补拍"),
        (REVIEW_VOIDED, "已作废"),
    )

    IMMUTABLE_PENDING = "pending"
    IMMUTABLE_LOCKED = "locked"
    IMMUTABLE_VOIDED = "voided"
    IMMUTABLE_CHOICES = (
        (IMMUTABLE_PENDING, "待锁定"),
        (IMMUTABLE_LOCKED, "原图已锁定"),
        (IMMUTABLE_VOIDED, "已作废"),
    )

    photo_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="Photo_ID")
    event = models.ForeignKey(CollectionEvent, related_name="photos", on_delete=models.CASCADE, verbose_name="采集事件")
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, verbose_name="照片分类")
    original_file = models.CharField(max_length=512, null=True, blank=True, verbose_name="原图路径")
    watermarked_file = models.CharField(max_length=512, null=True, blank=True, verbose_name="水印图路径")
    sha256 = models.CharField(max_length=128, verbose_name="原图SHA256")
    metadata_json = models.JSONField(default=dict, blank=True, verbose_name="照片Metadata")
    precheck_status = models.CharField(max_length=32, choices=PRECHECK_CHOICES, default=PRECHECK_PENDING, verbose_name="预检状态")
    review_status = models.CharField(max_length=32, choices=REVIEW_CHOICES, default=REVIEW_PENDING, verbose_name="审核状态")
    immutable_status = models.CharField(max_length=32, choices=IMMUTABLE_CHOICES, default=IMMUTABLE_PENDING, verbose_name="不可变状态")
    uploaded_at = models.DateTimeField(null=True, blank=True, verbose_name="上传完成时间")

    class Meta:
        db_table = table_prefix + "coffee_photo_asset"
        verbose_name = "咖啡照片资产"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["event", "category"]),
            models.Index(fields=["event", "review_status"]),
        ]


class PhotoAnnotation(CoreModel):
    SHAPE_BBOX = "bbox"
    SHAPE_POLYGON = "polygon"
    SHAPE_POINT = "point"
    SHAPE_CHOICES = (
        (SHAPE_BBOX, "矩形框"),
        (SHAPE_POLYGON, "多边形"),
        (SHAPE_POINT, "点"),
    )

    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = (
        (SOURCE_MANUAL, "人工标注"),
    )

    annotation_id = models.CharField(max_length=64, db_index=True, verbose_name="标注ID")
    photo = models.ForeignKey(PhotoAsset, related_name="annotations", on_delete=models.CASCADE, verbose_name="照片")
    label = models.CharField(max_length=64, verbose_name="标签")
    shape_type = models.CharField(max_length=32, choices=SHAPE_CHOICES, default=SHAPE_BBOX, verbose_name="形状类型")
    geometry_json = models.JSONField(default=dict, verbose_name="标注几何")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")
    is_latest = models.BooleanField(default=True, verbose_name="最新版本")
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_MANUAL, verbose_name="来源")
    annotated_by = models.CharField(max_length=64, null=True, blank=True, verbose_name="标注人")
    note = models.CharField(max_length=255, null=True, blank=True, verbose_name="备注")

    class Meta:
        db_table = table_prefix + "coffee_photo_annotation"
        verbose_name = "咖啡照片人工标注"
        verbose_name_plural = verbose_name
        unique_together = (("annotation_id", "version"),)
        indexes = [
            models.Index(fields=["photo", "label", "is_latest"]),
            models.Index(fields=["photo", "annotation_id", "version"]),
        ]


class PhotoUploadChunk(CoreModel):
    photo = models.ForeignKey(PhotoAsset, related_name="upload_chunks", on_delete=models.CASCADE, verbose_name="照片")
    upload_session_id = models.CharField(max_length=64, db_index=True, verbose_name="上传会话ID")
    chunk_index = models.PositiveIntegerField(verbose_name="分片序号")
    chunk_hash = models.CharField(max_length=128, verbose_name="分片Hash")
    chunk_size = models.PositiveIntegerField(verbose_name="分片大小")
    status = models.CharField(max_length=32, default="uploaded", verbose_name="状态")
    uploaded_at = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")

    class Meta:
        db_table = table_prefix + "coffee_photo_upload_chunk"
        verbose_name = "咖啡照片上传分片"
        verbose_name_plural = verbose_name
        unique_together = (("photo", "chunk_index"),)
        indexes = [
            models.Index(fields=["photo", "status"]),
            models.Index(fields=["upload_session_id", "chunk_index"]),
        ]


class OCRResult(CoreModel):
    PROVIDER_PADDLE = "paddleocr"
    PROVIDER_HUAWEI = "huawei_ocr"
    PROVIDER_MANUAL = "manual"
    PROVIDER_CHOICES = (
        (PROVIDER_PADDLE, "PaddleOCR"),
        (PROVIDER_HUAWEI, "华为OCR"),
        (PROVIDER_MANUAL, "人工录入"),
    )

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_TIMEOUT = "timeout"
    STATUS_MANUAL = "manual"
    STATUS_CHOICES = (
        (STATUS_PENDING, "待识别"),
        (STATUS_RUNNING, "识别中"),
        (STATUS_SUCCESS, "识别成功"),
        (STATUS_FAILED, "识别失败"),
        (STATUS_TIMEOUT, "识别超时"),
        (STATUS_MANUAL, "人工录入"),
    )

    ocr_result_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="OCR结果ID")
    photo = models.ForeignKey(PhotoAsset, related_name="ocr_results", on_delete=models.CASCADE, verbose_name="照片")
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, verbose_name="Provider")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="状态")
    raw_response_id = models.CharField(max_length=128, null=True, blank=True, verbose_name="原始响应引用")
    raw_response_json = models.JSONField(default=dict, blank=True, verbose_name="原始响应JSON")
    structured_json = models.JSONField(default=dict, blank=True, verbose_name="结构化识别结果")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, verbose_name="置信度")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    error_code = models.CharField(max_length=64, null=True, blank=True, verbose_name="错误码")
    error_message = models.CharField(max_length=255, null=True, blank=True, verbose_name="错误信息")

    class Meta:
        db_table = table_prefix + "coffee_ocr_result"
        verbose_name = "咖啡OCR结果"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["photo", "status"]),
            models.Index(fields=["provider", "status"]),
        ]


class OCRCorrection(CoreModel):
    ocr_result = models.ForeignKey(OCRResult, related_name="corrections", on_delete=models.CASCADE, verbose_name="OCR结果")
    field_name = models.CharField(max_length=64, verbose_name="字段名")
    raw_value = models.CharField(max_length=255, null=True, blank=True, verbose_name="原始值")
    corrected_value = models.CharField(max_length=255, verbose_name="修正值")
    reason = models.CharField(max_length=255, null=True, blank=True, verbose_name="修正原因")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")
    corrected_by = models.CharField(max_length=64, null=True, blank=True, verbose_name="修正人")
    corrected_at = models.DateTimeField(null=True, blank=True, verbose_name="修正时间")

    class Meta:
        db_table = table_prefix + "coffee_ocr_correction"
        verbose_name = "咖啡OCR修正"
        verbose_name_plural = verbose_name
        unique_together = (("ocr_result", "field_name", "version"),)


class ProviderCallLog(CoreModel):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_SUCCESS, "成功"),
        (STATUS_FAILED, "失败"),
    )

    provider_type = models.CharField(max_length=32, verbose_name="Provider类型")
    provider_name = models.CharField(max_length=64, verbose_name="Provider名称")
    request_id = models.CharField(max_length=128, db_index=True, verbose_name="请求ID")
    target_type = models.CharField(max_length=32, verbose_name="目标类型")
    target_id = models.CharField(max_length=64, db_index=True, verbose_name="目标ID")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, verbose_name="状态")
    latency_ms = models.PositiveIntegerField(default=0, verbose_name="耗时毫秒")
    request_digest = models.CharField(max_length=128, null=True, blank=True, verbose_name="请求摘要")
    response_digest = models.CharField(max_length=128, null=True, blank=True, verbose_name="响应摘要")
    raw_response_ref = models.CharField(max_length=128, null=True, blank=True, verbose_name="原始响应引用")
    error_code = models.CharField(max_length=64, null=True, blank=True, verbose_name="错误码")
    called_at = models.DateTimeField(null=True, blank=True, verbose_name="调用时间")

    class Meta:
        db_table = table_prefix + "coffee_provider_call_log"
        verbose_name = "咖啡Provider调用日志"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["provider_type", "status"]),
            models.Index(fields=["target_type", "target_id"]),
        ]


class ProviderConfig(CoreModel):
    TYPE_MAP = "map"
    TYPE_WEATHER = "weather"
    TYPE_OCR = "ocr"
    TYPE_STORAGE = "storage"
    TYPE_CHOICES = (
        (TYPE_MAP, "地图"),
        (TYPE_WEATHER, "天气"),
        (TYPE_OCR, "OCR"),
        (TYPE_STORAGE, "存储"),
    )

    STATUS_MISSING = "missing"
    STATUS_CONFIGURED = "configured"
    STATUS_TESTED = "tested"
    STATUS_BLOCKED = "blocked"
    STATUS_CHOICES = (
        (STATUS_MISSING, "未配置"),
        (STATUS_CONFIGURED, "已配置"),
        (STATUS_TESTED, "测试通过"),
        (STATUS_BLOCKED, "阻塞"),
    )

    provider_type = models.CharField(max_length=32, choices=TYPE_CHOICES, db_index=True, verbose_name="Provider类型")
    provider_name = models.CharField(max_length=64, db_index=True, verbose_name="Provider名称")
    display_name = models.CharField(max_length=128, verbose_name="显示名称")
    enabled = models.BooleanField(default=False, verbose_name="启用状态")
    priority = models.PositiveIntegerField(default=100, verbose_name="优先级")
    timeout_ms = models.PositiveIntegerField(default=15000, verbose_name="超时毫秒")
    rate_limit_per_minute = models.PositiveIntegerField(default=60, verbose_name="每分钟限流")
    config_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_MISSING, verbose_name="配置状态")
    config_json = models.JSONField(default=dict, blank=True, verbose_name="配置JSON")
    secret_fields = models.JSONField(default=list, blank=True, verbose_name="敏感字段")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")

    class Meta:
        db_table = table_prefix + "coffee_provider_config"
        verbose_name = "咖啡Provider配置"
        verbose_name_plural = verbose_name
        unique_together = (("provider_type", "provider_name", "version"),)
        indexes = [
            models.Index(fields=["provider_type", "enabled"]),
            models.Index(fields=["config_status", "priority"]),
        ]


class ExportJob(CoreModel):
    TYPE_EVENT_DETAIL = "event_detail"
    TYPE_PHOTO_ASSET = "photo_asset"
    TYPE_OCR_CORRECTION = "ocr_correction"
    TYPE_QUALITY_REVIEW = "quality_review"
    TYPE_STATISTICS = "statistics"
    TYPE_DATASET_PACKAGE = "dataset_package"
    TYPE_CHOICES = (
        (TYPE_EVENT_DETAIL, "采集事件明细"),
        (TYPE_PHOTO_ASSET, "照片资产清单"),
        (TYPE_OCR_CORRECTION, "OCR结果和修正记录"),
        (TYPE_QUALITY_REVIEW, "质检审核记录"),
        (TYPE_STATISTICS, "统计报表"),
        (TYPE_DATASET_PACKAGE, "数据集包"),
    )

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_QUEUED, "排队"),
        (STATUS_RUNNING, "处理中"),
        (STATUS_SUCCESS, "完成"),
        (STATUS_FAILED, "失败"),
        (STATUS_EXPIRED, "已过期"),
        (STATUS_CANCELLED, "已取消"),
    )

    job_code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="导出任务编号")
    export_type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name="导出类型")
    filters_json = models.JSONField(default=dict, blank=True, verbose_name="筛选条件")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_QUEUED, verbose_name="状态")
    progress = models.PositiveIntegerField(default=0, verbose_name="进度")
    file_path = models.CharField(max_length=512, null=True, blank=True, verbose_name="文件路径")
    file_sha256 = models.CharField(max_length=128, null=True, blank=True, verbose_name="文件SHA256")
    created_by = models.CharField(max_length=64, null=True, blank=True, verbose_name="创建人")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    error_message = models.CharField(max_length=255, null=True, blank=True, verbose_name="错误信息")

    class Meta:
        db_table = table_prefix + "coffee_export_job"
        verbose_name = "咖啡导出任务"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["export_type", "status"]),
            models.Index(fields=["created_by", "create_datetime"]),
        ]


class MetricDefinition(CoreModel):
    GROUP_PROGRESS = "progress"
    GROUP_QUALITY = "quality"
    GROUP_PERFORMANCE = "performance"
    GROUP_CHOICES = (
        (GROUP_PROGRESS, "采集进度"),
        (GROUP_QUALITY, "质量统计"),
        (GROUP_PERFORMANCE, "绩效统计"),
    )

    metric_code = models.CharField(max_length=64, db_index=True, verbose_name="指标编码")
    metric_name = models.CharField(max_length=128, verbose_name="指标名称")
    metric_group = models.CharField(max_length=32, choices=GROUP_CHOICES, db_index=True, verbose_name="指标分组")
    calculation_method = models.CharField(max_length=255, verbose_name="计算口径")
    unit = models.CharField(max_length=32, null=True, blank=True, verbose_name="单位")
    enabled = models.BooleanField(default=True, verbose_name="启用状态")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")

    class Meta:
        db_table = table_prefix + "coffee_metric_definition"
        verbose_name = "咖啡统计指标口径"
        verbose_name_plural = verbose_name
        unique_together = (("metric_code", "version"),)
        indexes = [
            models.Index(fields=["metric_group", "enabled"]),
            models.Index(fields=["metric_code", "version"]),
        ]


class BGradeRule(CoreModel):
    METRIC_APPROVED_EVENT_COUNT = "approved_event_count"
    METRIC_RETURNED_EVENT_COUNT = "returned_event_count"
    METRIC_SUBMITTED_EVENT_COUNT = "submitted_event_count"
    METRIC_CHOICES = (
        (METRIC_APPROVED_EVENT_COUNT, "通过事件数量"),
        (METRIC_RETURNED_EVENT_COUNT, "退回事件数量"),
        (METRIC_SUBMITTED_EVENT_COUNT, "已提交事件数量"),
    )

    LEVEL_BLOCKING = "blocking"
    LEVEL_WARNING = "warning"
    LEVEL_CHOICES = (
        (LEVEL_BLOCKING, "阻断"),
        (LEVEL_WARNING, "警告"),
    )

    rule_code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="规则编号")
    rule_name = models.CharField(max_length=128, verbose_name="规则名称")
    task_code = models.CharField(max_length=64, db_index=True, verbose_name="适用任务")
    metric = models.CharField(max_length=64, choices=METRIC_CHOICES, verbose_name="指标")
    min_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="最小数量")
    max_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="最大数量")
    block_level = models.CharField(max_length=32, choices=LEVEL_CHOICES, default=LEVEL_BLOCKING, verbose_name="阻断级别")
    enabled = models.BooleanField(default=True, verbose_name="启用状态")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")

    class Meta:
        db_table = table_prefix + "coffee_b_grade_rule"
        verbose_name = "咖啡B级数量规则"
        verbose_name_plural = verbose_name
        unique_together = (("task_code", "rule_name", "version"),)
        indexes = [
            models.Index(fields=["task_code", "enabled"]),
            models.Index(fields=["metric", "block_level"]),
        ]


class QualityReview(CoreModel):
    REVIEW_TYPE_EVENT = "event"
    REVIEW_TYPE_PHOTO = "photo"
    REVIEW_TYPE_CHOICES = (
        (REVIEW_TYPE_EVENT, "数据包审核"),
        (REVIEW_TYPE_PHOTO, "照片审核"),
    )

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_RETURNED = "returned"
    STATUS_RECHECKING = "rechecking"
    STATUS_CHOICES = (
        (STATUS_PENDING, "待审核"),
        (STATUS_APPROVED, "通过"),
        (STATUS_RETURNED, "退回"),
        (STATUS_RECHECKING, "复核中"),
    )

    event = models.ForeignKey(CollectionEvent, related_name="quality_reviews", on_delete=models.CASCADE, verbose_name="采集事件")
    review_type = models.CharField(max_length=32, choices=REVIEW_TYPE_CHOICES, default=REVIEW_TYPE_EVENT, verbose_name="审核类型")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="审核状态")
    reviewer_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="审核员ID")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    result_json = models.JSONField(default=dict, blank=True, verbose_name="审核结果")
    return_reason = models.CharField(max_length=128, null=True, blank=True, verbose_name="退回原因")
    return_items = models.JSONField(default=list, blank=True, verbose_name="退回项")
    version = models.PositiveIntegerField(default=1, verbose_name="版本")

    class Meta:
        db_table = table_prefix + "coffee_quality_review"
        verbose_name = "咖啡质检审核"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["event", "review_type", "version"]),
            models.Index(fields=["status", "reviewed_at"]),
        ]
