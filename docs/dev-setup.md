# Backend 开发环境与自检（Linux / Windows / Codex 通用）

本文档解决三个问题：

1. 如何在本地/云电脑把后端 Python 环境标准化（可复现）
2. 如何一键做"环境自检"（避免 `ModuleNotFoundError: app` 等问题反复出现）
3. 如何在 PR/CI 里保证同一套规则持续生效

---

## 1. 约定与原则（必须读一遍）

- 后端目录为 `backend/`，Python 包为 `app/`
- 后端以 **editable install（`pip install -e .`）** 的方式安装，避免依赖 `PYTHONPATH`
- CI 与本地开发使用同一条导入路径规则：`import app` 必须稳定可用

---

## 2. 快速开始（Linux / Ubuntu）

在仓库根目录执行：

```bash
bash backend/scripts/dev/bootstrap_venv.sh
```

> 该脚本会创建/复用 venv，并安装依赖与 editable 包。

---

## 3. 快速开始（Windows / PowerShell）

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\dev\bootstrap_venv.ps1
```

> 若你项目里没有 `bootstrap_venv.ps1`，则使用手工方式：
>
> - 创建 venv
> - `pip install -r backend/requirements.txt`
> - `pip install -e backend`

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
- 测试数据库初始化（SQLite）
- `pytest -q tests` 是否通过

---

## 5. 常见问题

### Q1：本地跑 pytest 报 `ModuleNotFoundError: No module named 'app'`

**原因**：当前环境没有把 `backend/app` 作为可导入包安装。

**解决**（二选一，推荐 A）：

**A. 推荐：在 `backend/` 里执行 editable install**

```bash
cd backend
python -m pip install -e .
```

**B. 临时：用 PYTHONPATH**（仅用于救急，不建议长期依赖）

```bash
cd backend
PYTHONPATH="$(pwd)" pytest -q tests
```

---

### Q2：CI 里为什么不再用 PYTHONPATH？

`PYTHONPATH` 属于"运行时补丁"，容易被不同 shell/IDE/工作目录影响。editable install 属于"工程级解决方案"，本地、CI、Codex 执行一致，减少漂移。

---

## 6. PR 提交流程（与 CI 对齐）

提交 PR 前建议顺序：

1. `bash backend/scripts/dev/doctor.sh`（或 Windows `doctor.ps1`）
2. `pytest -q tests`（doctor 已包含，可略）
3. push 分支 → 开 PR → 等 CI 绿 → squash merge

---

## 7. 索引

- 开发流程说明：`docs/dev-workflow.md`
- 治理规则：`docs/GOVERNANCE.md`

---
