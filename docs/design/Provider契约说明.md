# Provider 契约说明

## 设计原则

- 业务模型不直接依赖厂商原始结构。
- Provider 输入输出使用统一 DTO。
- 原始请求摘要、响应摘要、原始响应引用和错误码写入调用日志。
- 真实 Provider 配置缺失时，真实验收标记 `BLOCKED`；Mock Provider 可用于本地自动测试。

## 地图 Provider

输入：

```json
{
  "longitude": 100.0,
  "latitude": 22.0,
  "coordinate_system": "gcj02",
  "operation": "reverse_geocode"
}
```

输出：

```json
{
  "provider": "amap",
  "coordinate_system": "gcj02",
  "address": "云南省普洱市...",
  "confidence": 0.95,
  "raw_ref": "provider_call_log_id"
}
```

一期真实 Provider：高德地图。后续可扩展腾讯/百度。

## 天气 Provider

输入：经纬度、采集时间、行政区。  
输出：天气、温度、湿度、风力、数据时间、Provider、raw_ref。  
一期真实 Provider：聚合天气。

## OCR Provider

Provider：

- `paddleocr`：本地 HTTP 服务，优先用于 Mock/本地和真实样本测试。
- `huawei_ocr`：外部云服务，配置缺失时真实验收 `BLOCKED`。
- `manual`：人工录入，作为兜底 Provider。

统一输入：

```json
{
  "photo_id": "PH202606230001",
  "image_ref": "storage://...",
  "template": "device_reading_v1",
  "timeout_ms": 15000
}
```

统一输出：

```json
{
  "provider": "paddleocr",
  "status": "success",
  "fields": [
    {
      "name": "reading_value",
      "value": "12.6",
      "confidence": 0.91,
      "bbox": [10, 20, 100, 40]
    }
  ],
  "raw_ref": "provider_call_log_id"
}
```

## 存储 Provider

一期默认本地文件存储，可通过适配层扩展对象存储。  
契约：初始化上传、分片上传、完成上传、生成受控下载 URL、校验 Hash。

## 错误模型

| 错误码 | 说明 | 可重试 |
|---|---|---|
| PROVIDER_TIMEOUT | 超时 | 是 |
| PROVIDER_AUTH_FAILED | 鉴权失败 | 否 |
| PROVIDER_RATE_LIMIT | 限流 | 是 |
| PROVIDER_BAD_RESPONSE | 响应格式异常 | 否 |
| PROVIDER_NOT_CONFIGURED | 未配置 | 否 |
| PROVIDER_SAMPLE_REQUIRED | 缺真实样本 | 否 |
