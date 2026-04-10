# AI-Platform-Square-HB

企业内部 AI 应用广场，当前基线：

- 后端：FastAPI + SQLAlchemy ORM + Alembic
- 数据库：MySQL 5.7
- 前端：React + TypeScript + Vite
- 部署：开发机构建前端静态产物，远程主机只负责运行发布物

## 当前产品口径

- 首页对外聚焦：集团应用、省内应用、双榜单、申报入口
- 双榜单固定为：
  - `excellent`：总应用榜
  - `trend`：增长趋势榜
- 默认身份模式：`local`
- 当前只做统一身份适配层预留，不直接接真实 OA / 第三方协议
- 榜单参与与控制输入真相源：`AppRankingSetting`
- 对外榜单读取真相源：`HistoricalRanking`

更完整的治理结论见 [docs/GOVERNANCE.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/GOVERNANCE.md)。

## 环境文件

应用只认一个运行时配置文件：

- [backend/.env](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/backend/.env)
- [backend/.env.example](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/backend/.env.example)

根目录 `.env` 只用于 Docker Compose MySQL 覆盖，不要放应用配置。

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

完整开发说明见 [docs/dev-setup.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/dev-setup.md)。

## 发布与运维入口

开发机打包发布物：

```bash
make frontend-build
make release-bundle
```

远程主机启动：

```bash
make venv
make backend-install
make app-run
```

正式服务常用命令：

```bash
make service-install
make service-start
make service-restart
make service-status
make service-logs
```

详细发布流程见 [docs/dev-workflow.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/dev-workflow.md)。

## 数据库运维入口

当前正式命令只看这几类：

- 结构升级：`alembic upgrade head`
- 基础初始化：`python -m app.bootstrap init-base`
- 默认账号重置：`python -m app.bootstrap reset-default-users`
- 系统预置同步：`python -m app.bootstrap sync-system-presets`

完整命令、顺序和适用场景见 [docs/db-migration-sop.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/db-migration-sop.md)。

## 当前文档治理状态

当前只认以下文档为有效入口：

- [README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/README.md)
- [AGENTS.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/AGENTS.md)
- [docs/README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/README.md)
- [docs/dev-setup.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/dev-setup.md)
- [docs/db-migration-sop.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/db-migration-sop.md)
- [docs/dev-workflow.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/dev-workflow.md)
- [docs/GOVERNANCE.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/GOVERNANCE.md)

以下内容仅供追溯，不作为当前规则入口：

- `docs/archive/`
- `backend/scripts/README.md`
- 任何未在 `docs/README.md` 登记的临时说明文档

## 给智能体的入口提示

如果你是智能体工具，进入仓库后优先阅读：

1. [AGENTS.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/AGENTS.md)
2. [docs/README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/README.md)
3. [docs/GOVERNANCE.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/GOVERNANCE.md)

不要从 `docs/archive/` 或脚本说明文档推断当前实现口径。
