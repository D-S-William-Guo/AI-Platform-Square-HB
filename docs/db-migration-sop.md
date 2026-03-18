# 数据库迁移 SOP（MySQL Only）

> 真相源固定为 `HistoricalRanking`。本项目数据库基线已收敛为 MySQL + Alembic，旧的多数据库兼容路径已下线。

## 1. 标准执行顺序

新环境或空库初始化时，固定按以下顺序执行：

1. 配置 `DATABASE_URL`
2. 执行 `alembic upgrade head`
3. 视需要执行：
   - `python -m app.bootstrap init-base`
   - `python -m app.bootstrap seed-demo`
4. 启动后端服务

## 2. 开发 / 部署最小步骤

### 2.1 本地 Docker MySQL

1. 准备环境变量：
   ```bash
   cp backend/.env.example backend/.env
   # 如需覆盖 docker compose 默认账号，可额外执行：
   # cp .env.example .env
   ```
2. 启动数据库：
   ```bash
   docker compose up -d mysql
   ```
3. 迁移并初始化：
   ```bash
   cd backend
   alembic upgrade head
   python -m app.bootstrap init-base
   # 如需演示数据：
   # python -m app.bootstrap seed-demo
   ```
4. 启动后端并验证关键接口（如 `/api/health`、`/api/apps`）。

### 2.2 远程 MySQL

1. 将 `DATABASE_URL` 指向远程 MySQL 服务。
2. 在部署主机执行：
   ```bash
   cd backend
   alembic upgrade head
   python -m app.bootstrap init-base
   ```
3. 启动后端并验证关键接口。

## 3. 测试数据库

- `TEST_DATABASE_URL` 仅供测试使用，必须指向独立测试库。
- `scripts/backend_test.sh` 会优先使用 `TEST_DATABASE_URL`。
- 默认本地测试地址：
  - `mysql+pymysql://ai_app_user:ai_app_password@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4`

## 4. 迁移规则

- 结构变更只允许通过 Alembic revision 管理。
- 运行时代码不允许再通过 `create_all()`、启动补字段或手写 SQL DDL 偷偷修库。
- PR 描述中必须写明：
  - 变更了哪些 Alembic revision；
  - 是否需要执行 `init-base` 或 `seed-demo`；
  - MySQL 下的验证结果摘要。
