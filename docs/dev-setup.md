# Backend 开发环境与自检（Linux / Windows / Codex 通用）

本文档解决三个问题：

1. 如何在本地/云电脑把后端 Python 环境标准化（可复现）
2. 如何一键做"环境自检"（避免 `ModuleNotFoundError: app` 等问题反复出现）
3. 如何在 PR/CI 里保证同一套规则持续生效

---

## 1. 约定与原则（必须读一遍）

- 后端目录为 `backend/`，Python 包为 `app/`
- 仓库统一使用根目录 `.venv`
- 后端以 **editable install（`pip install -e .`）** 的方式安装，避免依赖 `PYTHONPATH`
- CI 与本地开发使用同一条导入路径规则：`import app` 必须稳定可用
- 数据库只支持 MySQL，结构迁移统一走 Alembic
- 准生产交付形态为“前端静态构建 + 后端单端口同源托管”

---

## 2. 快速开始（Linux / Ubuntu）

在仓库根目录执行：

```bash
bash backend/scripts/dev/bootstrap_venv.sh
```

> 该脚本会创建/复用 venv，并安装依赖与 editable 包。

首次完成后，继续执行：

```bash
cp backend/.env.example backend/.env
make db-up
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
```

开发调试端口可通过以下变量覆盖：

```bash
export APP_HOST=0.0.0.0
export BACKEND_DEV_PORT=8000
export FRONTEND_DEV_PORT=5173
export VITE_API_BASE_URL="http://127.0.0.1:${BACKEND_DEV_PORT}"
```

---

## 3. 快速开始（Windows / PowerShell）

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\dev\bootstrap_venv.ps1
```

> 该脚本会创建/复用 venv，并安装依赖与 editable 包。

---

## 4. 环境自检（强烈建议：每次提交前跑一次）

### 4.1 Linux / Ubuntu

在仓库根目录执行：

```bash
bash backend/scripts/dev/doctor.sh
```

### 4.2 Windows / PowerShell

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\dev\doctor.ps1
```

### 4.3 自检会检查什么？

- Python / pip 是否可用
- 是否在 venv 中（提示项）
- `import app` 是否成功（核心）
- 依赖健康度（`pip check`）
- 测试数据库迁移与初始化（MySQL）
- `python -m pytest -q tests` 是否通过

---

## 5. 常见问题

### Q1：本地跑 pytest 报 `ModuleNotFoundError: No module named 'app'`

**原因**：当前环境没有把 `backend/app` 作为可导入包安装。

**解决**（二选一，推荐 A）：

**A. 推荐：在仓库根目录执行标准安装**

```bash
make backend-install
```

**B. 临时：用 PYTHONPATH**（仅用于救急，不建议长期依赖）

```bash
cd backend
PYTHONPATH="$(pwd)" python -m pytest -q tests
```

---

### Q2：CI 里为什么不再用 PYTHONPATH？

`PYTHONPATH` 属于"运行时补丁"，容易被不同 shell/IDE/工作目录影响。editable install 属于"工程级解决方案"，本地、CI、Codex 执行一致，减少漂移。

---

## 6. PR 提交流程（与 CI 对齐）

提交 PR 前建议顺序：

1. `bash backend/scripts/dev/doctor.sh`（或 Windows `doctor.ps1`）
2. `python -m pytest -q tests`（doctor 已包含，可略）
3. `npm run build`（确认前端构建可用于单端口同源部署）
4. push 分支 → 开 PR → 等 CI 绿 → squash merge

---

## 7. 索引

- 开发流程说明：`docs/dev-workflow.md`
- 治理规则：`docs/GOVERNANCE.md`

---
