# 普洱咖啡数据采集系统 Codex 快速开始提示词

以下提示词可直接复制给 Codex，用于在 UAIDF 通用 AI 开发框架约束下，基于《普洱咖啡数据采集系统开发任务书（UAIDF 重写版）》启动、设计、开发、验证和交付项目。
执行提示词前执行下面代码（先阅读 universal-ai-delivery-framework文件下的 readme.md 文件，按照文件执行代码）：
uv venv
uv run python -m uaidf init \
  --name my-project \
  --target .. \
  --profile lifecycle/agile \
  --profile technology/typescript \
  --profile risk/balanced


```text
你是 Codex，请在 Universal AI Delivery Framework（UAIDF）约束下，开发“普洱咖啡数据采集系统”。

一、项目基线

1. 项目基于 django-vue3-admin 开发。
4. django-vue3-admin 基座上的实现、测试、证据和验收状态必须重新生成。
5. 移动端使用 UniApp。
6. 优先 App，先打通现场采集闭环。
7. Web 使用 django-vue3-admin Vue3 管理端。
8. 一期完整交付，不把 App、Web、后端、OCR、统计、导出、真机验收等核心能力移出一期。

二、必须读取的文件

开始任何工作前，必须先读取：

1. AGENTS.md
2. automation/state.json
3. automation/acceptance.yaml
4. automation/runbook.md
5. automation/state.json 中 last_report 指向的报告
6. docs/tasks/ 或docs/目录中的《普洱咖啡数据采集系统开发任务书-UAIDF重写版.md》
7. docs/design/ 下与本任务相关的设计文档
8. docs/ui/ 下与本任务相关的 UI 文档
9. docs/api/ 下与本任务相关的接口文档
10. git status --short

如果这些文件不存在，先说明缺失项，并根据 S0/S1 规则提出创建方案，不要假装已经存在。

三、阶段和门禁

本项目必须按以下路径推进：

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

强制规则：

1. 先判断当前处于 S0-S6 的哪个阶段。
2. 再判断 G0-G6 哪些门禁已经确认。
3. G1 未确认前，不进入 S2。
4. G2 未确认前，不写业务代码。
5. G4 未确认前，不执行真实服务联调。
6. 未取得真实密钥、真机、真实样本时，不得宣称真实验收 PASS。

四、G1 需求确认规则

G1 要确认：

1. 一期完整交付范围。
2. P0/P1。
3. 明确非目标。
4. App 优先。
5. UniApp 移动端。
6. django-vue3-admin Web 管理端。
7. 允许小范围受控框架改造。
8. UI 系统自动设计并由用户确认后再开发。
9. 真实服务和真机可在外部条件缺失时标记 BLOCKED。
10. 验收必须基于证据。

如果 G1 未确认，先输出 G1 确认清单，不要继续设计或开发。

五、G2 UI 和设计确认规则

本项目所有 UI 由系统自动设计，并由用户确认后再开发。

G2 前必须输出：

1. App 全部页面清单。
2. Web 全部页面清单。
3. 页面字段。
4. 按钮和操作。
5. 权限和可见性。
6. 状态流转。
7. 空状态。
8. 加载状态。
9. 错误状态。
10. 弱网/离线状态。
11. 退回复核流程。
12. 低保真原型或浏览器原型。
13. 数据库模型。
14. API 契约。
15. Provider 契约。
16. OCR、图片、水印、上传、质检、导出和测试方案。

推荐输出：

- docs/ui/UI设计总说明.md
- docs/ui/App页面设计说明.md
- docs/ui/Web管理端页面设计说明.md
- docs/ui/字段与按钮清单.md
- docs/ui/状态与异常流程.md
- docs/ui/设计确认清单.md
- docs/design/系统架构设计.md
- docs/design/数据库设计.md
- docs/api/API契约说明.md
- docs/design/Provider契约说明.md
- docs/design/测试方案.md
- docs/prototypes/g2-key-flows.html

用户确认 G2 前，不要写业务代码。

六、开发优先级

进入 S3 后，按以下顺序推进：

1. 后端基础模型、迁移、字典、菜单初始化。
2. 后端登录、权限、任务、地块、点位、采集、照片、OCR、质检 API。
3. UniApp App 登录、任务、采集、拍照、本地草稿、上传队列、OCR 校正、提交。
4. Web 业务菜单、采集数据、照片审核、OCR 校正、配置、统计、导出。
5. PaddleOCR 服务、设备模板和 OCR 解析。
6. Docker Compose、环境模板、安全配置。

App 第一条闭环最高优先级：

登录 -> 查看任务 -> 选择地块/点位 -> 创建采集事件 -> 拍照 -> 保存本地草稿 -> 上传队列 -> OCR 识别 -> 人工校正 -> 提交 -> Web 审核

七、P0 必须覆盖

必须覆盖以下 P0 能力：

- App/Web 共用用户、组织、角色和权限。
- 手机号 + 密码登录。
- 采集员、审核员、管理员、查看员等角色权限。
- 先编号后采集。
- Plot_ID、Point_ID、Event_ID、Photo_ID 四级主键。
- 地块、采样点、采集事件、照片资产关系。
- 定位、手动选点、地块边界、面积复核。
- 分类拍照、水印、不可变原图、metadata、图片预检。
- 离线草稿、上传队列、断点续传、分片上传、幂等提交和 Manifest。
- 设备测量、异常复测、全部记录留存。
- PaddleOCR、华为 OCR、人工录入 Provider 契约。
- OCR 原始响应、置信度、人工修正、调用日志和审计。
- 图片和数据包质检。
- 退回复核。
- B 级数量规则。
- Web 业务菜单、数据列表、图片审核、OCR 校正、配置、统计、绩效和导出。
- MySQL 8、Redis、Celery Worker/Beat、PaddleOCR、健康检查和持久化 Compose。
- 自动测试、安全检查、真实服务配置门禁和交付文档。

八、代码目录边界

推荐目录：

- 后端领域模块：backend/apps/coffee/
- Web 页面：web/src/views/coffee/
- Web API：web/src/api/coffee/
- UniApp：coffee-collector-app/
- PaddleOCR：services/paddleocr/
- 脚本：scripts/
- 任务书：docs/tasks/
- 设计文档：docs/design/
- UI 文档：docs/ui/
- API 文档：docs/api/
- ADR：docs/adr/
- 验收矩阵：automation/acceptance.yaml
- 状态机：automation/state.json
- 报告：reports/

不要把业务代码写入 UAIDF 框架仓库，除非用户明确要求开发框架本身。

九、django-vue3-admin 改造规则

允许小范围受控改造：

- 权限、菜单、数据权限、字段权限的业务扩展。
- 文件上传、图片管理、对象存储适配。
- 操作日志、审计日志、Provider 调用日志扩展。
- Celery 任务、异步处理、导出任务扩展。
- 与业务强相关的基础组件扩展。

禁止：

- 绕过上游认证、权限、菜单、日志和数据权限体系。
- 为了快速通过测试删除核心规则。
- 硬编码密钥、AK/SK、Token、密码。
- 把外部厂商逻辑直接写死到业务模型。

高风险框架改造前必须输出：

1. ADR
2. 回归测试计划
3. 回滚说明
4. 用户确认

十、验收状态和证据

验收状态只能使用：

- PASS
- FAIL
- BLOCKED
- NOT_VERIFIED

规则：

1. 每个 P0/P1 需求必须登记到 automation/acceptance.yaml。
2. 每个需求必须有实现位置。
3. 每个需求必须有自动测试或人工测试说明。
4. 每个通过项必须有证据。
5. Mock 证据和真实证据必须分开。
6. 不得把 NOT_VERIFIED 当作 PASS。
7. 不得把 BLOCKED 包装成已完成。
8. 原始采集记录、原图、OCR 原始响应只增不改。
9. 修正必须通过版本、审计或修正记录表达。

十一、外部依赖 BLOCKED 规则

以下条件缺失时，允许标记为 BLOCKED：

- 缺少高德地图真实 Key。
- 缺少聚合天气真实 Key。
- 缺少华为 OCR 服务开通状态和真实配置。
- 缺少 Android/iOS 真机。
- 缺少真实设备图片样本集。
- 缺少生产或准生产部署环境。

BLOCKED 必须包含：

1. 阻塞项。
2. 影响范围。
3. 当前已完成证据。
4. 解除条件。
5. 需要谁提供什么。
6. 下一步动作。

十二、常用验证命令

后端 API 测试：
cd backend && DATABASE_TYPE=SQLITE3 REDIS_ENABLE=false API_LOG_ENABLE=false .venv/bin/python manage.py test apps.coffee.tests -v 2

领域规则测试：
PYTHONPATH=backend python3 -m unittest discover -s backend/apps/coffee/common/tests -v

PaddleOCR 测试：
PYTHONPATH=services/paddleocr python3 -m unittest discover -s services/paddleocr/tests -v

Web 验证：
cd web && npm run lint && npm run build

App 验证：
cd coffee-collector-app && npm test && npm run lint && npm run build:app

完整验证：
scripts/verify-all.sh

如果命令因 Docker、网络、真实密钥、真实样本或真机缺失失败，请记录为 BLOCKED，不要绕过门禁。

十三、每轮开始时必须输出

每轮工作开始时，先输出：

1. 当前阶段。
2. 已确认门禁。
3. 未确认门禁。
4. 本轮是否允许写代码。
5. 本轮目标。
6. 计划读取文件。
7. 计划修改文件。
8. 计划运行测试。
9. 是否需要用户确认。

十四、每轮结束时必须输出

每轮工作结束时，输出：

1. 修改摘要。
2. 测试和验证结果。
3. 更新的 evidence。
4. 更新的 acceptance status。
5. 残余风险。
6. BLOCKED 项和解除条件。
7. 下一步动作。

十五、现在请开始

现在请执行：

1. 读取启动文件、任务书和 last_report。
2. 判断当前处于 S0-S6 的哪个阶段。
3. 判断 G0-G6 哪些已确认、哪些未确认。
4. 如果 G1 未确认，输出 G1 确认清单。
5. 如果 G1 已确认但 G2 未确认，进入 S2，输出 App 和 Web 全部 UI 设计说明，不写业务代码。
6. 如果 G2 已确认，选择 App 优先闭环中的最小 P0 任务，按 TDD 开始实现。
```
