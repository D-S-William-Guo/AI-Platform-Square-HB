# 前后端需求对齐清单（v2-final）

> 依据：业务方对 v2-draft 的逐条确认结果。
> 结论：5 个待确认点全部确认，进入“按 v2-final 实施并联调”阶段。

## 1) status 扩展（已确认）

- 枚举：`available` / `approval` / `beta` / `offline`
- 补充业务要求：
  - `direct`：可直达使用入口（访问 URL）
  - `profile`：展示介绍页（名称、接入系统、使用人群、解决问题、成效说明）

## 2) ranking 指标（已确认并扩充）

- `score`：综合分（可来自多维指标）
- `metric_type`：`composite` / `growth_rate` / `likes`
- `value_dimension`：`cost_reduction` / `efficiency_gain` / `perception_uplift` / `revenue_growth`
- 可选补充：`likes`、`usage_30d`（近30日使用情况）

## 3) submissions 字段（已确认并扩充）

除基础字段外，申报应覆盖与展示信息一致的核心信息：

- `scenario`（应用场景）
- `embedded_system`（嵌入系统）
- `problem_statement`（解决问题）
- `effectiveness_type`（降本/增效/感知提升/收入拉动）
- `effectiveness_metric`（指标口径）
- `data_level`（L1~L4）
- `expected_benefit`（预期收益）

## 4) rules OA 内链（已确认）

- 规则链接由后端按 OA 基础地址拼接并返回完整 URL。
- OA SSO 与具体路由在联调阶段再细化。

## 5) 单表策略（已确认）

- 当前采用单表 + `section` 枚举（集团/省内）。
- 后续若两侧字段差异显著再拆分子表或扩展表。

---

## 本轮实施范围（已落地）

- 后端模型、Schema、接口已按上述确认项扩展。
- 前端列表、榜单、详情、申报表单已同步字段与状态。
- 新增 `GET /api/meta/enums` 提供前端动态枚举来源。
