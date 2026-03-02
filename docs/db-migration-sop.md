# 数据库迁移 SOP（Single Source of Truth）

> 真相源固定为 `HistoricalRanking`。涉及榜单对外口径的结构或字段调整，均以 `HistoricalRanking` 相关迁移与验证为准。

## 1. 执行顺序与不可跳步原则

- 迁移文件必须按编号顺序执行：`001` → `002` → `003` → ...
- 禁止跳过中间版本直接执行后续文件。
- 新环境初始化时，必须从 `001` 开始按序执行到最新。

## 2. 开发/验证最小步骤

### 2.1 SQLite（本地快速验证）

1. 在 `backend/.env` 配置：`DATABASE_URL=sqlite:///./ai_app_square.db`
2. 依次执行迁移文件（示例）：
   ```bash
   sqlite3 ai_app_square.db < backend/migrations/001_init.sql
   sqlite3 ai_app_square.db < backend/migrations/002_add_run_id_to_historical_rankings.sql
   sqlite3 ai_app_square.db < backend/migrations/003_add_ranking_audit_logs.sql
   ```
3. 启动后端并验证关键接口（如 `/api/health`、`/api/rankings`）。

### 2.2 MySQL（开发/联调）

1. 在 `backend/.env` 配置 MySQL `DATABASE_URL`。
2. 创建数据库后依次执行迁移文件（示例）：
   ```bash
   mysql -u <user> -p <db> < backend/migrations/001_init.sql
   mysql -u <user> -p <db> < backend/migrations/002_add_run_id_to_historical_rankings.sql
   mysql -u <user> -p <db> < backend/migrations/003_add_ranking_audit_logs.sql
   ```
3. 启动后端并验证关键接口（如 `/api/health`、`/api/rankings`）。

## 3. 新增 migration 规则

- **命名规则**：`NNN_<action>_<target>.sql`（例如：`004_add_xxx_to_historical_rankings.sql`）。
- **可审计要求**：SQL 需可读、可复现、可回溯，避免隐式/不可追踪操作。
- **PR 要求**：PR 描述中必须写明：
  - 新增/变更了哪些 migration 文件；
  - 在 SQLite/MySQL 的验证方式与结果摘要。
