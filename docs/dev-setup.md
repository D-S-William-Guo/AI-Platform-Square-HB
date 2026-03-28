# 本地开发环境

## 前置条件

- Python 3.10+
- Node 18+（推荐 20 LTS）
- Docker + Docker Compose
- MySQL 5.7（本地通过 Compose）

## 最短启动命令

首次启动：

```bash
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

第二个终端：

```bash
make frontend-dev
```

## 常用命令

```bash
make venv
make backend-install
make frontend-install
make backend-dev
make frontend-dev
make backend-test
make frontend-build
make release-bundle
make db-up
make db-down
```

## 环境说明

- `backend/.env` 是唯一应用配置源
- 根目录 `.env` 只用于 Docker Compose MySQL 覆盖
- 生产环境 pip 源配置虽然可以写在 `backend/.env`，但本地开发默认仍走外网 PyPI

## 数据库初始化

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
```

如果你修改了默认密码：

```bash
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap reset-default-users
```

如果你要把旧库同步到新的系统榜单/维度默认值：

```bash
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap sync-system-presets
```
