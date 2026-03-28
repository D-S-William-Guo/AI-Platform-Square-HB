# AUDIT REPORT（治理规则对照审计）

## 审计范围
- 代码层：`backend/app/main.py`、`backend/app/models.py`、`backend/app/schemas.py`、`backend/app/seed.py`
- 文档层：`README.md`（新增治理摘要）与 `docs/GOVERNANCE.md`（本次定版）
- 审计基线：已冻结的 5 条治理规则

## 现状与规则对照表

| 规则 | 当前实现位置（文件 + 函数/模型） | 审计结论 |
|---|---|---|
| 1) 省内应用展示以 App 为准，独立于榜单 | `backend/app/main.py::list_apps`；`backend/app/models.py::App.section` | **部分符合**：主路径按 `App` 查询；但异常兜底 SQL 分支忽略 `section/status/category/q` 筛选，导致语义可能偏离。 |
| 2) 审批通过 submission 同时创建 AppRankingSetting 且默认禁用 | `backend/app/main.py::approve_submission_and_create_app`；`backend/app/seed.py::approve_submission_and_create_app`；`backend/app/models.py::AppRankingSetting.is_enabled` | **不符合**：审批流程仅创建 `App`，未创建 `AppRankingSetting`；且 `AppRankingSetting.is_enabled` 当前默认 `True`。 |
| 3) 榜单唯一真相源为 AppRankingSetting | `backend/app/main.py::sync_rankings_service`；`backend/app/seed.py::sync_rankings` | **部分符合**：同步计算已基于 `AppRankingSetting.is_enabled`；但 `App/Submission` 仍暴露大量 `ranking_*` 读写接口，边界易混淆。 |
| 4) 榜单结果为周期快照 HistoricalRanking，并明确周期口径 | `backend/app/main.py::list_rankings`、`list_historical_rankings`、`sync_rankings_service`；`backend/app/models.py::HistoricalRanking` | **部分符合**：对外榜单读取走 `HistoricalRanking`；但周期口径（周/双周/月）未落地到代码/文档约束，当前以 `today` 写入，缺乏治理定义。 |
| 5) 首版对外仅展示四类能力，管理能力仅管理员可见且后端受保护 | `backend/app/main.py` 中 ranking-dimensions/ranking-configs/ranking-settings/手工调分/批量更新等接口；`create_group_app` | **不符合**：除 `admin/group-apps` 外，大多数管理接口无权限保护；且 `admin/group-apps` 使用硬编码 query token，治理强度不足。 |

## 发现的问题（按风险排序）

### P0（高风险）
1. **审批后未自动初始化参评设置，且默认启用策略与规则冲突。**
   - 影响：无法保证“先审批入库，再管理员二次开启参评”的治理流程。
   - 涉及：`approve_submission_and_create_app`（API 与 seed helper），`AppRankingSetting.is_enabled` 默认值。

2. **管理接口普遍缺少权限保护。**
   - 影响：任何调用方可直接修改维度、榜单配置、参评设置、分数，破坏治理与数据可信度。
   - 涉及：`/ranking-dimensions*`、`/ranking-configs*`、`/apps/*/ranking-settings*`、`/rankings/sync`、`/apps/batch-update-ranking-params`、`/apps/{app_id}/dimension-scores/{dimension_id}` 等。

### P1（中风险）
3. **唯一真相源边界不清：`App/Submission.ranking_*` 仍可被更新并可能被误解为参评控制字段。**
   - 影响：未来维护易出现“多真相源”回归。
   - 涉及：`update_app_ranking_params`、`batch_update_ranking_params`、`SubmissionCreate`/`SubmissionOut`/`AppDetail` 的 `ranking_*` 字段暴露。

4. **榜单周期口径未治理化。**
   - 影响：快照虽存在，但“周/双周/月”的口径不可验证，审计口径不一致。
   - 涉及：`sync_rankings_service` 使用 `today` 直接写入 `HistoricalRanking.period_date`。

### P2（低风险）
5. **`list_apps` 异常兜底 SQL 分支忽略筛选条件，和“以 App 展示且可筛选”语义不完全一致。**
   - 影响：异常场景下返回集合可能超出调用者预期。

## 建议的最小修复 PR 列表

### PR-1（治理主修复，优先级最高）
- 在审批通过流程中（API + seed helper）执行：
  1) 创建 `App`；
  2) 按现有双榜单配置创建 `AppRankingSetting`；
  3) `is_enabled=false`（默认禁用）；
  4) 保持事务一致性。
- 调整 `AppRankingSetting` 模型与 schema 默认值为 `False`（仅默认，不改变接口形态）。

### PR-2（权限收敛）
- 为所有管理类接口补充统一管理员鉴权依赖（复用现有最小机制即可，不新增配置系统）。
- 对外公开接口仅保留：应用展示、榜单读取、申报入口、基础统计/规则链接。

### PR-3（真相源与周期口径固化）
- 在代码注释与接口文档中明确：`App/Submission.ranking_*` 为兼容字段，不作为参评判定。
- 在榜单快照生成处固化周期函数（至少周口径），并将 `period_date` 写入该周期锚点日期。
- 修复 `list_apps` SQL fallback 的筛选一致性（最小改动：移除 fallback 或补齐筛选条件）。

## 结论
当前实现已经具备三层榜单框架和历史快照基础，但与冻结治理规则相比，仍存在“审批后默认参评、管理接口未受保护、周期口径未定版”三类核心偏差。建议按 PR-1 → PR-2 → PR-3 顺序以最小改动闭环。
