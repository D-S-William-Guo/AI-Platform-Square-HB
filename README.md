# AI-Platform-Square-HB

企业内部 **AI 应用广场** 全栈实现（需求确认版 MVP）。

## 技术栈

- 前端：React + TypeScript + Vite
- 后端：Python FastAPI + SQLAlchemy
- 数据库：MySQL（生产建议）/ SQLite（本地快速启动默认）

## 目录结构

- `frontend/`：页面与组件实现（三栏布局、应用卡片、榜单、详情抽屉）
- `backend/`：REST API、数据模型、初始化种子数据
- `docs/ai-app-square-requirement-prompt.md`：需求冻结稿

## 快速启动

### 1) 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) 前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

## 后端 API（核心）

- `GET /api/apps`：应用列表（支持 section/status/category/q 过滤）
- `GET /api/apps/{id}`：应用详情
- `GET /api/rankings`：龙虎榜数据
- `GET /api/recommendations`：本期推荐
- `GET /api/stats`：申报统计
- `POST /api/submissions`：应用申报

## 数据结构（当前实现 + 建议扩展）

### 已实现（后端数据库核心表）

| 表 | 说明 | 主要字段 | 关系 |
| --- | --- | --- | --- |
| `apps` | 应用基础信息 | name/org/section/category/status/monthly_calls/release_date 等 | `rankings.app_id -> apps.id` |
| `rankings` | 应用榜单条目 | ranking_type/position/tag/score/likes/usage_30d/declared_at | 关联 `apps` |
| `submissions` | 申报记录 | app_name/unit_name/contact/scenario/status/created_at | 与 `apps` 暂未强关联（申报通过后可转化为 `apps`） |

> 当前数据结构以“展示 + 榜单 + 申报”为主，适合 MVP 运行与页面对齐。建议保持 `apps` 为主实体、`rankings` 为榜单派生、`submissions` 为待审核输入三段式链路。

### 建议补充（数据源采购/外部数据治理）

如果需要引入外部/采购数据源，建议新增一组独立表来管理“来源、采购、处理、落库”全流程，可先在 README 明确模型，再按需落到后端代码：

| 表 | 说明 | 关键字段 | 关联建议 |
| --- | --- | --- | --- |
| `data_sources` | 数据源登记（内部/外部） | name/type/provider/owner/contact/status | 作为其它数据表的来源引用 |
| `data_source_purchases` | 采购信息 | source_id/contract_no/cost/period/license_scope | `source_id -> data_sources.id` |
| `data_source_processing` | 数据处理链路 | source_id/pipeline/etl_owner/update_cycle/quality_score | `source_id -> data_sources.id` |
| `data_source_usage` | 使用记录与落库 | source_id/system/use_case/last_sync/retention_policy | `source_id -> data_sources.id` |

> 如果短期不落地到数据库，也可以先放在 `docs/` 内作为数据治理设计文档，待研发排期时再迁移到后端模型中。

## 需求对齐清单（持续更新）

- v1（接口字段冻结 + 页面状态机）：`docs/alignment-v1.md`
- v2-draft（5个待确认点建议决策）：`docs/alignment-v2-draft.md`
- v2-final（已确认版）：`docs/alignment-v2-final.md`
- 说明：后续每轮讨论先更新该清单，双方确认后再进入对应编码。

## 关系梳理与本地调试建议

### 模块关系（前后端 + 数据链路）

1. **前端（`frontend/`）** 通过 `/api/*` 拉取列表、榜单、推荐、统计数据。
2. **后端（`backend/`）** 负责聚合 `apps` / `rankings` / `submissions` 三类数据。
3. **数据主链路**：`submissions` 记录申报 → 通过后进入 `apps`（应用主实体）→ `rankings` 基于 `apps` 生成榜单派生数据。

> 该链路和页面结构保持一致，核心实体在 `apps`，榜单和申报是围绕它的前后向数据流。

### 分支与合并建议（保持结构正规化）

- 建议以 **主干（main/master）** 为稳定基线，当前工作分支用于验证需求与迭代。
- 当 README/数据结构更新完成后，合并回主干即可保证团队本地 IDE 拉取后可直接调试。
- 如果需要在本地执行“前后端联调”，可先按“快速启动”步骤分别拉起后端与前端。

## 阶段性成果可视化

- 预览页面：`preview/stage-demo.html`
- 本地查看：在仓库根目录执行 `python -m http.server 8081` 后访问 `http://localhost:8081/preview/stage-demo.html`
