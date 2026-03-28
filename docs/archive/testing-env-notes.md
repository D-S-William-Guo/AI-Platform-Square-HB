# 依赖安装与测试环境说明

> 说明：本文件仅保留网络受限场景的背景说明。当前项目默认口径是“前端在开发链路预构建，远程环境不再执行 npm 安装或前端构建”，请优先以 `README.md`、`docs/dev-setup.md` 与 `scripts/backend_test.sh` 为准。

## 当前现象

- `pip install -r backend/requirements.txt` 通过代理拉取 PyPI 时返回 403。
- 取消代理后，外网 `pypi.org` 网络不可达（`Network is unreachable`）。
- 受限网络环境不适合作为前端构建机。

## 结论

该环境属于“网络/镜像受限”的基础设施问题，不是项目代码本身问题。当前正式方案已经避免在远程部署环境执行前端构建。

## 建议的完善方案（可执行优先级）

1. **开发链路预构建前端（当前正式方案）**
   - 在开发机执行 `make frontend-build`
   - 通过 `make release-bundle` 产出包含 `frontend/dist` 的发布包
   - 远程环境只部署运行时产物
2. **公司内网镜像源（可选补充）**
   - Python: 配置内部 PyPI mirror（如 Artifactory / Nexus）
3. **容器化统一构建**
   - 使用公司允许的基础镜像，镜像内预置依赖

## 当前标准验证链路

- 后端测试：`make backend-test`
- 前端开发：`make frontend-dev`
- 数据库迁移：`cd backend && PYTHONPATH=. ../.venv/bin/alembic upgrade head`
- 基础初始化：`cd backend && PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base`
