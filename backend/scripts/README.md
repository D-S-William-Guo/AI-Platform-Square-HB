# Backend Scripts

当前脚本集只保留 MySQL / ORM / 发布运行主链路相关工具。

## 运行与发布

- `../../scripts/app_serve.sh`
  - 本机构建前端并单端口启动，适合开发机全量验证。
- `../../scripts/app_run.sh`
  - 远程运行时入口；要求发布物已包含 `frontend/dist`。
- `../../scripts/release_bundle.sh`
  - 在开发机打包包含 `frontend/dist` 的发布包。

## systemd 运维

- `../../scripts/service_install.sh`
- `../../scripts/service_start.sh`
- `../../scripts/service_stop.sh`
- `../../scripts/service_restart.sh`
- `../../scripts/service_status.sh`
- `../../scripts/service_logs.sh`
- `../../scripts/service_uninstall.sh`

## 数据库初始化与同步

```bash
cd backend
alembic upgrade head
python -m app.bootstrap init-base
python -m app.bootstrap reset-default-users
python -m app.bootstrap sync-system-presets
# 仅开发/演示需要时：
python -m app.bootstrap seed-demo
```

## 开发辅助

- `dedupe_data.py`
  - 基于 SQLAlchemy 的数据去重工具。
- `test_sync.py`
  - 针对本地运行中的 HTTP 接口做简单同步调试。
- `dev/doctor.sh`
  - MySQL 环境诊断与后端测试入口。
- `dev/bootstrap_venv.sh`
  - 在仓库根目录创建 `.venv` 并安装依赖。
