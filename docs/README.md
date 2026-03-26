# Docs README

当前文档入口请按下面顺序阅读：

- 项目启动、部署与当前能力总览：`README.md`
- 数据库迁移与初始化：`docs/db-migration-sop.md`
- 本地开发环境、自检与 MySQL 测试：`docs/dev-setup.md`
- Git 分支与 PR 规范：`docs/dev-workflow.md`
- 准生产单机内网部署：`README.md` 中“准生产部署（单机内网、单端口同源）”
  - 开发机先执行 `make frontend-build` 和 `make release-bundle`
  - 远程主机只执行 `make app-run`

环境文件治理口径：

- `backend/.env`：唯一应用配置源
- 根目录 `.env`：仅 Docker Compose MySQL 变量
- 根目录 `.env.local`：已废止，不再允许使用

## Phase-4 PR-D 回归测试（口径锁定）

在仓库根目录执行：`cd backend && PYTHONPATH=. ../.venv/bin/pytest -q tests/test_ranking_consistency.py tests/test_phase4_regression_lock.py`。
## Phase-4 结项

- 结项说明：`docs/phase4-closure.md`（Scope / Artifacts / Verification）。
