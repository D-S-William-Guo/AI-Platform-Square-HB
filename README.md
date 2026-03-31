# AI-Platform-Square-HB

企业内部 AI 应用广场，当前基线为：

- 后端：FastAPI + SQLAlchemy ORM + Alembic
- 数据库：MySQL 5.7
- 前端：React + TypeScript + Vite
- 部署：开发机构建前端静态产物，远程主机只负责运行

## 当前产品口径

- 首页对外聚焦：集团应用、省内应用、双榜单、申报入口。
- 双榜单固定为：
  - `excellent`：总应用榜
  - `trend`：增长趋势榜
- 默认系统榜单维度：
  - 总应用榜：用户满意度、业务价值、使用活跃度、稳定性和安全性
  - 增长趋势榜：使用活跃度、增长趋势、用户增长
- 系统预置维度和系统榜单默认权重统一为 `1.0`。
- 当前登录默认仍为本地账号；OA / 第三方统一登录采用预留模式，不在这一轮直接接真实系统。

## 环境文件

应用只认一个运行时配置文件：

- [backend/.env](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/backend/.env)：唯一应用配置源
- [backend/.env.example](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/backend/.env.example)：模板

根目录 `.env` 只给 Docker Compose MySQL 覆盖用，不要放应用配置。

最关键配置项：

```env
DATABASE_URL=mysql+pymysql://ai_app_user:ai_app_password@127.0.0.1:13306/ai_app_square?charset=utf8mb4
ENVIRONMENT=development

APP_HOST=0.0.0.0
APP_PORT=80
BACKEND_DEV_PORT=8000
FRONTEND_DEV_PORT=5173
VITE_API_BASE_URL=http://127.0.0.1:8000

AUTH_PROVIDER_MODE=local
OA_SSO_LOGIN_URL=
EXTERNAL_SSO_LOGIN_URL=
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
ALLOWED_HOSTS=127.0.0.1,localhost,testserver
# AUTH_COOKIE_SECURE=false
# ENABLE_API_DOCS=false

USER_DEFAULT_PASSWORD=ChangeMe_User_123!
ADMIN_DEFAULT_PASSWORD=ChangeMe_Admin_123!
```

生产环境后端依赖安装默认走内网 pip 源：

```env
PIP_INDEX_URL_PRODUCTION=http://136.142.12.68/simple/
PIP_TRUSTED_HOST_PRODUCTION=136.142.12.68
```

轻量安全基线：

- 前端默认只依赖 `HttpOnly` Cookie 会话，不再把登录 token 持久化到浏览器 `localStorage`
- 生产环境默认关闭 API docs；只有显式设置 `ENABLE_API_DOCS=true` 才会开启
- 生产环境请显式配置：
  - `ALLOWED_ORIGINS`
  - `ALLOWED_HOSTS`
- 纯内网 HTTP 主机如暂时没有 HTTPS 终止层，可显式设置 `AUTH_COOKIE_SECURE=false`，避免生产环境 `Secure` Cookie 无法回传
- 图片和文档上传默认要求已登录用户访问

## 本地开发最短命令

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

日常启动：

```bash
make db-up
make backend-dev
make frontend-dev
```

## 发布与远程部署

### 1. 开发机打包发布物

```bash
git checkout main
git pull origin main
make frontend-install
make frontend-build
make release-bundle
```

发布包会生成到 `release/`，其中已包含 `frontend/dist`。

### 2. 远程主机部署

远程主机不再需要 Node/npm，只需要 Python 3.10+、`make` 和数据库连通能力。

```bash
mkdir -p ~/AI-Platform-Square-HB
cd ~/AI-Platform-Square-HB
tar -xzf /上传路径/ai-platform-square-hb-*.tar.gz
cp backend/.env.example backend/.env
make venv
make backend-install
make app-run
```

`make app-run` 会自动执行：

- 校验 `frontend/dist/index.html`
- `alembic upgrade head`
- `python -m app.bootstrap init-base`
- 启动单端口服务

健康检查：

```bash
curl http://127.0.0.1:${APP_PORT:-8080}/api/health
```

## 正式服务管理

生产主机正式方案统一走 `systemd`，服务名默认是 `ai-platform-square`。

安装服务：

```bash
make service-install
```

常用运维命令：

```bash
make service-start
make service-stop
make service-restart
make service-status
make service-logs
make service-uninstall
```

说明：

- `service-install` 会把 [ai-platform-square.service](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/deploy/systemd/ai-platform-square.service) 安装到 `/etc/systemd/system/`
- `ExecStart` 最终执行的是 [app_run.sh](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/scripts/app_run.sh)
- `nohup make app-run` 只建议用于临时排障

## 数据库运维口径

当前数据库只支持三条正式运维路径：

### 1. 结构升级

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
```

### 2. 基础初始化

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
```

用途：

- 新库写入默认账号
- 初始化系统维度
- 初始化系统榜单配置

`init-base` 是幂等的，但**不会覆盖**已有默认账号密码，也**不会覆盖**已有系统榜单预置。

### 3. 默认账号重置

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap reset-default-users
```

用途：

- 显式重置 `zhangsan` / `lisi`
- 当你修改了 `USER_DEFAULT_PASSWORD` / `ADMIN_DEFAULT_PASSWORD` 后，必须手工执行这条

### 4. 系统预置同步

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap sync-system-presets
```

用途：

- 将系统内置维度和系统榜单配置同步到当前代码默认值
- 会更新：
  - 系统维度
  - `excellent`
  - `trend`
- 不会碰：
  - 自定义榜单
  - 自定义维度
  - 业务应用和榜单历史数据

### 5. 高风险例外路径

整库清空 / 整库重建不是常规运维命令，只能作为 DBA 或人工操作的例外方案。默认部署策略始终是“保留数据优先”。

## 登录与身份模式

身份模式通过 `AUTH_PROVIDER_MODE` 控制：

- `local`：当前默认，本地账号登录
- `oa`：预留 OA 统一登录入口
- `external_sso`：预留第三方统一登录入口

当前行为：

- `local`：登录页显示用户名/密码表单
- `oa` / `external_sso`：登录页切换为统一登录提示与外部入口按钮
- 如果外部入口未配置，前后端都会返回明确的“未配置”提示，而不是半工作状态

当前轮次只做架构预留，不直接打通 OA / 第三方协议。

## 排障速记

默认账号密码改了但登录不生效：

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap reset-default-users
```

系统榜单、维度还是旧权重/旧名字：

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap sync-system-presets
```

服务启动失败先看日志：

```bash
make service-logs
```

## 文档入口

当前有效文档只看这几个：

- [README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/README.md)
- [docs/README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/README.md)
- [docs/dev-setup.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/dev-setup.md)
- [docs/db-migration-sop.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/db-migration-sop.md)
- [docs/dev-workflow.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/dev-workflow.md)
- [docs/GOVERNANCE.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/GOVERNANCE.md)

历史审计、阶段性对齐稿和旧设计稿统一放到 `docs/archive/`，只用于追溯，不再作为主入口。
