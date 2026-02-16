# Truth Source Audit（Phase-2）

> 范围：仅审计与文档固化，不改动业务逻辑/模型/API 返回。
> 审计基准：Phase-1 冻结规则（App 展示独立、审批创建 Setting 且默认关闭、唯一真相源为 AppRankingSetting、榜单按 HistoricalRanking 快照读取、管理接口需 token 鉴权）。

## 1) 真相源声明（Source of Truth Statement）

- **参与（是否参评）唯一真相源**：`AppRankingSetting.is_enabled`，并按 `ranking_config_id` 过滤。计算入口 `sync_rankings_service` 仅查询 `AppRankingSetting`。  
- **权重（应用级）唯一真相源**：`AppRankingSetting.weight_factor`。  
- **标签（参评标签）唯一真相源**：`AppRankingSetting.custom_tags`（空值回退默认标签）。  
- **维度（榜单级）唯一真相源**：`RankingConfig.dimensions_config` + `RankingDimension`（active）。  
- **得分与排名结果真相源**：计算落地到 `Ranking`（当前态）与 `HistoricalRanking`（对外快照）；对外榜单读取以 `HistoricalRanking` 为准。  
- **兼容字段声明**：`App.ranking_*`、`Submission.ranking_*` 目前仍可写/可返回，但不应作为参与判定或计算控制输入。

## 2) 字段归类表（材料 / 控制 / 结果）

| 字段 | 实体 | 归类 | 是否允许写入 | 当前使用状态（读/写/暴露） |
|---|---|---|---|---|
| `Submission.ranking_enabled` | Submission | 材料（兼容） | 允许（提交时） | **写**：`POST /api/submissions`；**读+拷贝**：审批创建 App；**暴露**：`SubmissionOut` |
| `Submission.ranking_weight` | Submission | 材料（兼容） | 允许（提交时） | 同上；并用于审批前字段合法性校验（长度/区间） |
| `Submission.ranking_tags` | Submission | 材料（兼容） | 允许（提交时） | 同上 |
| `Submission.ranking_dimensions` | Submission | 材料（兼容） | 允许（提交时） | **写**：提交；**读**：审批前校验；**暴露**：`SubmissionOut` |
| `App.ranking_enabled` | App | 材料（兼容） | 允许（管理接口可改） | **写**：审批拷贝、集团录入、`/apps/{id}/ranking-params`、batch-update；**暴露**：`AppDetail` |
| `App.ranking_weight` | App | 材料（兼容） | 允许（管理接口可改） | 同上 |
| `App.ranking_tags` | App | 材料（兼容） | 允许（管理接口可改） | 同上 |
| `AppRankingSetting.is_enabled` | AppRankingSetting | **控制（唯一）** | 允许（管理接口） | **读（计算准入）**：`sync_rankings_service`；**写**：创建/更新 setting |
| `AppRankingSetting.weight_factor` | AppRankingSetting | **控制（唯一）** | 允许（管理接口） | **读（计算权重）**：`sync_rankings_service`；**写**：创建/更新 setting |
| `AppRankingSetting.custom_tags` | AppRankingSetting | **控制（唯一）** | 允许（管理接口） | **读（榜单标签）**：`sync_rankings_service`；**写**：创建/更新 setting |
| `RankingConfig.dimensions_config` | RankingConfig | 控制（榜单维度规则） | 允许（管理接口） | **读（计算）**：`sync_rankings_service`；**写**：ranking-config 管理接口 |
| `RankingDimension.*`（`weight/is_active` 等） | RankingDimension | 控制（维度定义） | 允许（管理接口） | **读（计算）**：`sync_rankings_service`；**写**：维度管理接口 |
| `Ranking.position/score/tag/...` | Ranking | 结果（当前态） | 仅计算流程写入 | **写**：`sync_rankings_service`；**读**：主要兼容内部 |
| `HistoricalRanking.position/score/tag/...` | HistoricalRanking | **结果（快照真相源）** | 仅计算流程写入 | **写**：`sync_rankings_service`；**读（对外）**：`/api/rankings`、`/api/rankings/historical`、`/available-dates` |

> 结论：`App/Submission.ranking_*` 应继续标记为“材料字段”，不得回归为控制字段。

## 3) 计算路径审计（B）

### 3.1 `sync_rankings_service` 数据来源与过滤

- 来源：`RankingConfig(is_active=true)` + `RankingDimension(is_active=true)` + `AppRankingSetting(ranking_config_id=config.id, is_enabled=true)`。  
- 过滤：只纳入 `setting.app.section == "province"`。  
- 计算：`calculate_dimension_score` + `calculate_three_layer_score(..., weight_factor=setting.weight_factor)`。  
- 输出：写 `Ranking`（当前态）并写 `HistoricalRanking(period_date=today)` 快照。

### 3.2 “是否读取 App/Submissions ranking_* 作为计算依据”

- **主计算路径中未发现**读取 `App.ranking_enabled/ranking_weight/ranking_tags` 或 `Submission.ranking_*` 参与准入/打分。  
- 发现一个**遗留风险点**：`main.py` 内 `calculate_app_score`（标注 Deprecated）仍引用 `app.ranking_weight`，虽当前未在权威同步路径中调用，但存在误用风险。

## 4) 接口分层清单（C）

## 4.1 Public endpoints（无需鉴权）

- `GET /api/health`
- `GET /api/venv/info`
- `GET /api/venv/python-path`
- `GET /api/venv/site-packages`
- `GET /api/apps`
- `GET /api/apps/{app_id}`
- `GET /api/rankings`
- `GET /api/recommendations`
- `GET /api/stats`
- `GET /api/rules`
- `POST /api/submissions`
- `GET /api/meta/enums`
- `GET /api/ranking-dimensions/{dimension_id}/scores`
- `GET /api/apps/{app_id}/dimension-scores`
- `GET /api/rankings/historical`
- `GET /api/rankings/available-dates`
- `POST /api/upload/image`
- `POST /api/submissions/{submission_id}/images`
- `GET /api/submissions/{submission_id}/images`

## 4.2 Admin endpoints（必须鉴权）

- `GET /api/submissions`
- `GET /api/ranking-dimensions`
- `GET /api/ranking-dimensions/{dimension_id}`
- `POST /api/ranking-dimensions`
- `PUT /api/ranking-dimensions/{dimension_id}`
- `DELETE /api/ranking-dimensions/{dimension_id}`
- `GET /api/ranking-logs`
- `POST /api/rankings/sync`
- `PUT /api/apps/{app_id}/ranking-params`
- `POST /api/apps/batch-update-ranking-params`
- `PUT /api/apps/{app_id}/dimension-scores/{dimension_id}`
- `POST /api/submissions/{submission_id}/approve-and-create-app`
- `POST /api/admin/group-apps`
- `GET /api/ranking-configs`
- `GET /api/ranking-configs/{config_id}`
- `GET /api/ranking-configs/{config_id}/with-dimensions`
- `POST /api/ranking-configs`
- `PUT /api/ranking-configs/{config_id}`
- `DELETE /api/ranking-configs/{config_id}`
- `GET /api/apps/{app_id}/ranking-settings`
- `POST /api/apps/{app_id}/ranking-settings`
- `PUT /api/apps/{app_id}/ranking-settings/{setting_id}`
- `DELETE /api/apps/{app_id}/ranking-settings/{setting_id}`
- `GET /api/app-ranking-settings`

### 4.3 边界/遗漏观察（仅列问题，不改）

1. 前端 `api/client.ts` 对管理员接口普遍**未携带 `X-Admin-Token` / Bearer**，且 `createGroupApp` 使用 query 参数 `admin_token`，与后端 `require_admin_token`（仅 Header/Bearer）不一致。  
2. `PUT /api/apps/{app_id}/ranking-params` 与 `POST /api/apps/batch-update-ranking-params` 仍写 `App.ranking_*`，存在“材料字段被误认为控制字段”的认知风险。  
3. `/api/venv/*` 为公开接口，虽与榜单无关，但属于环境信息暴露面，建议后续明确是否应管理员可见。

## 5) 风险清单（双轨回归风险）

### P0

- **前端-后端鉴权协议错位**：管理员接口设计要求 token header，但前端调用未统一按该协议发送，可能导致“管理能力不可用”或绕过约定实现。  
- **审批默认设置与治理文本不完全一致**：审批接口当前只创建 1 条 `AppRankingSetting(ranking_config_id=None, is_enabled=false)`，与“针对现有榜单配置创建设置”存在偏差，后续若代码依赖“每榜单一条 setting”会造成控制语义歧义。

### P1

- **遗留控制字段写口仍存在**：`App.ranking_*` 仍可通过管理接口修改，虽不参与计算，但会被误读为控制开关。  
- **Deprecated 旧函数仍可被误调用**：`calculate_app_score` 仍引用 `App.ranking_weight`。

### P2

- **Schema 持续暴露兼容字段**：`SubmissionOut`、`AppDetail` 暴露 `ranking_*`，前端容易形成“显示即控制”的误解。  
- **seed 脚本含另一条同步实现（`seed.sync_rankings`）**，虽非运行时主路径，但维护时有认知分叉风险。

## 6) 可执行审计清单（建议作为回归脚本）

- [ ] `rg -n "AppRankingSetting\.is_enabled|weight_factor|custom_tags" backend/app/main.py backend/app/seed.py`
- [ ] `rg -n "ranking_enabled|ranking_weight|ranking_tags|ranking_dimensions" backend/app/main.py backend/app/schemas.py backend/app/models.py`
- [ ] `rg -n "Depends\(require_admin_token\)|def require_admin_token" backend/app/main.py`
- [ ] `rg -n "@app\.(get|post|put|delete)\(" backend/app/main.py`
- [ ] `rg -n "X-Admin-Token|Authorization|admin_token" frontend/src/api/client.ts`

## 7) 后续最小 PR 建议（仅标题与范围）

1. **PR: 统一前端管理员鉴权头传递**  
   范围：`frontend/src/api/client.ts`（管理员接口统一加 `X-Admin-Token` 或 Bearer）。
2. **PR: 标注并收敛 App/Submission ranking_* 为兼容只读语义**  
   范围：接口文档与注释，不改返回字段；补充“非控制字段”说明。
3. **PR: 审批初始化按“每个 active RankingConfig 创建 disabled Setting”对齐治理规则**  
   范围：`approve-and-create-app` 初始化策略（单独变更，含迁移脚本评估）。
4. **PR: 下线或隔离 deprecated 评分函数与 seed 内重复同步逻辑**  
   范围：代码注释/模块边界整理，避免误调用。
