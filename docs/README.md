# Docs README

审计覆盖与数据库初始化顺序请以根目录 `README.md` 为准（含 001 + 002 + 003 迁移说明）。

## Phase-4 PR-D 回归测试（口径锁定）

在仓库根目录执行：`PYTHONPATH=backend pytest -q backend/tests/test_ranking_consistency.py backend/tests/test_phase4_regression_lock.py`。
