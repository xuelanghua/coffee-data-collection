# 普洱咖啡数据采集系统 UAIDF Runbook

## 启动顺序

每轮工作开始前必须读取：

1. `AGENTS.md`
2. `automation/state.json`
3. `automation/acceptance.yaml`
4. `automation/runbook.md`
5. `automation/state.json` 中 `last_report` 指向的报告
6. `docs/manual/普洱咖啡数据采集系统开发任务书-UAIDF重写版.md`
7. `docs/design/`、`docs/ui/`、`docs/api/` 中与当前阶段相关的文件
8. `git status --short`

如果是中断恢复，先运行：

```bash
universal-ai-delivery-framework/.venv/bin/python -m uaidf resume-check --project .
```

如果缺少 `checkpoints/latest.yaml`，说明还没有可恢复 checkpoint，本轮只能按当前 `state.json` 和 `last_report` 继续，并在阶段结束时创建 checkpoint。

## 阶段门禁

- `G0` 已确认后，进入 `S1` 补齐需求、验收矩阵和 G1 输入。
- `G1` 未确认前，不进入 `S2`。
- `G2` 未确认前，不写业务代码。
- `G4` 未确认前，不执行真实服务联调。
- 真实密钥、真机、真实样本或生产环境缺失时，对应验收只能标记 `BLOCKED` 或 `NOT_VERIFIED`。

## 证据规则

- 验收状态只能使用 `PASS`、`FAIL`、`BLOCKED`、`NOT_VERIFIED`。
- Mock、本地、准生产、生产和人工证据必须分开记录。
- 每个 `PASS` 必须有证据路径。
- 不得把 `NOT_VERIFIED` 当作 `PASS`。
- 不得把 `BLOCKED` 包装成已完成。

## 常用验证命令

后端 API 测试：

```bash
cd backend && DATABASE_TYPE=SQLITE3 REDIS_ENABLE=false API_LOG_ENABLE=false .venv/bin/python manage.py test apps.coffee.tests -v 2
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
cd web && npm run lint && npm run build
```

App 验证：

```bash
cd coffee-collector-app && npm test && npm run lint && npm run build:app
```

完整验证：

```bash
scripts/verify-all.sh
```

## 外部依赖 BLOCKED 记录模板

- 阻塞项：
- 影响范围：
- 当前已完成证据：
- 解除条件：
- 需要谁提供什么：
- 下一步动作：
