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

## 最近关键文档变更

- 最近一次文档治理收敛：2026-04-18
- 2026-04-18 补充 Phase 2 口径：匿名浏览+登录申报+管理员管理三层访问模型下，关键前端意图事件统一写入 `ActionLog` 并通过 `X-Request-Id` 串联；新增 Playwright 3 身份回归入口
- 2026-04-17 补充账号访问分层口径：匿名仅可读首页/详情/榜单；申报与管理统一要求登录；未登录点击“我要申报”登录成功后自动回跳并打开申报弹窗；不再维护 `manage_token` 自助链路
- 2026-04-14 记录远程子路径部署验证结果：`/AISquare/` 已在 `:38878 -> 127.0.0.1:30888` 场景启动并访问成功，继续沿用完整子路径部署口径
- 2026-04-13 补充“完整子路径部署口径”：子路径发布时，页面、前端 API 与媒体资源统一跟随同一前缀；远程主机继续采用停服务、换发布物、启服务的更新方式
- 2026-04-10 补充“前端支持根路径/子路径构建发布”的部署口径，主入口仍保持不变
- 当前有效入口：
  - 根 `README.md`
  - `docs/README.md`
  - `docs/dev-setup.md`
  - `docs/db-migration-sop.md`
  - `docs/dev-workflow.md`
  - `docs/GOVERNANCE.md`
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
