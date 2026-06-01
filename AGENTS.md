# AGENTS.md

本文件是仓库级智能体工作契约，目标是让任意智能体工具进入仓库后，先理解项目、文档入口和文档维护规则，再进行修改。

## 仓库速览

- 项目：企业内部 AI 应用广场
- 后端：FastAPI + SQLAlchemy ORM + Alembic
- 数据库：MySQL 5.7
- 前端：React + TypeScript + Vite
- 运行方式：开发机构建前端静态产物，远程主机只负责运行发布物
- 唯一应用配置源：`backend/.env`
- 根目录 `.env`：仅用于 Docker Compose MySQL 覆盖，不是应用配置
- 默认身份模式：`local`
- 榜单参与与控制输入真相源：`AppRankingSetting`
- 对外榜单读取真相源：`HistoricalRanking`

## 文档真相源分层

- 根 [README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/README.md)
  - 项目首页、最短入口、常用命令、文档导航
- [docs/README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/README.md)
  - 当前有效文档索引和职责说明
- [docs/GOVERNANCE.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/docs/GOVERNANCE.md)
  - 当前产品、数据、部署治理基线
- [backend/scripts/README.md](/home/ctyun/BigData/GitHub/AI-Platform-Square-HB/backend/scripts/README.md)
  - 仅解释脚本用途，不承担后端总文档角色
- `docs/archive/`
  - 历史审计、阶段性对齐稿、旧设计稿，仅供追溯，不作为当前规则入口

## 智能体硬约束

- 修改文档前，先判断现有主入口是否已经有对应真相源，禁止新建平行入口重复维护同类内容。
- 涉及运行、部署、数据库、身份模式、榜单规则的改动时，必须同时检查：
  - 根 `README.md` 是否仍是正确导航
  - `docs/README.md` 是否仍准确描述职责
  - `docs/GOVERNANCE.md` 是否需要同步治理结论
- 新增文档时必须标注归属，只能归到以下之一：
  - 主文档
  - 专题文档
  - 脚本说明
  - 历史归档
- 不额外制造“第二份 README”或“另一份当前规范”，尤其不要在 `backend/`、`docs/archive/` 或临时目录复制主入口内容。
- 如果只是补充脚本说明、排障笔记或阶段记录，不要把它写成当前治理口径。
- 文档中的命令和规则必须尽量单点维护；如果详细内容已经沉到 `docs/`，根 `README.md` 只保留短说明和跳转。

## 代码架构（2026-06-01 重构后）

### 后端分层

```
backend/app/
  main.py              (~240行，仅 app 创建 + lifespan + 中间件 + include_router)
  config.py            配置（pydantic-settings，读 backend/.env）
  database.py          DB 连接
  models.py            ORM 模型（15 个表）
  schemas.py           Pydantic 请求/响应模型
  auth_utils.py        密码哈希/验证/令牌
  dependencies.py      共享依赖（认证/鉴权/分页/审计/限流）
  identity.py          身份提供者抽象
  routers/            13 个域路由器（每个用 APIRouter + include_router）
    meta.py auth.py apps.py rankings.py submissions.py
    ranking_configs.py ranking_settings.py admin_users.py
    admin_review.py upload.py audit.py integration.py frontend.py
  services/            2 个服务层（业务逻辑脱离 HTTP）
    ranking_service.py submission_service.py
```

### 前端分层

```
frontend/src/
  App.tsx              (~280行，路由配置 + 认证加载)
  api/client.ts        API 客户端
  types/index.ts       类型定义
  utils/               media/basePath
  components/          通用组件（8 个）
    Modal.tsx PageHeader.tsx LoadingState.tsx EmptyState.tsx
    ErrorState.tsx StatCard.tsx Pagination.tsx UiIcon.tsx
  hooks/              自定义 Hook（3 个）
    useAuth.ts usePagination.ts useForm.ts
  pages/
    HomePage.tsx       441 行（重构前 1511）
    RankingManagementPage.tsx  457 行（重构前 1985）
    components/        HomePage 子组件（6 个）+ Ranking 子组件（9 个）
```

### 关键数据表

| 表 | 用途 |
|---|---|
| `ranking_configs` | 榜单配置（excellent / trend） |
| `ranking_config_dimensions` | 配置-维度关联（2026-06-01 由 JSON TEXT 迁移） |
| `app_ranking_settings` | 应用参与榜单设置 |
| `rankings` | 实时排名 |
| `historical_rankings` | 历史排名快照（真相源） |
| `submissions` | 申报记录 |
| `app_change_requests` | 已通过应用的变更申请 |

### 测试

```
backend/tests/
  test_api.py          2267 行，80 个 API 集成测试（按域分段注释）
  test_auth_utils.py   28 个单元测试
  test_submission_service.py  25 个单元测试
  test_ranking_service.py     30 个单元测试
  test_dependencies.py        16 个单元测试
  helpers.py           共享测试工厂函数
  conftest.py          session 级 DB fixture + rate limit 重置
```

- 总计 213 tests（重构前 103）
- 运行：`cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/`

### 已清理的技术债

- `ranking_type` 列已删除（三个表，原与 `ranking_config_id` 双写冗余）
- `dimensions_config` JSON TEXT → `ranking_config_dimensions` 关联表（有 FK 约束）
- `or_()` 双字段回退查询已全部简化为直接 `== ranking_config_id`
- 修复 bug：`_collect_config_dimension_ids` → `collect_config_dimension_ids`

### 刻意未做的项目

- Redis 限流：内部工具 ROI 为负，已文档化
- `test_api.py` 物理拆分：测试间有 DB 状态顺序依赖，强行拆会导致 flaky tests
- `useForm` / `useAuth` Hook 接入：验证 API 不兼容，需独立重构
- `dimensions_config` JSON 列物理删除：保留在 DB 中作为降级兜底，ORM 已不映射

## 最近关键文档变更

- 2026-06-01 完成架构重构：后端 13 routers + 2 services，前端 15 子组件，清理 ranking_type 双字段和 dimensions_config JSON 列，新增 112 单元测试（总计 213）
- 2026-05-29 重构用户操作手册为角色任务版，补充申报、应用、榜单、权重和历史快照关系图
- 2026-05-29 补充已通过应用修改链路：申报人提交应用变更申请，管理员审核后更新当前应用；历史榜单快照保留发布当时名称，不随改名回写
- 2026-05-25 补充已登录用户主动修改密码入口：首页右上角用户区展示“修改密码”，匿名游客不可见
- 2026-05-22 补充本地密码治理：默认密码、管理员新建/重置和用户自助改密统一要求强口令；初始或重置密码按临时密码处理，用户下次登录后必须改密
- 2026-05-03 调整首页产品口径：首页默认展示双榜单，集团应用/省内应用统一进入展示型应用视图并通过来源筛选区分；两类应用均不作为平台内跳转使用入口，当前榜单仍仅展示省内应用
- 最近一次文档治理收敛：2026-05-02（全仓库文档审计，修正过时/错误引用，标注历史归档）
- 2026-04-21 新增用户操作手册：`docs/user-manual.md`，按匿名/登录/管理员三类角色输出逐步骤操作与截图占位，并已纳入 `docs/README.md` 索引
- 2026-04-18 补充 Phase 2 口径：匿名浏览+登录申报+管理员管理三层访问模型下，关键前端意图事件统一写入 `ActionLog` 并通过 `X-Request-Id` 串联；新增 Playwright 3 身份回归入口
- 2026-04-17 补充账号访问分层口径：匿名仅可读首页/详情/榜单；申报与管理统一要求登录；未登录点击“我要申报”登录成功后自动回跳并打开申报弹窗；不再维护 `manage_token` 自助链路
- 2026-04-14 记录远程子路径部署验证结果：`/AISquare/` 已在 `:38878 -> 127.0.0.1:30888` 场景启动并访问成功，继续沿用完整子路径部署口径
- 2026-04-13 补充“完整子路径部署口径”：子路径发布时，页面、前端 API 与媒体资源统一跟随同一前缀；远程主机继续采用停服务、换发布物、启服务的更新方式
- 2026-04-10 补充“前端支持根路径/子路径构建发布”的部署口径，主入口仍保持不变
- 当前有效入口：
  - 根 `README.md`
  - `AGENTS.md`（本文件）
  - `docs/README.md`
  - `docs/GOVERNANCE.md`
  - `docs/user-manual.md`
  - `docs/dev-setup.md`
  - `docs/db-migration-sop.md`
  - `docs/dev-workflow.md`
- 已明确不是当前规则入口：
  - `docs/archive/*`
  - `backend/scripts/README.md`
  - 任何未在 `docs/README.md` 列出的临时说明文档
- 当前治理结论：
  - 根 `README.md` 保留总览和导航，不再承载完整运维细节
  - `docs/README.md` 作为文档总索引
  - `docs/GOVERNANCE.md` 只保留治理基线，不承担智能体操作规约

## 文档维护动作

- 修改主入口后，记得同步更新本文件里的“最近关键文档变更”。
- 新增或重命名有效文档后，记得同步更新 `docs/README.md`。
- 产品、部署、数据库、身份、榜单规则变化后，记得同步检查 `docs/GOVERNANCE.md`。
- 如果某文档只剩历史价值，应迁入 `docs/archive/` 或在正文显式标注“仅供追溯”。
