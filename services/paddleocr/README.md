# PaddleOCR Service

本服务为普洱咖啡数据采集系统的一期 OCR Provider 本地骨架。

当前能力：

- `GET /health`：返回服务健康状态、Provider 名称、引擎模式和模板列表。
- `POST /predict`：按 `device_reading_v1` 模板解析设备采集屏幕文本，输出 10 个设备采集字段。

当前默认 `PADDLEOCR_ENGINE_MODE=mock`，用于本地契约验证。真实 PaddleOCR 引擎和真实样本准确率验证需在 G4/G5 具备环境和样本后单独验收。

