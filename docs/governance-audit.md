# Governance Audit Report

> 范围：本次盘点聚焦“基础治理 + 风险消除”，不涉及功能新增和大规模重构。

## A. 项目结构概览

- `frontend/`：React + TypeScript + Vite 前端页面与样式。
- `backend/`：FastAPI 服务、SQLAlchemy 模型、脚本与测试。
  - `backend/app/`：后端核心（`main.py`、`models.py`、`schemas.py`、`config.py`）。
  - `backend/scripts/`：数据检查/修复脚本。
  - `backend/tests/`：已有 API 与数据完整性测试。
  - `backend/migrations/`：初始化 SQL 与 SQLite->MySQL 迁移辅助脚本。
- `docs/`：需求、架构、对齐记录、开发流程等文档。
- `docker-compose.yml`：仅声明 MySQL 服务。

## B. 运行方式现状

### 本地运行
- 后端：`uvicorn app.main:app --reload --port 8000`。
- 前端：`npm run dev`。
- 后端依赖在 `backend/requirements.txt`，含 FastAPI/SQLAlchemy/Pydantic/Pillow/PyMySQL。

### Docker 运行
- `docker-compose.yml` 当前只负责 MySQL（端口 `13306` 映射到容器 `3306`），应用服务仍需本地启动。

### 数据库选择
- 默认数据库 URL 为 SQLite：`sqlite:///./ai_app_square.db`（`backend/app/config.py`）。
- 生产建议 MySQL，`backend/app/database.py` 会根据 URL 自动切换 `check_same_thread`。

## C. 关键入口文件与关键路径

- 后端入口：`backend/app/main.py`
  - `@app.on_event("startup")` 中执行建表和 seed。
  - `/api/health` 可作为最小存活接口。
  - 排行榜相关逻辑同时存在：`calculate_app_score`（旧）与 `sync_rankings_service`（三层逻辑）。
- 配置入口：`backend/app/config.py`
- 数据模型：`backend/app/models.py`
- 序列化模型：`backend/app/schemas.py`
- 前端入口：`frontend/src/main.tsx`、`frontend/src/App.tsx`

## D. 当前已有文档清单与缺口

### 已有
- `README.md`：基础启动说明、接口列表、前端样式规范。
- `docs/three-layer-ranking-architecture-design.md`：三层榜单设计。
- `docs/dev-workflow.md` / `docs/GIT_WORKFLOW.md`：开发与协作流程。
- `docs/testing-env-notes.md`：测试环境记录。

### 缺口
- 缺少“治理修复记录”文档（每批变更目标、理由、验证、回滚）。
- README 缺少统一“最小验证链路”（启动 + 健康检查 + 关键接口 smoke）。
- 目录与路径约定（`static`、上传目录、图片目录）缺少显式配置说明与优先级定义。
- 榜单旧逻辑与新逻辑共存状态缺少“唯一权威路径”声明。

## E. 风险清单（P0/P1/P2）

## P0（运行失败/部署失败/数据错）

1. **StaticFiles 启动风险**
   - 当前固定挂载 `StaticFiles(directory="static")`，若仓库或运行目录中无 `static/`，FastAPI 启动将直接失败。
2. **上传/图片目录环境漂移风险**
   - 仅在模块加载时创建 `static/uploads`，缺乏统一配置（env/config/default）与图片目录约定。
   - 在不同工作目录启动时，路径解析可能漂移。
3. **一键最小验证链路缺失**
   - 缺少统一可复制的后端最小验证步骤（启动 + health + 关键读接口），环境问题难以快速定位。

## P1（高维护风险）

1. **榜单“双真相”风险**
   - 旧评分函数 `calculate_app_score` 与三层榜单同步逻辑 `sync_rankings_service` 并存。
   - 若入口未统一，存在“配置修改后结果未变化 / 不知道结果来自哪里”的歧义。
2. **模型与 Schema 类型一致性风险**
   - 存在 `mapped_column(Date)` 与类型注解 `datetime` 混用（如 `release_date`、`declared_at`），后续迁移/序列化易出现隐式转换问题。

## P2（规范与一致性）

1. 缺少统一开发脚本（如 run/test/lint）与最小 lint 配置。
2. 环境变量示例与配置说明尚不完整（尤其是路径相关配置）。
3. 文档与代码中的“当前推荐运行方式”描述分散，协作上手成本偏高。

---

## 建议执行顺序（本轮）

1. Batch 1：先消除启动/路径硬风险（P0）。
2. Batch 2：明确榜单唯一权威路径并保留兼容（P1）。
3. Batch 3：收敛模型/Schema 类型一致性与迁移说明（P1）。
4. Batch 4：补齐最小工程化脚手架与治理文档闭环（P2）。
