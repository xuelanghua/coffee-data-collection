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

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/auth/mobile-login/` | 手机号密码登录 |
| GET | `/app/tasks/` | 任务列表 |
| GET | `/app/tasks/{id}/` | 任务详情 |
| GET | `/app/tasks/{id}/offline-package/` | 离线包元数据 |
| GET | `/app/plots/` | 地块列表 |
| GET | `/app/plots/{plot_id}/points/` | 点位列表 |
| POST | `/app/events/` | 创建采集事件 |
| PATCH | `/app/events/{event_id}/draft/` | 保存草稿摘要 |
| POST | `/app/photos/init/` | 初始化照片上传 |
| PUT | `/app/photos/{photo_id}/chunks/{index}/` | 上传分片 |
| POST | `/app/photos/{photo_id}/complete/` | 完成照片上传 |
| POST | `/app/events/{event_id}/manifest/` | 提交 Manifest |
| POST | `/app/events/{event_id}/ocr/` | 发起 OCR |
| GET | `/app/events/{event_id}/ocr-results/` | 获取 OCR 结果 |
| POST | `/app/ocr-results/{id}/corrections/` | 保存人工校正 |
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
| GET/POST | `/points/` | 点位列表/新增 |
| POST | `/points/import/` | 导入点位 |
| GET | `/events/` | 采集事件列表 |
| GET | `/events/{event_id}/` | 采集事件详情 |
| POST | `/events/{event_id}/review/approve/` | 审核通过 |
| POST | `/events/{event_id}/review/return/` | 退回 |
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
  "measurements": [],
  "manifest_hash": "hex"
}
```

后端校验：任务权限、点位状态、照片 Hash、必拍分类、重复提交、Manifest Hash。

## 分页和筛选

Web 端遵循 django-vue3-admin 现有分页参数。App 端列表使用轻量分页：`page`、`page_size`、`updated_after`。
