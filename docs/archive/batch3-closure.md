# Batch3 Closure Notes (Models vs Schemas)

## 1. What we fixed (merged)
- **PR #19**
  - 目的：统一日期字段类型语义，避免模型注解与数据库列/Schema 在 date 与 datetime 上不一致。
  - 改动范围：`App.release_date`、`Ranking.declared_at` 类型提示对齐，并新增 `test_date_hints.py`。
  - 如何验证：运行新增日期类型测试，确认类型提示与既有 schema 语义一致。
- **PR #20**
  - 目的：修复可空字段在 schema 层被误设为非 Optional 的不一致问题。
  - 改动范围：`AppDetail` 中可空排行榜字段的 Optional 对齐，并新增 `test_schemas_optional_nullable.py`。
  - 如何验证：运行 Optional/nullable 对齐测试，确认 nullable 字段可被正确序列化与校验。
- **PR #21**
  - 目的：统一创建时默认值来源，避免 model 与 schema 默认值分歧。
  - 改动范围：`difficulty`、`effectiveness_type` 创建默认值与模型默认对齐，并新增 `test_schema_model_default_alignment.py`。
  - 如何验证：运行默认值对齐测试，确认未传值时 schema 与 model 产生一致默认。
- **PR #15**
  - 目的：形成 Batch3 模型与 schema 的差异清单，作为后续修复依据。
  - 改动范围：新增审计报告 `docs/batch3-models-audit.md`。
  - 如何验证：审阅报告条目，确认覆盖字段缺失、类型、Optional、默认值等关键差异。

## 2. Current remaining gaps (decision required, NOT implemented)

| Item | Where (model/schema) | Impact | Risk level (Low/Medium/High) | Suggested next action (Expose / Keep internal / Need product decision) |
|---|---|---|---|---|
| App growth metrics fields (`last_month_calls`, `new_users_count`, `search_count`, `share_count`, `favorite_count`) | Model: `App` has fields; Schema: `AppBase/AppDetail` missing | Growth metrics exist in DB but are not available via API, causing data visibility mismatch | Medium | Need product decision |
| RankingItem missing `ranking_config_id`, `updated_at` | Model: `Ranking` has fields; Schema: `RankingItem` missing | API cannot directly trace ranking source config and update time | Medium | Expose |
| HistoricalRankingOut missing `ranking_config_id` | Model: `HistoricalRanking` has field; Schema: `HistoricalRankingOut` missing | Historical ranking records cannot be directly traced to ranking config | Medium | Expose |
| SubmissionOut missing `cover_image_id` | Model: `Submission` has field; Schema: `SubmissionOut` missing | Asset relationship is partially lost at API layer, affecting image governance | Low | Need product decision |
| Missing schema for `SubmissionImage` | Model: `SubmissionImage` exists; Schema: no corresponding input/output schema | `submission_images` table exists but lacks schema contract for API-level use | Medium | Need product decision |

## 3. Governance rule going forward
- docs-only closure does not change API。
- Any schema exposure change must be a separate PR with owner decision。
- One PR at a time, squash merge, delete branch。
- Tests required: `test_imports` + `test_health` + new tests。

## 4. Next suggested PRs (roadmap)
- PR-A: Expose `ranking_config_id` + `updated_at` in `RankingItem` (if approved).
- PR-B: Decide whether to expose App growth metrics (needs product/security).
- PR-C: Add `SubmissionImage` schemas and endpoints (if needed).
