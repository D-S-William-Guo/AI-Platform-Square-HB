# GOVERNANCE（一期定版）

> 适用范围：AI-Platform-Square-HB 一期（展示为主 + 双榜单氛围）。

## 1. 定版规则（Normative Rules）

1. **省内应用展示以 App 为准，独立于榜单。**
   - `/api/apps?section=province` 的返回应仅由 `App.section="province"` 决定。
   - 省内应用是否在榜、是否参与计算，不影响其在“省内应用”展示区被展示。

2. **审批通过 submission 时必须同时创建 AppRankingSetting，且默认 `is_enabled=false`。**
   - 审批通过后：
     - 创建 `App`（`section="province"`）；
     - 针对现有榜单配置（一期为双榜单）创建 `AppRankingSetting`；
     - `AppRankingSetting.is_enabled=false`（管理员二次开启后才参评）。

3. **榜单参与与计算唯一真相源是 AppRankingSetting。**
   - 榜单同步/计算时，候选集必须仅来自 `AppRankingSetting` 中 `is_enabled=true` 的记录。
   - `App` / `Submission` 中 `ranking_*` 字段仅保留为兼容或展示，不得作为参与判定依据。

4. **榜单结果为周期快照（HistoricalRanking），不做实时计算。**
   - 对外榜单读取以 `HistoricalRanking` 为准。
   - 周期口径固定为：
     - 默认：**周榜（自然周）**；
     - 可选：双周/月榜（仅在规则明确发布时启用）。
   - 一期实现至少需保证“周期快照 + 可按期查询”语义，不以内存/实时计算结果直接对外。

5. **首版对外可见范围受限。**
   - In-scope（对外）：集团应用、省内应用、双榜单、申报入口。
   - Out-of-scope（对外）：任何管理能力（维度管理、榜单配置管理、应用参评设置管理、手工调分、批量更新参数等）。
   - 所有管理能力必须：
     - 仅管理员可见（前端）；
     - 后端接口具备权限保护（不是仅靠“约定不调用”）。

## 2. 术语定义

- **App**：应用主实体。承载应用展示信息（名称、单位、类别、状态、描述等）。`section` 区分 `group` 与 `province`。
- **Submission**：省内单位的申报记录。审批通过后可转化为 App。
- **Setting（AppRankingSetting）**：应用对某个榜单配置的参评设置（是否启用、权重因子、自定义标签），是参评真相源。
- **Ranking（当前榜单）**：某榜单配置当前有效的排序结果，用于内部同步与兼容。
- **HistoricalRanking（历史快照）**：按周期固化的榜单结果快照；对外榜单展示以此为准。

## 3. 一期范围边界

### 3.1 In-scope
- 展示：集团应用、省内应用。
- 榜单：双榜单（优秀榜、趋势榜）展示与历史期查询。
- 入口：省内应用申报。

### 3.2 Out-of-scope
- 平台化多榜单扩展（用户自定义创建任意榜单）。
- 对外开放管理后台能力。
- 实时/流式榜单计算。
- 新增配置系统或外部依赖。

## 4. 数据与接口约束（执行性要求）

- 审批接口需保证事务一致性：`Submission.status` 更新、`App` 创建、`AppRankingSetting` 初始化应在同一事务语义下完成。
- 榜单读取接口返回的数据应能追溯到 `HistoricalRanking.period_date`。
- 任何直接修改 `App.ranking_*` / `Submission.ranking_*` 的接口不得宣称“控制参评”，且应在文档中标记为兼容字段。


## 5. Truth Source Guardrails

- 榜单参与判定、应用权重、参评标签的控制输入仅允许来自 `AppRankingSetting`（`is_enabled` / `weight_factor` / `custom_tags`）。
- 禁止 `App.ranking_*`、`Submission.ranking_*` 直接参与榜单候选过滤、得分计算、排序判定。
- `App.ranking_*`、`Submission.ranking_*` 仅可作为兼容材料字段或历史展示字段，不得作为“参评开关”对外承诺。
- 对外榜单展示必须来源于 `HistoricalRanking` 周期快照，不得以实时计算结果直接替代。
- 如需展示“参与状态/标签/权重”，应从 `AppRankingSetting` 或 `HistoricalRanking` 投影，不得从 `App/Submission.ranking_*` 反推。
- 任何新增或修改排行榜相关接口，必须在评审中显式回答：
  1) 该变更是否引入第二真相源；
  2) 是否保持 `require_admin_token` 管理鉴权；
  3) 是否保持快照读取语义。
