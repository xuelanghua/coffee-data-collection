# 普洱咖啡数据采集系统 UAIDF 快速开发使用说明

本文根据《普洱咖啡数据采集系统开发任务书（UAIDF 重写版）》编写，用于指导团队和 Codex 在 Universal AI Delivery Framework（UAIDF）约束下，重新基于 `django-vue3-admin` 快速完成普洱咖啡数据采集系统的一期完整交付。

对应任务书：

```text
/Users/xuelang/Documents/Code/Coffee Data Collection/普洱咖啡数据采集系统开发任务书-UAIDF重写版.md
```

## 1. 核心结论
开发口径统一为：

- 新项目基线：`django-vue3-admin`
- 移动端：UniApp
- 优先级：App 优先
- Web 端：django-vue3-admin Vue3 管理端
- 交付范围：一期完整交付
- UI 方式：系统自动设计，用户确认后再开发
- 框架改造：允许小范围受控改造，必须有 ADR、测试和回滚说明
- 验收方式：证据驱动，状态只允许 `PASS`、`FAIL`、`BLOCKED`、`NOT_VERIFIED`

`django-vue3-admin` 基座上的代码、测试、证据和验收状态必须重新生成。

## 2. 项目开始点

真正开始点是：

```text
S0 新基座初始化
```

不要直接跳到 S2 设计，也不要直接进入 S3 开发。

完整路径：

```text
S0 新基座初始化
  -> G0 立项/基线确认
S1 需求澄清与任务书确认
  -> G1 需求确认
S2 UI/UX、架构、数据库、API 和测试设计
  -> G2 设计确认
S3 App 优先开发 + 后端接口 + Web 管理端
  -> G3 实现确认
S4 本地自动验证、代码审查、发布准备
  -> G4 发布/真实联调确认
S5 真实服务、真机、真实样本联调
  -> G5 运行确认
S6 交付、复盘、框架沉淀
  -> G6 复盘确认
```

## 3. 每次启动必须读取

每次让 Codex 开发、设计、验证、修复或生成报告前，必须先读取：

1. `AGENTS.md`
2. `automation/state.json`
3. `automation/acceptance.yaml`
4. `automation/runbook.md`
5. `automation/state.json` 中 `last_report` 指向的报告
6. `docs/tasks/` 下的任务书
7. `docs/design/` 下的设计文档
8. `docs/ui/` 下的 UI 文档
9. 本轮相关报告
10. `git status --short`

目的：

- 确认当前处于 S0-S6 的哪个阶段。
- 确认对应 G0-G6 门禁是否已经通过。
- 避免把旧基座证据当成新基座证据。
- 避免覆盖用户已有修改。
- 避免把 Mock 证据当成真实服务证据。

## 4. 推荐项目目录

```text
Coffe Data Collection/
  AGENTS.md
  automation/
    project.yaml
    state.json
    acceptance.yaml
    runbook.md
    framework-lock.yaml
  docs/
    tasks/
    requirements/
    design/
    ui/
    api/
    config/
    prototypes/
    adr/
  reports/
    gates/
    development/
    test/
    integration/
    review/
    release/
  backend/
    apps/coffee/
  web/
    src/views/coffee/
    src/api/coffee/
  coffee-app/
  services/paddleocr/
  scripts/
  docker-compose.yml
```

## 5. S0 到 G1：先把项目站起来

### 5.1 S0 新基座初始化

Codex 要做：

1. 确认目标目录已经锁定 `django-vue3-admin`。
2. 锁定上游提交，写入 `automation/framework-lock.yaml` 或阶段报告。
3. 建立 UAIDF 治理文件。
4. 建立 `automation/state.json`、`automation/acceptance.yaml`、`automation/runbook.md`。
5. 输出 S0 基线报告。

完成条件：

- 上游提交已锁定。
- 基础目录存在。
- 本地基础环境可启动，或阻塞原因清晰。
- 可以进入 G0。

### 5.2 G0 立项/基线确认

需要用户确认：

- 接受重新基于 `django-vue3-admin`。
- 接受移动端 UniApp，App 优先。
- 接受 Web 使用 django-vue3-admin Vue3 管理端。
- 接受使用 UAIDF 管理阶段、门禁和证据。

### 5.3 S1 需求澄清与任务书确认

Codex 要做：

1. 读取新版任务书。
2. 把 P0/P1/非目标整理成需求清单。
3. 生成或更新 `automation/acceptance.yaml`。
4. 明确外部依赖和阻塞条件。
5. 输出 G1 需求确认稿。

### 5.4 G1 需求确认

用户可用以下口令确认：

```text
我确认 G1：接受本任务书中的一期完整交付范围、P0/P1、明确非目标、App 优先、UniApp 移动端、django-vue3-admin Web 管理端、允许小范围受控框架改造、UI 系统自动设计并由我确认后再开发、真实服务和真机可在外部条件缺失时标记 BLOCKED、验收必须基于证据。请进入 S2，先输出 App 和 Web 的全部 UI 设计说明，不要写业务代码。
```

## 6. S2 到 G2：UI 和系统设计

G2 是本项目最重要的设计门禁。

G2 前禁止开发业务代码。

Codex 要先输出：

- App 全部页面清单。
- Web 全部页面清单。
- 页面字段。
- 按钮和操作。
- 权限和可见性。
- 状态流转。
- 空状态。
- 加载状态。
- 错误状态。
- 弱网/离线状态。
- 退回复核流程。
- 低保真原型或浏览器原型。
- 数据库模型。
- API 契约。
- Provider 契约。
- OCR、图片、水印、上传、质检、导出和测试方案。

推荐输出文件：

```text
docs/ui/UI设计总说明.md
docs/ui/App页面设计说明.md
docs/ui/Web管理端页面设计说明.md
docs/ui/字段与按钮清单.md
docs/ui/状态与异常流程.md
docs/ui/设计确认清单.md
docs/design/系统架构设计.md
docs/design/数据库设计.md
docs/api/API契约说明.md
docs/design/Provider契约说明.md
docs/design/测试方案.md
docs/prototypes/g2-key-flows.html
```

用户确认 G2 后，Codex 才能进入 S3 开发。

## 7. S3：App 优先开发

S3 不是“所有人各写各的”，而是按采集闭环推进。

推荐顺序：

1. 后端基础模型、迁移、字典、菜单初始化。
2. 后端登录、权限、任务、地块、点位、采集、照片、OCR、质检 API。
3. UniApp App 登录、任务、采集、拍照、本地草稿、上传队列、OCR 校正、提交。
4. Web 业务菜单、采集数据、照片审核、OCR 校正、配置、统计、导出。
5. PaddleOCR 服务、设备模板和 OCR 解析。
6. Docker Compose、环境模板、安全配置。

App 第一条闭环必须优先跑通：

```text
登录
  -> 查看任务
  -> 选择地块/点位
  -> 创建采集事件
  -> 拍照
  -> 保存本地草稿
  -> 上传队列
  -> OCR 识别
  -> 人工校正
  -> 提交
  -> Web 审核
```

## 8. 子系统开发边界

### 8.1 后端

目录：

```text
backend/apps/coffee/
```

职责：

- 领域模型。
- API。
- 权限和数据权限。
- Provider 配置和调用。
- OCR 结果和修正。
- 图片资产。
- 质检。
- 标注。
- 统计。
- 导出。
- Celery 异步任务。
- 测试。

### 8.2 Web 管理端

目录：

```text
web/src/views/coffee/
web/src/api/coffee/
```

职责：

- 咖啡业务菜单。
- 任务管理。
- 地块管理。
- 点位管理。
- 采集事件管理。
- 照片管理和审核。
- OCR 结果和校正。
- 质检和退回。
- 标注管理。
- Provider 配置。
- 统计报表。
- 绩效统计。
- 数据导出。

约束：

- 保持 django-vue3-admin Vue3 + TypeScript + Vite + Element Plus 风格。
- 优先复用上游布局、菜单、表格、表单、上传、字典和权限组件。
- 不另写一套登录、权限或菜单体系。

### 8.3 App

目录：

```text
coffee-collector-app/
```

职责：

- 手机号 + 密码登录。
- 首页任务。
- 地块和采样点查看。
- 创建采集事件。
- 分类拍照。
- 水印和 metadata。
- 本地草稿。
- 上传队列。
- 断网恢复。
- OCR 结果查看。
- 人工校正。
- 质检退回修改。
- 我的记录和详情。

### 8.4 OCR 服务

目录：

```text
services/paddleocr/
```

职责：

- PaddleOCR HTTP 服务。
- 健康检查。
- 设备模板。
- 图像预处理。
- 识别结果结构化。
- 置信度输出。
- 错误和超时处理。
- 真实样本报告。

### 8.5 Provider 适配层

Provider 必须隔离外部厂商：

- 地图：高德，后续可扩展腾讯/百度。
- 天气：聚合天气。
- OCR：PaddleOCR、华为 OCR、人工录入。

业务模型不能直接依赖厂商返回结构。

## 9. 框架改造规则

允许小范围受控改造 `django-vue3-admin`。

可以改：

- 权限、菜单、数据权限、字段权限的业务扩展。
- 文件上传、图片管理、对象存储适配。
- 操作日志、审计日志、Provider 调用日志扩展。
- Celery 任务、异步处理、导出任务扩展。
- 与业务强相关的基础组件扩展。

改造前必须判断风险。

高风险改造必须输出：

```text
docs/adr/ADR-xxx-xxx.md
reports/review/框架改造评审报告.md
reports/test/框架改造回归测试报告.md
reports/release/框架改造回滚说明.md
```

禁止：

- 绕过上游认证、权限、菜单、日志和数据权限体系。
- 为了快速通过测试删除核心规则。
- 硬编码密钥、AK/SK、Token、密码。
- 把外部厂商逻辑直接写死到业务模型。

## 10. 验收和证据规则

验收状态只能使用：

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_VERIFIED`

每个需求必须在 `automation/acceptance.yaml` 中包含：

- requirement id。
- 标题。
- 优先级。
- 当前状态。
- 实现位置。
- 自动测试。
- 人工测试。
- 证据路径。
- 阻塞原因。
- 解除条件。

规则：

- 不得把 `NOT_VERIFIED` 当作 `PASS`。
- 不得把 `BLOCKED` 包装成完成。
- Mock 证据和真实服务证据必须分开。
- 原始采集记录、原图、OCR 原始响应只增不改。
- 修正必须通过版本、审计或修正记录表达。

## 11. 外部依赖 BLOCKED 规则

以下条件缺失时，可以标记为 `BLOCKED`：

- 缺少高德地图真实 Key。
- 缺少聚合天气真实 Key。
- 缺少华为 OCR 服务开通状态和真实配置。
- 缺少 Android/iOS 真机。
- 缺少真实设备图片样本集。
- 缺少生产或准生产部署环境。

`BLOCKED` 必须写清：

- 阻塞项。
- 影响范围。
- 当前已完成证据。
- 解除条件。
- 需要谁提供什么。
- 下一步动作。

## 12. 常用验证命令

后端 API 测试：

```bash
cd backend
DATABASE_TYPE=SQLITE3 REDIS_ENABLE=false API_LOG_ENABLE=false .venv/bin/python manage.py test apps.coffee.tests -v 2
```

领域规则测试：

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/apps/coffee/common/tests -v
```

PaddleOCR 测试：

```bash
PYTHONPATH=services/paddleocr python3 -m unittest discover -s services/paddleocr/tests -v
```

Web 验证：

```bash
cd web
npm run lint
npm run build
```

App 验证：

```bash
cd coffee-collector-app
npm test
npm run lint
npm run build:app
```

完整验证：

```bash
scripts/verify-all.sh
```

如果命令因 Docker、网络、真实密钥、真实样本或真机缺失失败，不要绕过门禁，应记录为 `BLOCKED`。

## 13. 人员和 Codex 配合方式

| 角色 | 人类职责 | Codex/AI 职责 |
|---|---|---|
| 项目负责人 | 确认 G0/G1/G5/G6，控制范围、预算和节奏 | 生成阶段报告、风险清单、门禁检查 |
| 产品/业务分析 | 确认业务流程、字段、验收标准 | 整理需求、拆分 P0/P1、生成验收矩阵 |
| UI/体验负责人 | 确认页面、流程和体验 | 自动生成页面清单、原型说明、状态设计 |
| 技术负责人 | 确认架构、接口、数据库、风险和回滚 | 生成架构方案、ADR、接口契约、测试建议 |
| 后端开发 | 实现 Django 模块、API、Provider、异步任务 | 生成代码、测试、迁移、接口文档 |
| Web 开发 | 实现 Vue3 管理端页面 | 生成页面、API 封装、权限接入、构建验证 |
| App 开发 | 实现 UniApp 采集 App | 生成页面、状态管理、离线队列、真机测试步骤 |
| OCR/算法负责人 | 确认 OCR 模板、样本、准确率 | 生成 OCR 服务、模板解析、样本报告 |
| 测试/质量 | 管理验收矩阵和证据 | 生成测试用例、执行脚本、报告和缺陷定位 |
| DevOps/运维 | 环境、部署、备份、回滚、监控 | 生成 Compose、部署文档、健康检查和回滚说明 |

## 14. 最小启动口令

```text
请读取当前项目 AGENTS.md、automation/state.json、automation/acceptance.yaml、automation/runbook.md、last_report 和docs/《普洱咖啡数据采集系统开发任务书-UAIDF重写版.md》。
本项目基于 django-vue3-admin 开发。
移动端使用 UniApp，优先 App；Web 使用 django-vue3-admin Vue3 管理端。
请先判断当前处于 S0-S6 的哪个阶段、G0-G6 哪些门禁已确认。
G1 未确认前不要进入 S2；G2 未确认前不要写业务代码。
如果 G1 已确认，请进入 S2，先输出 App 和 Web 的全部 UI 设计说明、字段、按钮、权限、状态、异常流程和验收标准。
```
