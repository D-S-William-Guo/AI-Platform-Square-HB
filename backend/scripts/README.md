# Backend Scripts

当前脚本集只保留 MySQL / ORM 主链路相关工具。

## 保留脚本

- `dedupe_data.py`
  - 基于 SQLAlchemy 的数据去重工具。
- `test_sync.py`
  - 针对本地运行中的 HTTP 接口做简单同步调试。
- `dev/doctor.sh`
  - MySQL 环境诊断与后端测试入口。
- `dev/bootstrap_venv.sh`
  - 在仓库根目录创建 `.venv` 并安装依赖。

## 初始化命令

数据库初始化不再通过脚本直接建表，统一改为：

```bash
cd backend
alembic upgrade head
python -m app.bootstrap init-base
# 仅开发/演示需要时：
python -m app.bootstrap seed-demo
```
