# Batch3 Models vs Schemas 审计报告

## 范围
- 模型文件：`backend/app/models.py`
- Schema 文件：`backend/app/schemas.py`
- 目标：识别模型字段与 API schema 之间的不一致（字段缺失、类型、Optional、默认值等）

---

## 1) 字段覆盖不一致（Model 有，Schema 缺失）

### 1.1 `App` 模型存在但 `AppBase/AppDetail` 未暴露
- `last_month_calls: float | None`
- `new_users_count: int | None`
- `search_count: int | None`
- `share_count: int | None`
- `favorite_count: int | None`

**影响**：数据库已有增长指标，但接口层不可见，前后端可能产生“数据存在但无法读取/回传”的认知差异。

### 1.2 `Ranking` 模型字段未进入 `RankingItem`
- `ranking_config_id: str`
- `updated_at: datetime`

**影响**：榜单记录无法通过当前输出 schema 直接追踪配置来源与更新时间。

### 1.3 `Submission` 模型字段未进入 `SubmissionOut`
- `cover_image_id: int | None`

**影响**：提交记录与图片主键关系在接口层丢失，仅保留 URL，不利于后续图片资产治理。

### 1.4 完整模型缺少对应 schema
- `SubmissionImage`

**影响**：`submission_images` 表虽然存在，但当前 `schemas.py` 未定义对应输入/输出模型。

### 1.5 `HistoricalRanking` 模型字段未进入 `HistoricalRankingOut`
- `ranking_config_id: str`

**影响**：历史榜单在 API 层无法直接溯源到榜单配置。

---

## 2) Date vs datetime 不一致

### 2.1 `App.release_date`
- Model：`Mapped[datetime] = mapped_column(Date, nullable=False)`（注解是 `datetime`，列类型是 `Date`）
- Schema：`AppBase.release_date: date`

**问题类型**：模型类型注解与数据库列/Schema 语义不一致（`datetime` vs `date`）。

### 2.2 `Ranking.declared_at`
- Model：`Mapped[datetime] = mapped_column(Date, nullable=False)`（注解是 `datetime`，列类型是 `Date`）
- Schema：`RankingItem.declared_at: date`

**问题类型**：同上，模型注解与列/Schema 存在日期粒度不一致。

---

## 3) Optional vs 非 Optional 不一致

### 3.1 `App` 排行榜字段（Model 可空，Schema 非可空）
- Model（均 `nullable=True`）：
  - `ranking_enabled: bool | None`
  - `ranking_weight: float | None`
  - `ranking_tags: str | None`
- Schema（`AppDetail`）：
  - `ranking_enabled: bool = True`
  - `ranking_weight: float = 1.0`
  - `ranking_tags: str = ""`

**问题类型**：数据库允许 `NULL`，但 schema 约束为非 Optional。若库中历史数据出现 `NULL`，序列化/校验可能出错。

---

## 4) 默认值不统一

### 4.1 `difficulty` 默认值
- Model（`App.difficulty`）：`"Low"`
- Schema（`GroupAppCreate.difficulty`）：`"Medium"`

**问题类型**：同一业务字段跨层默认值不一致。

### 4.2 `effectiveness_type` 默认值
- Model（`App.effectiveness_type`）：`"cost_reduction"`
- Schema（`GroupAppCreate.effectiveness_type`）：`"efficiency_gain"`

**问题类型**：默认语义不一致，可能导致“未传值时”入库结果与接口文档预期偏差。

---

## 5) 一致性较好（供参考）
- `RankingDimension` 与 `RankingDimension*` 系列 schema 基本对齐。
- `RankingLog` 与 `RankingLogOut` 对齐。
- `AppDimensionScore` 与 `AppDimensionScoreOut` 对齐。
- `RankingConfig` / `AppRankingSetting` 与对应 schema 基本对齐（`AppRankingSettingCreate` 不含 `app_id` 更像接口设计决策，而非直接冲突）。

---

## 建议（仅审计，不改代码）
1. 先统一“日期粒度”语义：`date`/`datetime` 二选一，并同步模型注解与 schema。
2. 统一 `nullable` 与 Optional 策略：
   - 若业务不接受空值，迁移数据并将列设为 `nullable=False`；
   - 若历史上允许空值，schema 改为 Optional 并显式兜底。
3. 统一默认值来源（优先单一真源）：避免 model 与 schema 各自定义不同默认。
4. 评估是否补齐增长指标字段与历史榜单配置字段的 API 暴露。

