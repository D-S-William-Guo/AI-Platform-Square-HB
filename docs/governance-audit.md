# Governance Audit Report

> 说明：本文件已按当前仓库状态更新，用于描述“现在是什么”；不再描述已删除的 SQLite 或手写 SQL 运行路径。

> 范围：本次盘点聚焦“基础治理 + 风险消除”，不涉及功能新增和大规模重构。

## A. 项目结构概览

- `frontend/`：React + TypeScript + Vite 前端页面与样式。
- `backend/`：FastAPI 服务、SQLAlchemy 模型、脚本与测试。
  - `backend/app/`：后端核心（`main.py`、`models.py`、`schemas.py`、`config.py`）。
  - `backend/scripts/`：MySQL 诊断、自检与少量 ORM 辅助脚本。
  - `backend/tests/`：已有 API 与 MySQL 测试基线。
  - `backend/alembic/`：MySQL Alembic 迁移脚本。
- `docs/`：需求、架构、对齐记录、开发流程等文档。
- `docker-compose.yml`：仅声明 MySQL 服务。

## B. 运行方式现状

### 本地运行
- 后端：`make backend-dev`。
- 前端：`make frontend-dev`。
- 后端依赖在 `backend/requirements.txt`，含 FastAPI/SQLAlchemy/Pydantic/Pillow/PyMySQL。

### Docker 运行
- `docker-compose.yml` 当前只负责 MySQL（端口 `13306` 映射到容器 `3306`），应用服务仍需本地启动。

### 数据库选择
- 数据库基线为 MySQL：`DATABASE_URL` 必须使用 `mysql+pymysql://...`。
- 启动前需要先执行 Alembic 迁移；应用本身不再负责建表或补表。

## C. 关键入口文件与关键路径

- 后端入口：`backend/app/main.py`
  - lifespan 中只做目录与数据库就绪检查。
  - `/api/health` 可作为最小存活接口。
  - 排行榜相关逻辑同时存在：`calculate_app_score`（旧）与 `sync_rankings_service`（三层逻辑）。
- 配置入口：`backend/app/config.py`
- 数据模型：`backend/app/models.py`
- 序列化模型：`backend/app/schemas.py`
- 前端入口：`frontend/src/main.tsx`、`frontend/src/App.tsx`

## D. 当前已有文档清单与缺口

### 已有
- `README.md`：基础启动说明、接口列表、前端样式规范。
- `docs/governance-fixes.md`：治理修复记录、验证与回滚思路。
- `docs/three-layer-ranking-architecture-design.md`：三层榜单设计。
- `docs/dev-workflow.md` / `docs/GIT_WORKFLOW.md`：开发与协作流程。
- `docs/testing-env-notes.md`：测试环境记录。

### 缺口
- 当前主入口文档已补齐：README、数据库迁移 SOP、开发环境自检与 Git 流程都可直接执行。
- 仍需持续保持“代码变更时同步更新文档”的纪律，避免治理文档再次落后于实现。

## E. 风险清单（P0/P1/P2）

## P0（运行失败/部署失败/数据错）

1. **StaticFiles 启动风险**
   - 当前已通过运行时目录校验与自动创建机制缓解，但路径配置变更仍需回归验证。
2. **上传/图片目录环境漂移风险**
   - 已统一锚定到 `backend/` 目录解析；后续若新增路径变量，必须保持同一解析策略。
3. **一键最小验证链路缺失**
   - 当前已由 `README.md`、`docs/dev-setup.md` 与 `scripts/backend_test.sh` 覆盖。

## P1（高维护风险）

1. **榜单“双真相”风险**
   - 旧评分函数 `calculate_app_score` 与三层榜单同步逻辑 `sync_rankings_service` 并存。
   - 需要继续坚持以 `HistoricalRanking` 和 `AppRankingSetting` 为对外与参评真相源。
2. **模型与 Schema 类型一致性风险**
   - 存在 `mapped_column(Date)` 与类型注解 `datetime` 混用（如 `release_date`、`declared_at`），后续迁移/序列化易出现隐式转换问题。

## P2（规范与一致性）

1. 前端依赖安全告警仍需单独治理，不应与业务改动混做。
2. 环境变量示例需要在每次新增配置项后同步更新。
3. 文档与代码中的“当前推荐运行方式”需要持续保持单一入口。

---

## 建议执行顺序（本轮）

1. 继续保持 MySQL-only + Alembic-only 的运行边界。
2. 对新增 schema 变更坚持 Alembic revision 管理。
3. 保持 README / docs / Makefile / 脚本说明同步更新。
