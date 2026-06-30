# API 契约说明

## 通用约定

- 前缀：`/api/coffee/`
- 认证：复用 django-vue3-admin Token/JWT 机制。
- 权限：复用菜单、按钮和数据权限。
- 幂等：创建采集事件、上传 Manifest、提交事件必须携带 `Idempotency-Key`。
- 错误响应：

```json
{
  "code": "COFFEE_VALIDATION_ERROR",
  "message": "字段校验失败",
  "details": {},
  "request_id": "req_xxx"
}
```

## App API

App 端采用“提交前独立上传和识别，最终一个接口提交”的边界：

- 图片上传接口负责大文件、分片、断点续传和 Hash 校验。
- OCR 接口负责实时识别并返回结构化字段，供当前页面输入框回填。
- 最终提交接口负责一次性提交 Manifest、最终字段值、OCR 纠正值、测量记录和图片引用。

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/auth/mobile-login/` | 手机号密码登录 |
| GET | `/app/tasks/` | 任务列表 |
| GET | `/app/tasks/{id}/` | 任务详情 |
| GET | `/app/tasks/{id}/offline-package/` | 离线包元数据 |
| GET | `/app/plots/` | 地块列表 |
| POST | `/app/plots/` | 现场圈选后创建正式地块 |
| POST | `/app/plots/{plot_id}/boundary-versions/` | 保存地块边界版本 |
| GET | `/app/plots/{plot_id}/points/` | 点位列表 |
| POST | `/app/points/` | 现场点选后创建正式采集点 |
| POST | `/app/events/` | 创建采集事件 |
| PATCH | `/app/events/{event_id}/draft/` | 保存草稿摘要 |
| POST | `/app/photos/init/` | 初始化照片上传 |
| PUT | `/app/photos/{photo_id}/chunks/{index}/` | 上传分片 |
| POST | `/app/photos/{photo_id}/complete/` | 完成照片上传 |
| POST | `/app/events/{event_id}/manifest/` | 提交 Manifest |
| POST | `/app/events/{event_id}/ocr/` | 发起 OCR |
| GET | `/app/events/{event_id}/ocr-results/` | 获取 OCR 结果 |
| POST | `/app/ocr-results/{id}/corrections/` | 可选：提交前保存人工校正草稿 |
| POST | `/app/events/{event_id}/submit/` | 提交采集事件 |
| GET | `/app/returns/` | 退回列表 |
| POST | `/app/events/{event_id}/resubmit/` | 退回后重新提交 |

## Web API

| 方法 | 路径 | 用途 |
|---|---|---|
| GET/POST | `/tasks/` | 任务列表/新增 |
| GET/PATCH | `/tasks/{id}/` | 任务详情/编辑 |
| POST | `/tasks/{id}/publish/` | 发布任务 |
| POST | `/tasks/{id}/assign/` | 分配采集员 |
| GET/POST | `/plots/` | 地块列表/新增 |
| POST | `/plots/import/` | 导入地块 |
| POST | `/plots/{plot_id}/review/` | 复核 App 现场圈选地块 |
| GET/POST | `/points/` | 点位列表/新增 |
| POST | `/points/import/` | 导入点位 |
| POST | `/points/{point_id}/review/` | 复核 App 现场点选点位 |
| GET | `/events/` | 采集事件列表 |
| GET | `/events/{event_id}/` | 采集事件详情 |
| POST | `/events/{event_id}/review/approve/` | 审核通过 |
| POST | `/events/{event_id}/review/return/` | 退回 |
| POST | `/events/review/bulk-approve/` | 批量审核通过 |
| POST | `/events/review/bulk-return/` | 批量审核退回 |
| GET | `/photos/` | 照片资产列表 |
| POST | `/photos/{photo_id}/review/` | 照片审核 |
| GET | `/ocr/jobs/` | OCR 任务列表 |
| POST | `/ocr/jobs/{id}/retry/` | OCR 重试 |
| GET/POST | `/provider-configs/` | Provider 配置 |
| POST | `/provider-configs/{id}/test/` | 连接测试 |
| GET | `/statistics/progress/` | 采集进度 |
| GET | `/statistics/quality/` | 质量统计 |
| GET | `/statistics/performance/` | 绩效统计 |
| GET/POST | `/exports/` | 导出任务 |
| POST | `/exports/{id}/cancel/` | 取消导出 |

## Manifest 契约

```json
{
  "event_id": "EV202606230001",
  "plot_id": "PL202606230001",
  "plot_boundary_version": 1,
  "point_id": "PT202606230001",
  "idempotency_key": "uuid",
  "app_version": "1.0.0",
  "photos": [
    {
      "photo_id": "PH202606230001",
      "category": "device_reading",
      "sha256": "hex",
      "metadata": {}
    }
  ],
  "field_values": [
    {
      "field_code": "air_temperature",
      "field_label": "空气温度",
      "value_text": "23.6",
      "value_number": 23.6,
      "unit": "摄氏度",
      "source_type": "ocr",
      "source_photo_id": "PH202606230001",
      "ocr_result_id": "OCR202606230001",
      "ocr_raw_value": "23.8",
      "ocr_confidence": 0.91,
      "corrected_from": "23.8",
      "correction_reason": "人工核对设备采集屏幕"
    }
  ],
  "measurements": [
    {
      "device_no": "ENV-001",
      "measured_at": "2026-06-24T10:30:00+08:00",
      "wind_speed": 1.8,
      "wind_direction": "东南",
      "air_temperature": 23.6,
      "air_humidity": 72.0,
      "atmospheric_pressure": 90.8,
      "rainfall": 0.0,
      "soil_moisture": 38.5,
      "soil_temperature": 21.4,
      "soil_salinity": 0.18,
      "soil_ph": 6.4,
      "source_photo_id": "PH202606230001",
      "ocr_result_id": "OCR202606230001"
    }
  ],
  "manifest_hash": "hex"
}
```

后端校验：任务权限、点位状态、照片 Hash、必拍分类、字段完整性、OCR 结果引用合法性、重复提交、Manifest Hash。

## App 现场地块创建接口

`POST /api/coffee/app/plots/`

请求体：

```json
{
  "task_id": "TASK202606240001",
  "plot_id": "PL-local-or-server-confirmed",
  "name": "现场圈选地块",
  "boundary_geojson": {},
  "area_mu": 12.34,
  "area_calc_method": "geodesic",
  "coordinate_system": "gcj02",
  "source_type": "app_drawn",
  "idempotency_key": "uuid"
}
```

处理规则：

1. 校验采集员是否有任务权限。
2. 校验边界是合法 Polygon。
3. 后端复算面积并记录 App 面积与后端面积。
4. 创建正式 `Plot_ID`，`review_status` 初始为 `pending_review`。
5. 写入第一条 `coffee_plot_boundary_version`。
6. 返回可立即用于点位和采集事件的地块。

## App 现场点位创建接口

`POST /api/coffee/app/points/`

请求体：

```json
{
  "task_id": "TASK202606240001",
  "plot_id": "PL202606240001",
  "point_id": "PT-local-or-server-confirmed",
  "longitude": 100.0,
  "latitude": 22.0,
  "altitude": 1200.0,
  "coordinate_system": "gcj02",
  "source_type": "app_selected",
  "idempotency_key": "uuid"
}
```

处理规则：

1. 校验地块存在且属于当前任务。
2. 校验点位落在地块边界内；如定位精度不足，允许创建但标记复核风险。
3. 创建正式 `Point_ID`，`review_status` 初始为 `pending_review`。
4. 返回可立即用于创建采集事件的点位。

## 最终提交接口

`POST /api/coffee/app/events/{event_id}/submit/`

请求体：

```json
{
  "idempotency_key": "uuid",
  "manifest": {},
  "field_values": [],
  "measurements": [],
  "ocr_corrections": [],
  "submit_note": "现场采集完成"
}
```

处理规则：

1. 校验事件、地块、点位和采集员权限。
2. 校验所有图片已上传完成且 Hash 匹配。
3. 校验 `field_values` 中最终值，并写入 `coffee_event_field_value`。
4. 对 `ocr_corrections` 生成 `coffee_ocr_correction` 版本记录。
5. 写入测量和复测记录。
6. 更新 `coffee_collection_event` 状态为 `submitted`。
7. 重复提交同一幂等键返回同一提交结果。

## Web 详情接口

`GET /api/coffee/events/{event_id}/`

响应聚合：

```json
{
  "event": {},
  "task": {},
  "plot": {},
  "point": {},
  "field_values": [],
  "photos": [
    {
      "photo": {},
      "ocr_results": [],
      "ocr_corrections": []
    }
  ],
  "measurements": [],
  "quality_reviews": [],
  "audit_logs": []
}
```

该接口支撑后端同一个详情页面展示地块信息、图片资料、OCR 识别信息、最终字段值和审核信息。

## Web 批量审核接口

`POST /api/coffee/events/review/bulk-approve/`

请求体：

```json
{
  "event_ids": ["EV202606240001", "EV202606240002"],
  "review_note": "批量审核通过"
}
```

处理规则：

1. 校验审核员权限和数据权限。
2. 校验事件均为可审核状态。
3. 校验无阻断质检项。
4. 为每条事件生成独立 `coffee_quality_review` 记录。
5. 返回成功、失败和跳过清单。

`POST /api/coffee/events/review/bulk-return/`

请求体：

```json
{
  "event_ids": ["EV202606240001", "EV202606240002"],
  "return_reason": "OCR_OR_MEASUREMENT_ERROR",
  "return_note": "设备采集数据需重新校准",
  "return_items": ["ocr", "measurement"]
}
```

处理规则：

1. 校验审核员权限和数据权限。
2. 批量退回必须提供统一退回原因。
3. 为每条事件生成独立退回记录、审计日志和 App 退回任务。
4. 返回成功、失败和跳过清单。

## 分页和筛选

Web 端遵循 django-vue3-admin 现有分页参数。App 端列表使用轻量分页：`page`、`page_size`、`updated_after`。
