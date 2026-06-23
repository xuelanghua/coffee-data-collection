# 咖啡数据采集系统使用通用 AI 开发框架说明书

日期：2026-06-16

## 1. 说明书目标

本文说明如何用 `universal-ai-delivery-framework` 通用 AI 开发框架，驱动“普洱咖啡数据采集系统”的完整开发、验证、设计协同、AI 自动开发、Figma 连接、Prompt/Skill/Loop/Harness 调整和后续升级。

当前咖啡项目不是从零开始的新项目，而是已有明确基线和门禁的业务项目：

- 上游基线：`django-vue-admin v1.1.2`
- 后端：`dvadmin-backend/`，Django + DRF + JWT + 动态菜单 + 数据权限
- Web：`dvadmin-ui/`，Vue 2 + Element UI
- 当前状态：S5 本机环境验证中
- 已确认门禁：G1、G2、G3 本地验收确认
- 当前剩余重点：真实服务、真实设备、OBS/OCR 手动验证、真机验收和生产级证据

因此，咖啡项目使用通用框架时，不是重新初始化一个空项目，而是把通用框架作为“开发治理与 AI 协同层”叠加到现有项目上。

## 2. 推荐总体策略

推荐配置：

```yaml
profiles:
  - lifecycle/predictive
  - technology/django-vue
  - risk/conservative
```

原因：

- 咖啡系统已有明确 G1/G2/G3/S3/S4/S5 阶段，适合 `predictive` 的阶段门禁。
- 项目基线是 Django + Vue 2，因此使用 `technology/django-vue`。
- 涉及原始采集记录、图片、OCR 原始响应、地理位置、人员权限、真实服务密钥和数据审计，因此风险策略应使用 `conservative`。

AI 自治建议：

| 场景 | 自治等级 | 说明 |
|---|---:|---|
| 文档整理、需求拆分、测试草案 | L3 | AI 可主动产出，人工审核 |
| 单元测试、契约测试、本地 mock 实现 | L3 | AI 可开发并运行测试 |
| 业务代码修改 | L2-L3 | 需要最小测试先行和人工确认范围 |
| 数据迁移、权限、上传、密钥、真实服务 | L2 | AI 只能提出方案和补测试，执行需确认 |
| 生产发布、真实数据变更、框架升级 apply | L1-L2 | 必须人工确认 |

## 3. 目录如何组织

### 3.1 咖啡项目目录分层

咖啡项目继续使用当前目录：

```text
/Users/xuelang/Documents/软件开发自动化框架
```

通用框架建议迁移为独立项目：

```text
/Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
```

咖啡项目中只保留“引用关系”和“业务项目自己的治理文件”，不要把通用框架本体继续混入业务项目。

建议咖啡项目保持以下结构：

```text
automation/
  state.json
  acceptance.yaml
  framework-lock.yaml
  runbook.md
docs/
  requirements/
  analysis/
  design/
  ui/
  figma/
  ai-components/
  prompts/
  skills/
  harness/
  loops/
  reports/
reports/
  integration/
  release/
  ai/
evidence/
  gates/
  api/
  ui/
  ocr/
  obs/
  mobile/
checkpoints/
```

当前项目已有 `docs/analysis`、`docs/design`、`docs/ui`、`docs/tasks`，可以保留。新增目录用于承载 AI 框架化开发资产。

### 3.2 需求规格说明书放到哪个目录

推荐主需求规格说明书放在：

```text
docs/requirements/咖啡数据采集系统需求规格说明书.md
```

如果当前没有 `docs/requirements/`，创建该目录。

已有文档可以作为输入，不建议删除：

```text
docs/tasks/普洱咖啡数据采集系统开发任务书.md
docs/analysis/需求分析报告.md
docs/analysis/API需求清单.md
docs/analysis/数据对象清单.md
docs/analysis/页面清单.md
docs/analysis/角色权限说明.md
docs/design/概要设计说明书.md
docs/design/详细设计说明书.md
docs/design/API接口文档.md
docs/design/数据库设计说明书.md
docs/ui/UI设计总说明.md
```

主需求规格说明书应成为后续 AI 开发的统一输入，不要让 AI 同时从多个旧文档中猜需求。旧文档可以被引用，但最终口径以需求规格说明书和验收矩阵为准。

## 4. 需求规格说明书应包含哪些内容

建议结构：

```markdown
# 咖啡数据采集系统需求规格说明书

## 1. 项目背景和目标
## 2. 用户角色和权限
## 3. 业务范围
## 4. 业务流程
## 5. 功能需求
## 6. 数据需求
## 7. 图片、定位、OCR、OBS 和设备采集需求
## 8. App 端需求
## 9. Web 后台需求
## 10. API 需求
## 11. 非功能需求
## 12. 数据安全和审计要求
## 13. 离线、上传、重试和恢复要求
## 14. 质量验收标准
## 15. 阶段门禁
## 16. AI 自动开发范围
## 17. 不在本期范围
## 18. 术语表
```

### 4.1 需求规格说明书的重点

重点不是“把需求写多”，而是让 AI 能稳定开发、测试和验证。

最重要的内容：

1. **角色和权限**
   - 采集员、质检员、管理员分别能看什么、改什么、导出什么。
   - API 必须同时满足接口权限和数据权限。

2. **数据不可变和审计**
   - 原始采集记录、原图、OCR 原始响应只增不改。
   - 修正通过版本、标注、审核记录表达。

3. **四级业务编号**
   - `Plot_ID`
   - `Point_ID`
   - `Event_ID`
   - `Photo_ID`

4. **采集前置条件**
   - 未编号时禁止设备采集或批量拍照。
   - 异常设备读数需要提示清洁并复测。

5. **图片和上传**
   - 原图、本地不可变保存、Hash、幂等键、断点续传、Manifest。
   - 上传校验 MIME、扩展名、大小、解码结果、Hash、对象 Key。

6. **OCR Provider 合约**
   - PaddleOCR、华为 OCR、人工录入必须走统一 Provider 接口。
   - OCR 原始响应、置信度、版本、人工修正和调用日志必须保留。

7. **地图和定位**
   - WGS84、GCJ-02、BD-09 转换策略。
   - 定位来源、精度、手动选点、重新定位。

8. **验收标准**
   - 每个需求必须能映射到 `automation/acceptance.yaml`。
   - 状态只允许 `PASS`、`FAIL`、`BLOCKED`、`NOT_VERIFIED`。

9. **真实服务证据**
   - Mock 测试只证明本地契约。
   - OBS/OCR/地图/天气/真机必须有真实验收证据后才能宣称真实联调通过。

## 5. 需求如何进入 AI 开发流程

每个需求进入开发前，必须先变成一个 AI 任务契约，建议放在：

```text
docs/ai-components/<模块名>/<任务名>.md
```

例如：

```text
docs/ai-components/ocr/统一OCRProvider接口.md
docs/ai-components/photo/图片上传Manifest与断点续传.md
docs/ai-components/permission/采集数据权限校验.md
docs/ai-components/app/离线草稿与恢复.md
```

任务契约模板：

```markdown
# AI 组件开发任务：<组件名>

## 1. 目标

## 2. 业务背景

## 3. 输入

## 4. 输出

## 5. 影响范围

## 6. 约束

## 7. 数据权限和安全

## 8. 接口契约

## 9. 数据模型

## 10. UI 或交互要求

## 11. 测试要求

## 12. 验收证据

## 13. 不允许 AI 做的事

## 14. 回滚方案
```

## 6. 如何选择开发语言

### 6.1 咖啡项目不建议随意切换主语言

当前咖啡项目已有明确基线：

| 层 | 现状 | 建议 |
|---|---|---|
| 后端 | Django / DRF | 继续使用 Python / Django |
| Web | Vue 2 / Element UI | 继续使用 Vue 2 / Element UI |
| App | UniApp 待创建 | G2/G3 确认后再创建或继续推进 |
| OCR 服务 | Python 服务 | 保持独立 Python 服务 |
| 脚本和验证 | Python / Bash | 保持 |

因此，选择语言不是问“AI 想用什么”，而是：

1. 是否符合上游基线？
2. 是否减少集成风险？
3. 是否能复用已有权限、菜单、数据权限和测试能力？
4. 是否能被当前团队维护？

### 6.2 在通用框架中如何表达语言选择

咖啡项目对应通用框架 Profile：

```yaml
profiles:
  - lifecycle/predictive
  - technology/django-vue
  - risk/conservative
```

建议在咖啡项目新增：

```text
automation/framework-lock.yaml
```

内容示例：

```yaml
schema_version: 1
framework:
  name: universal-ai-delivery-framework
  version: 0.1.0
  source: /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
  profiles:
    - lifecycle/predictive
    - technology/django-vue
    - risk/conservative
technology:
  backend:
    language: python
    framework: django-drf
    path: dvadmin-backend/
  web:
    language: javascript
    framework: vue2-element-ui
    path: dvadmin-ui/
  ocr_service:
    language: python
    framework: fastapi-or-contract-service
    path: services/paddleocr-or-existing-path
  app:
    language: javascript
    framework: uniapp
    path: app/
    status: create_after_gate_confirmation
```

## 7. 如何在已有框架基础上开发

### 7.1 基本原则

不要让 AI 绕过 `django-vue-admin` 的已有能力。

必须沿用：

- `dvadmin-backend/` 的 Django、DRF、JWT
- 动态菜单
- 数据权限机制
- 系统角色权限
- `dvadmin-ui/` 的 Vue 2 + Element UI 风格
- 现有目录和编码习惯

AI 修改前必须先回答：

```text
1. 影响哪些文件？
2. 是否涉及数据库迁移？
3. 是否涉及权限或数据权限？
4. 是否涉及上传、密钥、真实服务或原始数据？
5. 回滚方案是什么？
6. 最小测试是什么？
```

### 7.2 推荐开发顺序

1. 需求规格说明书冻结本轮范围。
2. 更新 `automation/acceptance.yaml`。
3. 为模块写 AI 组件任务契约。
4. 先补测试。
5. 开发后端模型、Serializer、ViewSet、权限。
6. 开发 Web 页面和接口调用。
7. 开发 App 或 OCR 服务。
8. 补端到端或契约验证。
9. 更新报告和证据。

### 7.3 AI 开发时的提示词骨架

```text
你现在在普洱咖啡数据采集系统中开发 <模块名>。

必须遵守：
1. 读取 automation/state.json、automation/acceptance.yaml 和 last_report。
2. 不修改无关文件。
3. 沿用 dvadmin-backend 的 Django/DRF/JWT/动态菜单/数据权限机制。
4. 沿用 dvadmin-ui 的 Vue 2 + Element UI 风格。
5. 原始采集记录、原图、OCR 原始响应只增不改。
6. 先写最小失败测试，再实现。
7. Mock 只能证明本地契约，不能作为真实服务验收。

本次任务：
<粘贴 docs/ai-components/... 任务契约>

输出要求：
1. 先列影响文件、权限边界、迁移风险和回滚方案。
2. 先运行或新增最小测试。
3. 实现后运行相关测试。
4. 更新验收证据，不宣称未验证的真实服务通过。
```

## 8. 需要 AI 自动开发的组件如何描述

AI 组件描述要足够“可执行”，不能只写一句“实现图片上传”。

推荐写法：

```markdown
## 组件名称

图片上传 Manifest 与断点续传

## 组件目标

采集员在 App 离线或弱网环境中拍照后，系统能保存本地 Manifest，恢复上传队列，按 Photo_ID 幂等上传原图、水印图、缩略图和 metadata。

## 输入

- 用户登录 Token
- Event_ID
- Photo_ID
- 本地文件路径
- 图片 SHA-256
- metadata JSON

## 输出

- 上传任务状态
- OBS object key
- 服务端 photo record
- 审计日志

## 关键规则

- 原图不可覆盖。
- 同一个 Photo_ID 重复上传必须幂等。
- Hash 不一致必须拒绝。
- 上传失败可重试，不得生成重复业务记录。

## 测试

- 本地 Manifest 生成测试
- Hash 校验失败测试
- 重复上传幂等测试
- 上传队列恢复测试
- 权限不足拒绝测试

## 验收

- Mock Provider 契约 PASS
- 真实 OBS 上传手动或自动证据 PASS
- App 弱网/断网恢复证据 PASS 或 NOT_VERIFIED
```

### 8.1 咖啡项目建议拆分的 AI 组件

| 模块 | AI 组件 | 风险 |
|---|---|---|
| 权限 | 手机号登录、角色权限、数据权限 | 高 |
| 核心数据 | Plot/Point/Event/Photo 四级编号 | 高 |
| 采集 | 设备读数、复测、异常提示 | 高 |
| 图片 | 原图、水印、缩略图、Hash、Manifest | 高 |
| 上传 | 队列、分片、断点续传、幂等 | 高 |
| OCR | Provider 接口、PaddleOCR、华为 OCR、人工录入 | 高 |
| 地图 | 定位、手动选点、坐标系转换、地块 GeoJSON | 中高 |
| 质检 | A/B/C 等级、退回、复核闭环 | 中高 |
| Web | 人工标注、列表、导出、统计、配置 | 中 |
| App | 离线草稿、采集流程、同步状态 | 高 |

## 9. 如何连接 Figma 设计平台

### 9.1 推荐目录

```text
docs/figma/
  figma-connection.md
  figma-pages-map.md
  figma-components-map.md
  figma-review-record.md
```

### 9.2 Figma 连接说明

在 Codex 中连接 Figma 的常见方式是使用已启用的 Figma 插件或连接器。连接后，Codex 可以读取 Figma 文件、页面、组件、变量和设计稿信息，并把设计映射到前端任务。

建议记录：

```markdown
# Figma 连接记录

## Figma 文件

- 文件名：
- URL：
- File Key：
- 负责人：
- 最近确认时间：

## 页面映射

| Figma 页面 | 系统页面 | 前端路径 | 状态 |
|---|---|---|---|
| App-采集流程 | App 采集首页 | app/pages/collect/index | 待开发 |
| Web-质检 | 质检列表 | dvadmin-ui/src/views/... | 待开发 |

## 组件映射

| Figma 组件 | 前端组件 | 说明 |
|---|---|---|
| PhotoCard | CoffeePhotoCard | 图片、状态、Hash |
| QualityBadge | QualityBadge | A/B/C 等级 |
```

### 9.3 给 Codex 的 Figma 任务提示词

```text
请连接当前 Figma 文件，读取咖啡数据采集系统的 App 和 Web 页面设计。

目标：
1. 输出 Figma 页面到系统页面的映射表。
2. 输出 Figma 组件到 Vue/UniApp 组件的映射表。
3. 标出缺失状态：空状态、错误状态、权限不足、离线、上传中、上传失败、OCR 识别失败。
4. 不直接生成代码，先生成 docs/figma/figma-pages-map.md 和 docs/figma/figma-components-map.md。
5. 等我确认后，再把设计拆成 AI 开发任务。
```

### 9.4 Figma 到开发的门禁

Figma 设计确认前，不建议直接让 AI 开发 UI。

建议门禁：

```text
F1：Figma 文件连接确认
F2：页面映射确认
F3：组件映射确认
F4：关键状态覆盖确认
F5：开发任务拆分确认
```

## 10. 如何让 AI 自己设计，确认后执行开发

如果没有 Figma，或者希望 AI 先产出设计方案，可以走 AI 自设计流程。

### 10.1 AI 自设计流程

1. AI 读取需求规格说明书。
2. AI 读取现有 `docs/ui/` 和 `docs/prototypes/`。
3. AI 生成页面清单、流程图、字段布局、组件清单。
4. AI 生成 HTML 原型或 Markdown 原型说明。
5. 人工确认。
6. AI 把设计拆成开发任务。
7. AI 按 TDD 和门禁执行开发。

### 10.2 AI 自设计提示词

```text
请基于咖啡数据采集系统需求规格说明书，设计 <App/Web/某模块> 的 UI 和交互方案。

输入：
1. docs/requirements/咖啡数据采集系统需求规格说明书.md
2. docs/ui/UI设计总说明.md
3. docs/ui/App页面原型说明.md
4. docs/ui/Web后台页面原型说明.md
5. docs/design/API接口文档.md

要求：
1. 先输出页面清单。
2. 每个页面包含：目标、用户、入口、字段、操作、状态、错误、权限、验收点。
3. 必须覆盖：空状态、加载中、离线、权限不足、上传失败、OCR 失败、退回修改。
4. 不写代码。
5. 输出到 docs/ui/ai-design-<模块名>.md。
6. 等我确认“设计符合预期”后，再生成开发任务。
```

### 10.3 确认后执行开发提示词

```text
设计已确认。请把 docs/ui/ai-design-<模块名>.md 拆分成可执行开发任务。

要求：
1. 每个任务写入 docs/ai-components/<模块名>/。
2. 每个任务必须包含测试、验收证据、影响文件、权限边界、回滚方案。
3. 先输出任务列表，不直接开发。
4. 等我确认任务列表后，按优先级逐个 TDD 实现。
```

## 11. Prompt Engineering 需要调整什么

建议在咖啡项目新增：

```text
docs/prompts/
  system-constraints.md
  task-contract.md
  coffee-domain-rules.md
  review-rubric.md
  figma-to-development.md
```

### 11.1 system-constraints.md

从通用框架继承，再增加咖啡项目规则：

```markdown
- 每次开始必须读取 automation/state.json、automation/acceptance.yaml 和 last_report。
- G1/G2/G3/S5 门禁不得绕过。
- 后端沿用 dvadmin-backend 的 Django/DRF/JWT/动态菜单/数据权限。
- Web 沿用 dvadmin-ui 的 Vue 2 + Element UI。
- 原始采集记录、原图、OCR 原始响应只增不改。
- Mock 测试不得作为真实服务验收证据。
- 上传必须校验 MIME、扩展名、大小、解码、Hash 和 object key。
```

### 11.2 task-contract.md

每个 AI 任务必须写清：

- 任务目标
- 影响文件
- 数据模型
- API 契约
- 权限边界
- 数据权限
- 测试先行计划
- 验收证据
- 回滚方案
- 哪些动作需要人工确认

### 11.3 coffee-domain-rules.md

放咖啡项目专有规则：

- Plot/Point/Event/Photo 编号
- A/B/C 采集等级
- 复测规则
- 图片命名和水印
- 地理坐标转换
- OCR Provider 结构
- 质检退回闭环

## 12. Skill Engineering 需要调整什么

通用框架已有两类 Skill：

```text
skills/roles/
  value
  experience
  technology
  quality

skills/tasks/
  clarify-requirement
  design-review
  tdd
  debug
  code-review
  release
  retrospective
```

咖啡项目需要新增 domain skills，建议放在独立框架项目或咖啡项目：

```text
docs/skills/
  coffee-domain.yaml
  coffee-photo-upload.yaml
  coffee-ocr-provider.yaml
  coffee-geo-boundary.yaml
  coffee-qc-workflow.yaml
  coffee-data-permission.yaml
```

### 12.1 coffee-domain.yaml 应包含

- 业务术语
- 四级编号
- 采集流程
- 数据不可变规则
- 采集等级
- 质检闭环
- 真实服务验收边界

### 12.2 coffee-ocr-provider.yaml 应包含

- PaddleOCR Provider
- 华为 OCR Provider
- 人工录入 Provider
- 统一输入输出
- 原始响应保存
- 置信度和人工修正
- 真实服务验收条件

### 12.3 coffee-data-permission.yaml 应包含

- 采集员数据范围
- 质检员数据范围
- 管理员数据范围
- 列表、详情、图片、统计、导出、配置 API 的数据权限
- 权限测试模板

## 13. Loop Engineering 需要调整什么

通用框架已有五类 Loop：

```text
discovery
delivery
verification
operations
framework-improvement
```

咖啡项目建议增加项目级 loop 配置：

```text
docs/loops/
  coffee-discovery-loop.md
  coffee-delivery-loop.md
  coffee-verification-loop.md
  coffee-real-provider-loop.md
  coffee-mobile-acceptance-loop.md
```

### 13.1 discovery loop

用于需求澄清：

- 是否已明确角色和权限？
- 是否已明确数据对象？
- 是否已明确真实服务和 mock 边界？
- 是否已明确 App/Web/OCR/OBS/地图/天气范围？

### 13.2 delivery loop

用于日常开发：

- 一个任务只做一个可验证行为。
- 每轮先测试，再实现，再回归。
- 超过预算或连续失败时升级到人工设计复核。

### 13.3 verification loop

用于验收：

- 先本地测试。
- 再契约测试。
- 再真实服务测试。
- 再真机或浏览器测试。
- 未验证必须写 `NOT_VERIFIED`，不能写 PASS。

### 13.4 real-provider loop

专门处理 OBS/OCR/地图/天气：

- 环境变量存在性
- 签名请求
- 真实响应
- 错误码
- 降级策略
- 证据报告

### 13.5 mobile acceptance loop

专门处理 UniApp / 真机：

- iOS/Android 真机
- 定位权限
- 相机权限
- 离线草稿
- 弱网恢复
- 上传队列

## 14. Harness Engineering 需要调整什么

Harness 是 AI 执行约束层。咖啡项目要重点调整四类策略。

建议目录：

```text
docs/harness/
  permissions.md
  data-policy.md
  resume-policy.md
  model-routing.md
  verification-policy.md
```

### 14.1 permissions.md

明确 AI 哪些能做，哪些需要确认。

AI 可自动做：

- 读取文档
- 新增测试
- 运行本地测试
- 修改低风险业务代码
- 生成报告

AI 需要确认：

- 数据库迁移
- 权限模型修改
- 上传/对象存储修改
- 真实服务密钥配置
- 删除或覆盖数据
- 生产发布
- 框架升级 apply

### 14.2 data-policy.md

咖啡项目数据等级：

| 数据 | 等级 | 默认策略 |
|---|---|---|
| 公开文档 | public | 可给 AI |
| 代码和需求 | internal | 可走企业云 |
| 采集数据、图片、定位 | confidential | 需要脱敏或私有路由 |
| 密钥、Token、真实个人信息 | restricted | 默认拒绝 |

### 14.3 resume-policy.md

中断恢复规则：

- 工作区文件 Hash 未变化：可继续。
- 需求、权限、数据迁移、真实服务配置变化：等待确认。
- 上次失败原因未解决：不得重复执行。
- 同一阻塞连续出现三次：标记 BLOCKED。

### 14.4 model-routing.md

咖啡项目建议：

```yaml
default_provider: enterprise-cloud
deny_data_classes:
  - restricted
routes:
  - data_class: internal
    task: code
    provider: enterprise-cloud
  - data_class: confidential
    task: analysis
    provider: private-cloud
  - data_class: restricted
    task: any
    provider: deny
```

### 14.5 verification-policy.md

真实验收边界：

- SQLite 测试不等于 MySQL 验收。
- Mock OCR 不等于真实 OCR 验收。
- 静态 OBS 配置不等于签名上传通过。
- 浏览器页面 200 不等于业务流程通过。
- App 模拟器不等于真机验收。

## 15. 咖啡项目推荐门禁

当前已有 G1/G2/G3，可扩展为：

| 门禁 | 目的 | 是否已满足 |
|---|---|---|
| G1 | 开发任务书确认 | 已确认 |
| G2 | UI 与系统设计确认 | 已确认 |
| G3 | 本地验收确认 | 已确认 |
| G4 | 真实 Provider 验收 | 部分完成 |
| G5 | 真机/真实业务流程验收 | 待完成 |
| G6 | 发布准备确认 | 待完成 |

G4 重点：

- OBS 签名上传
- OCR 真实识别
- 地图/天气真实接口
- MySQL 8 真实数据库回归

G5 重点：

- App 真机定位
- 相机拍照
- 离线草稿
- 弱网上传
- 质检退回闭环

G6 重点：

- 发布包
- 回滚方案
- 备份方案
- 监控和日志
- 权限审计

## 16. 一次标准 AI 开发任务应该怎么执行

以“图片上传 Manifest 与断点续传”为例：

1. 写 `docs/ai-components/photo/图片上传Manifest与断点续传.md`
2. 更新 `automation/acceptance.yaml`
3. 让 AI 读取状态和 last_report
4. AI 输出影响文件、风险、回滚
5. AI 写失败测试
6. AI 运行失败测试并确认失败原因
7. AI 实现最小代码
8. AI 运行相关测试
9. AI 更新证据报告
10. 人工确认真实设备或真实 OBS 证据

提示词：

```text
请按 docs/ai-components/photo/图片上传Manifest与断点续传.md 执行开发。

硬性要求：
1. 先读取 automation/state.json、automation/acceptance.yaml、last_report。
2. 先列影响文件、数据迁移、权限边界、回滚方案。
3. 先写失败测试并运行。
4. 不得修改无关文件。
5. OBS 真实上传没有证据时，只能写 NOT_VERIFIED。
6. 完成后更新测试证据和报告。
```

## 17. 建议新增的文件清单

为了让通用框架真正接管咖啡项目开发，建议新增：

```text
docs/requirements/咖啡数据采集系统需求规格说明书.md
docs/ai-components/
docs/figma/
docs/prompts/
docs/skills/
docs/loops/
docs/harness/
evidence/gates/
evidence/api/
evidence/ui/
evidence/ocr/
evidence/obs/
evidence/mobile/
checkpoints/
automation/framework-lock.yaml
```

## 18. 首轮落地顺序

不要一口气让 AI 开发所有模块。建议：

1. 补 `automation/framework-lock.yaml`
2. 整理主需求规格说明书
3. 把 `automation/acceptance.yaml` 和需求规格说明书对齐
4. 拆 3 个高价值 AI 组件：
   - 数据权限校验
   - OCR Provider 统一接口
   - 图片 Manifest 与断点续传
5. 连接或生成 UI 设计
6. 逐个组件 TDD 开发
7. 跑真实 Provider loop
8. 跑移动端真机 loop

## 19. 你可以直接对 Codex 这样下达下一步

```text
请基于 docs/咖啡数据采集系统使用通用AI开发框架说明书.md，先为咖啡数据采集系统补齐以下治理文件：

1. docs/requirements/咖啡数据采集系统需求规格说明书.md
2. automation/framework-lock.yaml
3. docs/prompts/system-constraints.md
4. docs/harness/data-policy.md
5. docs/skills/coffee-domain.yaml

要求：
- 不开发业务代码。
- 不修改现有 G1/G2/G3 状态。
- 所有内容必须引用现有 docs/tasks、docs/analysis、docs/design、docs/ui。
- 完成后给出需求到验收矩阵的缺口清单。
```

## 20. 总结

通用 AI 开发框架在咖啡项目中的角色是：

- 用 Profile 固定生命周期、技术栈和风险策略。
- 用需求规格说明书统一 AI 输入。
- 用 AI 组件任务契约把需求变成可开发单元。
- 用 Figma 或 AI 自设计把 UI 先确认再开发。
- 用 Prompt/Skill/Loop/Harness 把 AI 行为限制在安全边界内。
- 用 Gate 和 Evidence 防止 mock、猜测和未验证内容变成“已完成”。

咖啡项目当前最应优先做的不是继续增加代码，而是把需求规格、验收矩阵、AI 组件任务、真实服务证据和中断恢复策略收拢到同一套框架语言里。这样后续每个模块都能稳定交给 AI 开发、测试和复盘。
