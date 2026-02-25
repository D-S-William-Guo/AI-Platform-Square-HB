# MILESTONE Phase-1 ~ Phase-3（Baseline Summary）

> 目的：归档 Phase-1 ~ Phase-3 已完成治理动作（仅记录已实现事实）。

## Phase-1（治理基线冻结）

1. 已形成一期治理定版文档，明确“展示独立、审批建 Setting 且默认关闭、Setting 为参评真相源、快照读取、管理鉴权”等基线规则。
2. 已明确一期范围边界：对外聚焦集团应用、省内应用、双榜单、申报入口；管理能力不对外开放。
3. 已在 README 固化 Governance Snapshot，建立与治理文档的一致入口。

## Phase-2（真相源与执行路径固化）

1. 已完成 Truth Source 审计文档，给出参评/权重/标签/维度/结果的真相源声明与字段归类。
2. 运行时榜单权威同步路径已固定为 `sync_rankings_service()`，并基于 `AppRankingSetting.is_enabled` 过滤参评候选。
3. 榜单对外读取已基于 `HistoricalRanking` 快照（含 `/api/rankings`、`/api/rankings/historical`、`/api/rankings/available-dates`）。
4. 管理类接口已统一纳入 `require_admin_token` 鉴权依赖（按后端接口实现）。
5. 已保留并标注旧评分路径为 deprecated，用于兼容/审计语义，不作为权威计算入口。

## Phase-3（展示层字段补充）

1. `/api/rankings` 返回已补充 `ranking_config_id` 字段，来源为 `HistoricalRanking.ranking_config_id`。
2. `/api/rankings` 返回已补充 `updated_at` 字段，来源为 `HistoricalRanking.updated_at`。
3. 本阶段变更已在 README 与治理文档中同步说明，且未改变计算口径与真相源定义。

## 交付状态

- Phase-1 ~ Phase-3 治理动作已形成“规则文档 + 审计文档 + 接口实现 + README 入口”的可审计闭环。
