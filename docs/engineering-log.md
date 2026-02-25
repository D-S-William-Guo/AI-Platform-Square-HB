## Phase-4

### PR-A
- PR: #42
- Branch: fix/phase4-pr-a-migrations-align
- Commit: 2a11391
- Summary: 对齐数据库基础结构与 Phase-4 后续能力的模型基线。
- Verified: 001 初始化可执行。

### PR-B
- PR: #44
- Branch: feat/phase4-pr-b-run-id-publish
- Commit: a677549
- Summary: 引入 HistoricalRanking 的 run_id 发布机制并保持兼容读取。
- Verified: sync/读取链路可用。

### PR-C
- PR: #46
- Branch: chore/phase4-pr-c-audit-coverage
- Commit: 9e577f3
- Summary: 补齐 HistoricalRanking 最小审计覆盖并落地 003 迁移。
- Verified: 审计记录可写。

### PR-D
- PR: #48
- Branch: test/phase4-pr-d-regression-lock
- Commit: e1d7044
- Summary: 锁定 Phase-4 回归口径（分数夹取、排序稳定、run_id 选择）。
- Verified: 回归测试通过。
