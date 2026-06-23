# 通用 AI 开发框架独立迁移说明

日期：2026-06-16

## 1. 目标

当前 `universal-ai-delivery-framework` 模板是在咖啡数据采集系统工作区内生成的。为了后续单独管理、审查、优化和升级，建议把它迁移为一个独立 Codex 项目和独立 Git 仓库。

迁移后的目标是：

- 框架模板不再受咖啡数据采集系统 `AGENTS.md`、状态机、业务门禁影响。
- 后续所有框架优化都在独立项目中进行。
- 咖啡数据采集系统只作为“使用该框架的业务项目”，而不是框架本体。
- 可持续检查框架是否存在业务耦合、组织耦合、技术栈耦合和流程耦合。

当前模板源路径：

```bash
/Users/xuelang/Documents/软件开发自动化框架/.worktrees/universal-ai-delivery-framework/universal-ai-delivery-framework
```

当前模板分支：

```bash
codex/universal-ai-delivery-framework
```

当前首版发布提交：

```bash
b9913a7 release: deliver universal AI delivery framework v0.1.0
```

## 2. 推荐迁移方式

推荐使用 Git subtree split，把当前仓库中的 `universal-ai-delivery-framework/` 子目录拆成一个独立历史分支，再从该分支 clone 成独立项目。

这样做的好处是：

- 独立项目根目录就是框架文件，不再嵌套一层 `universal-ai-delivery-framework/`。
- 可保留框架从 v0.1.0 开始的相关提交历史。
- 咖啡项目的业务代码不会进入新仓库。
- 后续 Codex 打开新目录时，读取的是框架自己的 `AGENTS.md`。

## 3. 迁移前检查

先确认当前模板工作区干净，只允许存在无关未跟踪文件，例如 `.DS_Store`。

```bash
cd /Users/xuelang/Documents/软件开发自动化框架/.worktrees/universal-ai-delivery-framework
DEVELOPER_DIR=/Library/Developer/CommandLineTools git status --short
```

如果看到模板文件有未提交变更，先不要迁移，应该先回到当前任务中提交或丢弃这些变更。

运行框架完整门禁：

```bash
cd /Users/xuelang/Documents/软件开发自动化框架/.worktrees/universal-ai-delivery-framework/universal-ai-delivery-framework
bash scripts/verify-framework.sh
```

期望结果：

```text
70 passed
uaidf 0.1.0
```

## 4. 创建独立 Git 分支

在包含外层 Git 仓库的 worktree 根目录执行：

```bash
cd /Users/xuelang/Documents/软件开发自动化框架/.worktrees/universal-ai-delivery-framework
DEVELOPER_DIR=/Library/Developer/CommandLineTools git subtree split \
  --prefix=universal-ai-delivery-framework \
  -b codex/uaidf-standalone
```

这个命令会创建一个新分支：

```bash
codex/uaidf-standalone
```

该分支的仓库根目录就是框架本体。

## 5. Clone 为独立项目

建议放到一个不属于咖啡系统的新目录，例如：

```bash
/Users/xuelang/Documents/通用AI开发框架
```

执行：

```bash
mkdir -p /Users/xuelang/Documents/通用AI开发框架

DEVELOPER_DIR=/Library/Developer/CommandLineTools git clone \
  --branch codex/uaidf-standalone \
  /Users/xuelang/Documents/软件开发自动化框架 \
  /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
```

进入新项目：

```bash
cd /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
DEVELOPER_DIR=/Library/Developer/CommandLineTools git status --short
```

期望：没有业务代码，没有咖啡系统目录，根目录直接包含：

```text
README.md
AGENTS.md
pyproject.toml
src/
framework/
profiles/
skills/
harness/
loops/
templates/
examples/
transformation-handbook/
assessments/
reports/
```

## 6. 在独立项目中安装和验证

```bash
cd /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework

python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
bash scripts/verify-framework.sh
```

期望：

```text
70 passed
uaidf 0.1.0
```

再执行几个关键冒烟：

```bash
.venv/bin/python -m uaidf version
.venv/bin/python -m uaidf route-check --data-class internal --task code
.venv/bin/python -m uaidf route-check --data-class restricted --task analysis
bash scripts/smoke-examples.sh
```

期望：

- version 输出 `uaidf 0.1.0`
- internal/code 输出 `enterprise-cloud`
- restricted/analysis 返回失败，说明默认拒绝受限数据
- smoke examples 全部 PASS

## 7. 在 Codex 中创建新的独立项目

在 Codex 桌面端中：

1. 新建或打开一个 Codex 线程。
2. 选择项目目录：

```bash
/Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
```

3. 确认 Codex 当前工作目录是独立框架目录，而不是：

```bash
/Users/xuelang/Documents/软件开发自动化框架
```

4. 新线程第一句话可以这样说：

```text
这是通用 AI 开发框架独立项目。请先读取 AGENTS.md、README.md、reports/首版框架验收报告.md，并运行 bash scripts/verify-framework.sh。后续所有优化只在当前框架项目内进行，不要引用咖啡数据采集系统规则。
```

## 8. 独立项目首轮去业务化检查

迁移完成后，建议立刻执行以下检查，确认没有咖啡数据采集系统残留。

```bash
cd /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework

rg -n "咖啡|普洱|coffee|采集|地块|土壤|PaddleOCR|OBS|OCR|django-vue-admin|Plot_ID|Point_ID|Event_ID|Photo_ID" .
```

期望：无结果。

如果有结果，按以下规则处理：

- 出现在示例业务文档中：改成通用示例，如 `agile-product` 或 `predictive-delivery`。
- 出现在框架规则中：改成中立表达，如 `domain data`、`business project`、`regulated data`。
- 出现在测试中：改成通用 fixture。
- 出现在 README 或手册中：改成“业务项目示例”，不要出现咖啡项目专有词。

## 9. 设计局限性检查清单

后续你可以在独立项目中要求 Codex 按这份清单做 review。

### 9.1 是否局限于咖啡数据采集系统

检查：

- 是否存在咖啡、普洱、采集、地块、土壤、OCR、OBS、PaddleOCR 等专有词。
- 是否假设业务一定有图片、地图、设备、采集员、质检员。
- 是否把“原始数据只增不改”写死到所有项目，而不是作为可选数据策略。
- 是否把 G1/G2/G3 咖啡项目门禁复制到了通用框架。

判断：

- 如果规则只对某类业务成立，应移动到 `skills/domains/` 或项目 Profile。
- 如果规则对所有项目成立，保留在 `AGENTS.md`、Harness 或 Gate 中。

### 9.2 是否局限于当前组织架构

检查：

- 是否写死“产品经理、UI、前端、后端、测试”必须一人一岗。
- 是否允许一人多责和多人共责。
- 是否使用 `value / experience / technology / quality` 责任能力，而不是组织岗位。

判断：

- 通用框架应绑定责任，不绑定部门。
- 岗位只在公司采用手册中作为映射建议出现。

### 9.3 是否局限于某个技术栈

检查：

- 是否默认只能 Django/Vue。
- 是否默认只能 Python。
- 是否能通过 `profiles/technology/*` 切换技术栈。
- `templates/project` 是否没有硬编码业务框架。

判断：

- 技术栈应在 Profile 中切换。
- 通用 CLI 和协议内核应保持技术无关。

### 9.4 是否局限于 Codex

检查：

- Codex 规则是否只存在于 `adapters/codex/`。
- `framework/`、`profiles/`、`skills/`、`loops/` 是否不依赖 Codex 专有能力。
- 是否有 `adapters/generic/adapter-contract.yaml`。

判断：

- Codex 是一个适配器，不是框架内核。
- 后续可增加 Claude、Cursor、CI、自研 Agent 适配器。

### 9.5 是否局限于敏捷或预测型

检查：

- 是否同时有 `profiles/lifecycle/agile.yaml`、`predictive.yaml`、`hybrid.yaml`。
- 示例是否同时覆盖敏捷和预测型。
- Gate 是否能支持连续门禁和阶段门禁。

判断：

- 生命周期应通过 Profile 切换。
- 不应把 Scrum、瀑布、看板任一方法写死为唯一流程。

### 9.6 是否局限于企业云 AI

检查：

- 默认是否是 `enterprise-cloud`。
- 是否支持 `private-cloud` 和 `local`。
- restricted 数据是否默认拒绝。
- 是否能通过配置切换模型和工具路由。

判断：

- 默认企业云是策略选择，不是框架限制。
- 受限数据必须可切换到私有或本地，但要有审批。

## 10. 独立项目中的优化升级流程

后续所有框架优化都在独立项目里走这套流程：

1. 新建优化分支：

```bash
cd /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
DEVELOPER_DIR=/Library/Developer/CommandLineTools git checkout -b codex/upgrade-framework-v0.2.0
```

2. 提出升级提案：

```bash
cp upgrades/proposals/example-process-improvement.yaml upgrades/proposals/UPG-002-your-change.yaml
```

3. 先写失败测试：

```bash
.venv/bin/python -m pytest tests/test_<area>.py -q
```

4. 实现最小变更。

5. 运行完整门禁：

```bash
bash scripts/verify-framework.sh
```

6. 更新发布记录：

```bash
upgrades/releases/0.2.0.yaml
framework/version.yaml
reports/
```

7. 提交：

```bash
DEVELOPER_DIR=/Library/Developer/CommandLineTools git add .
DEVELOPER_DIR=/Library/Developer/CommandLineTools git commit -m "feat: upgrade framework capability ..."
```

## 11. 咖啡项目如何使用独立框架

迁移后，咖啡数据采集系统不要再承载框架本体。它只需要记录自己使用的框架版本。

建议在咖啡项目中保留或新增：

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
```

如果咖啡项目需要升级框架，应该：

1. 在独立框架项目中完成升级和发布。
2. 在咖啡项目中提出框架升级确认。
3. 运行 migration dry-run。
4. 确认不会覆盖咖啡项目本地规则。
5. 再更新 `framework-lock.yaml`。

## 12. 不推荐做法

不要：

- 继续在咖啡系统目录里直接改通用框架。
- 把咖啡项目的 `automation/state.json` 当成框架项目状态。
- 把咖啡项目 G1/G2/G3 门禁复制成所有项目默认门禁。
- 为了迁移方便直接复制 `.venv`、`.pytest_cache`、`.DS_Store`。
- 在独立框架项目中引用咖啡项目密钥、数据库、OCR、OBS 或真实业务数据。

## 13. 备用迁移方式：不保留历史的纯复制

如果 subtree split 遇到问题，可以用纯复制方式。

```bash
mkdir -p /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework

rsync -av \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.pytest_cache' \
  --exclude '__pycache__' \
  --exclude '*.egg-info' \
  --exclude '.DS_Store' \
  /Users/xuelang/Documents/软件开发自动化框架/.worktrees/universal-ai-delivery-framework/universal-ai-delivery-framework/ \
  /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework/

cd /Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
DEVELOPER_DIR=/Library/Developer/CommandLineTools git init
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
bash scripts/verify-framework.sh
DEVELOPER_DIR=/Library/Developer/CommandLineTools git add .
DEVELOPER_DIR=/Library/Developer/CommandLineTools git commit -m "init: standalone universal AI delivery framework v0.1.0"
```

这种方式简单，但不保留之前的提交历史。

## 14. 建议给 Codex 的独立项目检查提示词

迁移完成后，在新 Codex 项目中可以直接发送：

```text
请审查当前 universal-ai-delivery-framework 独立项目是否仍然残留咖啡数据采集系统、django-vue-admin 上游项目、OCR/OBS/采集业务或当前组织结构的耦合。

要求：
1. 先运行 bash scripts/verify-framework.sh。
2. 用 rg 搜索业务残留关键词。
3. 检查 AGENTS.md、README.md、profiles、skills、harness、loops、templates、examples、transformation-handbook。
4. 按严重程度列出设计局限。
5. 对每个局限给出是否应移动到 domain skill、project profile、adapter、template 或 handbook。
6. 不直接修改文件，先给我优化计划。
```

如果你确认计划后，再让 Codex 在独立项目中执行升级。

## 15. 迁移完成判定

满足以下条件即可认为迁移完成：

- 独立目录存在：

```bash
/Users/xuelang/Documents/通用AI开发框架/universal-ai-delivery-framework
```

- Codex 新线程工作目录指向该目录。
- `bash scripts/verify-framework.sh` PASS。
- `rg` 业务残留关键词无结果，或残留项已分类并有优化计划。
- 咖啡项目不再作为框架本体修改位置。
- 后续框架升级只在独立项目中执行。
