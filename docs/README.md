# Docs README

## Phase-4 PR-C：审计覆盖（最小说明）

本次补齐了影响 `HistoricalRanking` 真相源链路的审计记录，覆盖：
- 榜单发布：`POST /api/rankings/sync`
- 维度配置写操作：`POST/PUT/DELETE /api/ranking-dimensions`
- 榜单配置写操作：`POST/PUT/DELETE /api/ranking-configs`
- 应用参与配置写操作：`POST/PUT/DELETE /api/apps/{app_id}/ranking-settings/{setting_id}`

审计记录落表：`ranking_audit_logs`，关键字段：
- `action`：动作类型
- `ranking_type` / `ranking_config_id`：榜单类型或配置标识
- `period_date`：生效日期（发布周期）
- `run_id`：发布批次（仅发布时有值）
- `actor`：操作人（当前为 `system`）
- `created_at`：记录时间
- `payload_summary`：简要变更摘要
