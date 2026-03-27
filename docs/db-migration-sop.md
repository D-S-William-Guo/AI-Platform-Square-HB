# 数据库迁移 SOP（MySQL Only）

> 真相源固定为 `HistoricalRanking`。本项目数据库基线已收敛为 MySQL + Alembic，旧的多数据库兼容路径已下线。
> 当前本地开发、CI、远程部署口径统一按 MySQL 5.7 验证。

## 1. 标准执行顺序

新环境或空库初始化时，固定按以下顺序执行：

1. 配置 `DATABASE_URL`
2. 执行 `alembic upgrade head`
3. 视需要执行：
   - `python -m app.bootstrap init-base`
   - `python -m app.bootstrap seed-demo`
4. 启动单端口服务

环境文件约束：

- `backend/.env` 是唯一应用配置源。
- 根目录 `.env` 仅用于本地 Docker Compose MySQL 凭据。
- 根目录 `.env.local` 已废止；脚本发现该文件存在会直接退出并提示迁移。
- `ENVIRONMENT=production` 时，后端安装脚本默认改走 `PIP_INDEX_URL_PRODUCTION` / `PIP_TRUSTED_HOST_PRODUCTION`；未显式配置时默认值为 `http://136.142.12.68/simple/` 和 `136.142.12.68`。

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
   如果你本机之前使用的是 MySQL 8.0 数据卷，先执行：
   ```bash
   docker compose down -v
   ```
   然后再重新 `docker compose up -d mysql`。MySQL 8.0 与 5.7 不应复用同一数据目录。
3. 迁移并初始化：
   ```bash
   cd backend
   alembic upgrade head
   python -m app.bootstrap init-base
   # 如需演示数据：
   # python -m app.bootstrap seed-demo
   ```
4. 开发模式下分别启动：
   - `make backend-dev`
   - `make frontend-dev`

最短命令清单：

```bash
cd /home/ctyun/BigData/GitHub/AI-Platform-Square-HB
make venv
make backend-install
make frontend-install
cp backend/.env.example backend/.env
make db-up
cd backend && PYTHONPATH=. ../.venv/bin/alembic upgrade head
cd backend && PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
cd ..
make backend-dev
```

新开一个终端：

```bash
cd /home/ctyun/BigData/GitHub/AI-Platform-Square-HB
make frontend-dev
```

### 2.2 远程 MySQL

1. 将 `DATABASE_URL` 指向远程 MySQL 服务。
2. 目标库必须是空库或由本项目独占的新库。
3. 在开发机执行：
   ```bash
   make frontend-install
   make frontend-build
   make release-bundle
   ```
4. 将发布包传到部署主机并解压；发布包必须已包含 `frontend/dist`。
5. 在部署主机执行：
   ```bash
   make venv
   make backend-install
   cd backend
   PYTHONPATH=. ../.venv/bin/alembic upgrade head
   PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
   ```
6. 回到仓库根目录执行：
   ```bash
   make app-run
   ```
7. 验证：
   - `http://<host>:${APP_PORT:-80}`
   - `http://<host>:${APP_PORT:-80}/api/health`

最短命令清单：

开发机：

```bash
cd /home/ctyun/BigData/GitHub/AI-Platform-Square-HB
make frontend-install
make frontend-build
make release-bundle
```

部署主机：

```bash
cd /home/ctyun/BigData/GitHub/AI-Platform-Square-HB
make venv
make backend-install
cp backend/.env.example backend/.env
```

编辑 `backend/.env` 后执行：

```bash
cd /home/ctyun/BigData/GitHub/AI-Platform-Square-HB/backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
cd ..
make app-run
```

## 2.3 端口规则

- `APP_PORT`：准生产对外单端口，默认 `80`
- `BACKEND_DEV_PORT`：后端开发端口，默认 `8000`
- `FRONTEND_DEV_PORT`：前端开发端口，默认 `5173`
- `VITE_API_BASE_URL`：开发态前端代理目标；未配置时默认指向 `http://127.0.0.1:${BACKEND_DEV_PORT}`

旧 `.env.local` 迁移步骤：

1. 将原 `.env.local` 中仍需保留的应用变量迁移到 `backend/.env`
2. 根目录 `.env` 仅保留 MySQL Compose 变量
3. 删除根目录 `.env.local`

## 3. 测试数据库

- `TEST_DATABASE_URL` 仅供测试使用，必须指向独立测试库。
- `scripts/backend_test.sh` 会优先使用 `TEST_DATABASE_URL`。
- 默认本地测试地址：
  - `mysql+pymysql://ai_app_user:ai_app_password@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4`

## 4. 迁移规则

- 结构变更只允许通过 Alembic revision 管理。
- 运行时代码不允许再通过 `create_all()`、启动补字段或手写 SQL DDL 偷偷修库。
- 禁止把“兼容未知已有库状态”作为默认部署路径。
- 若库已初始化过且修改了 `USER_DEFAULT_PASSWORD` / `ADMIN_DEFAULT_PASSWORD`，需显式执行 `cd backend && PYTHONPATH=. ../.venv/bin/python -m app.bootstrap reset-default-users`；`init-base` 不会覆盖已有默认账号密码。
- PR 描述中必须写明：
  - 变更了哪些 Alembic revision；
  - 是否需要执行 `init-base` 或 `seed-demo`；
  - MySQL 下的验证结果摘要。
