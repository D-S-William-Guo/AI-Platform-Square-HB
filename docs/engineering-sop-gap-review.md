# 工程化审阅 / SOP 差距清单（最小可落地）

> 审阅范围：repo root / backend / frontend 的工程化机制、脚本、文档、CI、模板。

## 1) 现有机制清单

### A. repo root

- CI：`.github/workflows/ci.yml`
  - backend job：安装 `requirements.txt` + `pip install -e .` 后执行 `pytest -q tests`
  - frontend job：`npm ci|npm install` 后执行 `npm run build`
- PR 模板：
  - `.github/pull_request_template.md`（包含 doctor 检查项）
  - `.github/PULL_REQUEST_TEMPLATE.md`（另一套模板，不含 doctor）
- 主文档入口：`README.md`（含快速启动、迁移说明、开发文档索引）
- 开发流程文档：`docs/dev-workflow.md`（分支流程、DB 切换）
- 开发环境文档：`docs/dev-setup.md`（doctor、自检、editable install）

### B. backend

- Python 工程化：`backend/pyproject.toml`（已支持 editable install）
- 依赖：`backend/requirements.txt`
- 环境自检脚本：
  - Linux：`backend/scripts/dev/doctor.sh`
  - Windows：`backend/scripts/dev/doctor.ps1`
- 测试：`backend/tests/*`
- 迁移：当前已收敛为 `backend/alembic/` 下的 Alembic revision

### C. frontend

- 标准脚本：`frontend/package.json`
  - `dev` / `build` / `preview`
  - `verify:styles`（build + preview）
- 锁文件：`frontend/package-lock.json`
- 构建配置：`vite.config.ts` / `tsconfig.json`

---

## 2) Gap List（含现象 / 风险 / 最小修复建议）

### Gap-1（P0）：Linux/Windows doctor 行为不一致，Windows 仍直接用 `pytest`

- 现象：
  - Linux `doctor.sh` 使用 `${PY_CMD} -m pytest -q tests`
  - Windows `doctor.ps1` 使用 `pytest -q tests`（依赖 PATH/venv 状态）
- 风险：
  - Windows 本地容易出现“命令可执行但解释器不一致”的隐性漂移，导致本地通过/CI 失败。
- 最小修复建议（单 PR 可完成）：
  1. `backend/scripts/dev/doctor.ps1`
     - 将 `pytest -q tests` 改为 `python -m pytest -q tests`
     - 对齐 Linux 的执行语义。
  2. `docs/dev-setup.md`
     - 在“自检会检查什么”补一条“统一通过 `python -m pytest` 运行测试”。

### Gap-2（P0）：`docs/dev-setup.md` 引用了不存在的 bootstrap 脚本

- 现象：
  - 文档要求执行：
    - `backend/scripts/dev/bootstrap_venv.sh`
    - `backend/scripts/dev/bootstrap_venv.ps1`
  - 仓库中实际不存在上述文件。
- 风险：
  - 新同学按文档执行即失败，首屏体验差；会绕回“手工命令版本漂移”。
- 最小修复建议（单 PR 可完成，二选一）：
  1. 补齐两个 bootstrap 脚本（推荐，10~30 行即可），仅做：创建 venv + 安装 requirements + `pip install -e .`。
  2. 若暂不提供脚本，则删除文档中的脚本入口，改为明确手工命令（Linux/Windows 各一段）。

### Gap-3（P1）：PR 模板存在双版本且标准不一致

- 现象：`.github/pull_request_template.md` 与 `.github/PULL_REQUEST_TEMPLATE.md` 并存，字段与 checklist 不一致。
- 风险：
  - 提交者随机命中不同模板，导致审阅标准不统一（doctor、迁移检查、frontend build 等可能漏填）。
- 最小修复建议（单 PR 可完成）：
  1. 保留一份模板（建议保留包含 doctor 的 `.github/pull_request_template.md`）。
  2. 删除或重定向另一份模板内容，避免分叉。
  3. 在唯一模板中补齐关键检查项：doctor、backend pytest、frontend build、迁移变更说明、文档/变更记录更新。

### Gap-4（P1）：CI 与本地入口存在轻微偏差（是否统一使用模块方式）

- 现象：CI backend 目前执行 `pytest -q tests`，doctor 使用 `python -m pytest -q tests`。
- 风险：
  - 少量环境下 `pytest` 命令入口与解释器绑定不一致，产生“本地/CI 行为差异”排查成本。
- 最小修复建议（单 PR 可完成）：
  1. `.github/workflows/ci.yml` backend 测试命令改为 `python -m pytest -q tests`。
  2. `docs/dev-setup.md` 和 README 的测试示例统一使用模块方式。

### Gap-5（P1）：数据库迁移 SOP 的“唯一真相源”分散在多文档，且 README 有重复段落

- 现象：
  - 迁移顺序信息分布在 README、dev-workflow、其他治理文档。
  - README 存在“后端目录配置 + 健康检查”重复段落，维护成本高。
- 风险：
  - 文档演进时容易出现顺序不一致；阅读路径冗长，团队成员执行步骤不统一。
- 最小修复建议（单 PR 可完成）：
  1. 新增 `docs/db-migration-sop.md`，明确唯一执行顺序与 MySQL 迁移入口。
  2. README 仅保留“短入口 + 链接”，删除重复块。
  3. `docs/dev-workflow.md` 改为引用该 SOP 文件，避免多处维护。

### Gap-6（P2）：基础 hygiene 文件缺失（.editorconfig / CONTRIBUTING）

- 现象：根目录缺少 `.editorconfig`、`CONTRIBUTING.md`（issue template/pre-commit 也尚未建立）。
- 风险：
  - 编辑器换行/缩进风格与协作入口约定不统一，长周期会放大 PR 噪音。
- 最小修复建议（单 PR 可完成）：
  1. 新增 `.editorconfig`（UTF-8、LF、2/4 空格策略按现状配置）。
  2. 新增 `CONTRIBUTING.md`（引用 doctor、pytest、frontend build、PR checklist）。
  3. pre-commit 可先不引入，仅在文档中给“可选建议”。

---

## 3) 优先级汇总

- P0
  - Gap-1：doctor 脚本 Linux/Windows 语义不一致
  - Gap-2：dev-setup 引用了不存在脚本
- P1
  - Gap-3：PR 模板双版本不一致
  - Gap-4：CI 与本地测试命令入口不完全统一
  - Gap-5：迁移 SOP 真相源分散 + README 重复
- P2
  - Gap-6：hygiene 文件缺失（.editorconfig / CONTRIBUTING）

---

## 4) 建议 PR 拆分计划（最小补丁、可验证）

### PR-1（先做，P0）
- 标题：`chore(devx): unify doctor behavior across linux/windows and fix setup doc`
- 改动范围：
  - `backend/scripts/dev/doctor.ps1`（`pytest` -> `python -m pytest`）
  - `docs/dev-setup.md`（修正文档中 bootstrap 描述，确保与仓库一致）
  - 可选新增：`backend/scripts/dev/bootstrap_venv.sh`、`backend/scripts/dev/bootstrap_venv.ps1`
- 验收方式：
  - Linux：`bash backend/scripts/dev/doctor.sh`
  - Windows：`powershell -ExecutionPolicy Bypass -File backend\scripts\dev\doctor.ps1`

### PR-2（P1）
- 标题：`chore(ci): align backend test command with local doctor`
- 改动范围：
  - `.github/workflows/ci.yml`（backend test 改为 `python -m pytest -q tests`）
  - 文档示例同步（`docs/dev-setup.md` / `README.md`）
- 验收方式：
  - 本地：`cd backend && python -m pytest -q tests`
  - CI：PR 检查通过

### PR-3（P1）
- 标题：`docs(process): consolidate PR template and migration SOP entry`
- 改动范围：
  - 统一 PR 模板（仅保留一个）
  - 新增 `docs/db-migration-sop.md`
  - README / `docs/dev-workflow.md` 改为“短说明 + 指向 SOP”
- 验收方式：
  - 手工检查：新 PR 页面模板唯一且包含 doctor / pytest / frontend build / migration
  - 文档链路检查：README 与 dev-workflow 均能跳转到同一 SOP

### PR-4（P2，可并入 PR-3）
- 标题：`docs(hygiene): add editorconfig and contributing guide`
- 改动范围：`.editorconfig`、`CONTRIBUTING.md`
- 验收方式：
  - `git diff --check` 无格式告警
  - 新贡献者可按 CONTRIBUTING 一次跑通 doctor + build + pytest
