# AI-Platform-Square-HB

企业内部 **AI 应用广场** 全栈实现（需求确认版 MVP）。

## 技术栈

- 前端：React + TypeScript + Vite
- 后端：Python FastAPI + SQLAlchemy
- 数据库：MySQL 8.0 + Alembic

## Governance Snapshot

- 省内应用展示以 `App(section=province)` 为准，独立于是否上榜。
- 审批通过申报时必须创建 `App` + `AppRankingSetting`，且后者默认 `is_enabled=false`。
- 榜单参评唯一真相源为 `AppRankingSetting`（不是 `App/Submission` 的 `ranking_*` 字段）。
- 榜单对外展示以周期快照 `HistoricalRanking` 为准，不做实时计算口径。
- 周期口径默认按周（自然周）；双周/月仅在规则明确发布时启用。
- 一期对外仅展示：集团应用、省内应用、双榜单、申报入口。
- 维度管理、榜单配置、参评设置、手工调分等管理能力仅管理员可见且后端需权限保护。
- 一期不做平台化扩展：不引入“可创建无限榜单”产品能力。
- 保持 `main` 可 import，health test 与 import smoke test 持续通过。
- 详细规则见 `docs/GOVERNANCE.md`。

## Phase-3 API 字段增强说明

`/api/rankings` 展示字段已补充以下两个返回项：

- `ranking_config_id`：来源于榜单快照记录 `HistoricalRanking.ranking_config_id`。
- `updated_at`：来源于榜单快照记录 `HistoricalRanking.updated_at`。

## Phase-4 run_id 发布机制（PR-B）

- `HistoricalRanking` 新增可空字段 `run_id`（UUID 字符串），用于区分同一天内的多次发布。
- `/api/rankings/sync` 支持可选参数 `run_id`；不传时后端自动生成并随响应返回。
- 榜单读取默认取“该日期最新 run_id”的快照；旧数据 `run_id=NULL` 仍可正常读取（向后兼容）。
- 数据库迁移执行顺序与验证方式见 `docs/db-migration-sop.md`。
- 回放口径：可按 `date + run_id` 精确回放同日任意一次发布快照。
- 审计口径：发布行为具备最小审计落库，可追溯关键上下文。
- 回归锁口径：核心行为由 Phase-4 回归用例锁定，防止口径漂移。

## 目录结构

```
AI-Platform-Square-HB/
├── frontend/          # 前端项目
│   ├── src/
│   │   ├── pages/     # 页面组件
│   │   ├── api/       # API客户端
│   │   ├── types/     # TypeScript类型定义
│   │   ├── styles/    # 样式文件
│   │   │   ├── global-layout.css  # 全局布局样式
│   │   │   ├── ranking-detail.css # 榜单详情样式
│   │   │   └── ranking-management.css # 排行榜管理样式
│   │   └── styles.css # 全局样式入口
│   └── package.json
├── backend/           # 后端项目
│   ├── app/
│   │   ├── main.py    # FastAPI主应用
│   │   ├── models.py  # SQLAlchemy数据模型
│   │   └── schemas.py # Pydantic数据验证
│   ├── alembic/       # Alembic 迁移脚本
│   └── requirements.txt
├── docs/              # 项目文档
│   ├── ai-app-square-requirement-prompt.md
│   ├── dev-workflow.md
│   └── CHANGELOG.md   # 更新日志
└── README.md
```

## 快速启动

### 0) 准备环境变量

```bash
cp backend/.env.example backend/.env
# 如需覆盖 docker compose 的默认账号，再额外复制：
# cp .env.example .env
# 如需给 make/backend/frontend 统一注入本地变量，可再复制：
# cp .env.local.example .env.local
```

说明：
- `backend/.env` 是后端运行时真相源，至少要配置 `DATABASE_URL`。
- 根目录 `.env` 仅用于覆盖 docker compose 中的 MySQL 默认账号。
- 根目录 `.env.local` 会被 `make backend-dev`、`make frontend-dev`、`make test` 自动加载，适合本机调试。
- 默认端口约定：
  - `APP_PORT=80`：准生产单端口
  - `BACKEND_DEV_PORT=8000`：后端开发端口
  - `FRONTEND_DEV_PORT=5173`：前端开发端口

### 1) 安装依赖与虚拟环境

```bash
make venv
make backend-install
make frontend-install
```

当前仓库统一使用根目录 `.venv`，不再使用 `backend/.venv`。

### 2) 启动 MySQL

```bash
make db-up
```

本地默认通过 Docker Compose 暴露 `127.0.0.1:13306`。
如果部署环境是“本机应用 + 远程 MySQL 服务”，只需要把 `backend/.env` 中的 `DATABASE_URL` / `TEST_DATABASE_URL` 改成远程地址。

### 3) 执行迁移与基础初始化

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
# 仅开发/演示需要时：
# PYTHONPATH=. ../.venv/bin/python -m app.bootstrap seed-demo
```

### 4) 开发模式启动前后端

后端：
```bash
make backend-dev
```

前端：
```bash
make frontend-dev
```

开发访问地址：
- 后端 API：`http://127.0.0.1:${BACKEND_DEV_PORT:-8000}`
- Swagger：`http://127.0.0.1:${BACKEND_DEV_PORT:-8000}/docs`
- 前端：`http://127.0.0.1:${FRONTEND_DEV_PORT:-5173}`

### 5) 最小验证

```bash
curl -sS "http://127.0.0.1:${BACKEND_DEV_PORT:-8000}/api/health"
```

期望返回：`{"status":"ok"}`

后端运行配置：
- `DATABASE_URL`（必填，仅支持 `mysql+pymysql://...`）
- `TEST_DATABASE_URL`（测试专用，建议独立库）
- `STATIC_DIR`（默认：`static`）
- `UPLOAD_DIR`（默认：`static/uploads`）
- `IMAGE_DIR`（默认：`static/images`）
- 以上相对路径统一以 `backend/` 目录为基准解析（与启动时 cwd 无关），也可配置为绝对路径。
- 启动校验要求：`UPLOAD_DIR` 必须解析到 `STATIC_DIR/uploads`，否则服务将启动失败并提示配置错误（避免返回 `/static/uploads/...` 出现 404）。

数据库迁移与初始化步骤统一维护在：`docs/db-migration-sop.md`。

## 准生产部署（单机内网、单端口同源）

目标形态：
- 前端先构建成 `frontend/dist`
- 后端同源托管前端静态文件和 `/api/*`
- 对外只暴露一个端口：`APP_PORT`
- 数据库连接远程 MySQL，首次部署按空库初始化处理

推荐顺序：

```bash
cp backend/.env.example backend/.env
# 把 DATABASE_URL 改成远程 MySQL
# 把 ENVIRONMENT 改成 production
# 把 USER_DEFAULT_PASSWORD / ADMIN_DEFAULT_PASSWORD 改成正式值

cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
cd ..
make app-serve
```

准生产访问地址：
- 应用首页：`http://<host>:${APP_PORT:-80}`
- 健康检查：`http://<host>:${APP_PORT:-80}/api/health`

说明：
- `make app-serve` 会先构建前端，再启动后端单端口服务。
- 若远程 MySQL 不是空库或不是本项目独占的新库，本次定版不负责自动识别和兼容，需先人工清库或迁移到新库。

本地 0 门槛调试（推荐）：

```bash
cp .env.local.example .env.local
```

> `make backend-dev` / `make frontend-dev` / `make test` 会自动加载仓库根目录 `.env.local`。  
> 该文件已在 `.gitignore` 中忽略，不会提交到 GitHub。  
> 管理接口只接受管理员登录态，不再支持 `X-Admin-Token`、`ADMIN_TOKEN`、`VITE_ADMIN_TOKEN` 之类旁路令牌。

## 登录与权限（第一阶段）

- 新增会话登录接口：
  - `POST /api/auth/login`
  - `GET /api/auth/me`
  - `POST /api/auth/logout`
- 初始化基础数据后会提供两个默认账号（可通过环境变量修改默认密码）：
  - 普通用户：`zhangsan`（张三）
  - 管理员：`lisi`（李四）
- 管理接口只接受：`Authorization: Bearer <session_token>`（管理员登录态）
- 前端访问控制：
  - 未登录用户会被重定向到登录页，不能直接进入首页。
  - 普通用户可访问展示能力；管理员可额外访问“申报审核/排行榜管理”。
- 审计追溯增强：
  - `submissions` / `apps` 新增申报人、审批人、审批/拒绝时间与拒绝原因等追溯字段。
  - 关键动作（申报创建、修改、撤回、审批、拒绝、集团应用录入）会写入 `action_logs`。
- 用户管理能力（管理员）：
  - `GET /api/admin/users`（查询用户）
  - `PUT /api/admin/users/{id}/role`（调整角色）
  - `PUT /api/admin/users/{id}/status`（启停用户）
  - `POST /api/admin/users/import`（批量导入/更新用户资料，角色不随导入变更）
- 外部系统同步预留：
  - `POST /api/integration/users/sync`（基于 `X-User-Sync-Token`）
  - 当 `USER_SYNC_TOKEN` 未配置时该接口默认禁用

## ⚠️ 前端开发规范（重要）

### CSS 命名空间规范（必读）

**⚠️ 警告**：本项目使用 **CSS 命名空间** 来隔离不同页面的样式，以避免样式冲突。这是经过实践验证的最佳方案，**所有前端开发人员必须遵守**。

#### 为什么需要命名空间？

在之前的开发中，我们遇到了严重的样式冲突问题：
- 修改排行榜管理页面样式 → 首页样式被破坏
- 全局样式 `.card`、`.grid`、`.main` 被多个页面共用 → 相互覆盖
- Vite 开发模式下 CSS 优先级难以预测

**解决方案**：每个页面使用独立的命名空间前缀

#### 命名空间规则

| 页面 | 命名空间类名 | 示例 |
|------|-------------|------|
| 首页 | `.home-page` | `.home-page .card` |
| 排行榜管理 | `.ranking-management-page` | `.ranking-management-page .page-container` |
| 榜单详情 | `.ranking-detail-page` | `.ranking-detail-page .section` |

#### 实施步骤

**1. 在页面根元素添加命名空间类：**
```tsx
// App.tsx（首页）
<div className="page home-page">  {/* 添加 home-page 类 */}
  {/* 页面内容 */}
</div>

// RankingManagementPage.tsx
<div className="page ranking-management-page">  {/* 添加 ranking-management-page 类 */}
  {/* 页面内容 */}
</div>
```

**2. 在样式文件中使用命名空间：**
```css
/* styles/home-page.css */
.home-page .card {
  /* 首页特有的卡片样式 */
}

.home-page .grid {
  /* 首页特有的网格布局 */
}

/* styles/ranking-management.css */
.ranking-management-page .page-container {
  max-width: 1400px;
}

.ranking-management-page .table {
  /* 排行榜管理特有的表格样式 */
}
```

**3. 样式文件导入顺序（styles.css）：**
```css
/* CSS 变量必须在 @import 之前定义 */
:root {
  --primary-color: #4f7cff;
  /* ... */
}

/* 1. 全局布局样式（先导入，优先级最低） */
@import './styles/global-layout.css';

/* 2. 页面特定样式（后导入，优先级更高） */
@import './styles/home-page.css';
@import './styles/ranking-detail.css';
@import './styles/ranking-management.css';
```

#### 文件组织规范

```
src/styles/
├── global-layout.css      # 全局布局样式（简单类名，如 .page-container）
├── home-page.css          # 首页样式（使用 .home-page 命名空间）
├── ranking-detail.css     # 榜单详情样式（使用 .ranking-detail-page 命名空间）
└── ranking-management.css # 排行榜管理样式（使用 .ranking-management-page 命名空间）
```

#### 开发注意事项

**✅ 正确的做法：**
```css
/* 页面特定样式使用命名空间 */
.home-page .card {
  background: white;
}

/* 全局通用组件不使用命名空间 */
.btn-primary {
  background: var(--primary-color);
}
```

**❌ 错误的做法：**
```css
/* 不要在没有命名空间的情况下定义页面特定样式 */
.card {
  /* 这会影响所有页面！ */
}

/* 不要在页面样式中修改全局组件 */
.ranking-management-page .btn {
  /* 这会破坏其他页面的按钮样式！ */
}
```

#### Vite 开发模式注意事项

⚠️ **重要**：Vite 开发模式下 CSS 处理与生产模式有差异：

- CSS `@import` 顺序决定最终优先级
- 后导入的文件中的同名选择器会覆盖先导入的
- 开发模式下样式是动态注入的，可能与生产构建结果不同

**验证样式**：修改样式后，务必运行以下命令验证：
```bash
npm run verify:styles  # 构建并预览生产版本
```

#### 调试技巧

1. 使用浏览器 DevTools 检查元素样式来源
2. 确认样式选择器包含正确的命名空间前缀
3. 检查 `styles.css` 中的 `@import` 顺序是否正确
4. 如果样式不生效，尝试重启开发服务器

#### 常见问题

**Q: 为什么我的样式修改没有生效？**
A: 检查以下几点：
1. 是否在页面根元素添加了命名空间类（如 `className="page home-page"`）？
2. 样式选择器是否正确使用了命名空间（如 `.home-page .card`）？
3. 是否在 `styles.css` 中正确导入了样式文件？
4. 是否重启了开发服务器？

**Q: 如何修改全局共享组件的样式？**
A: 在 `styles.css` 中定义通用组件样式（如 `.btn`、`.card`），**不要**使用命名空间。如果某个页面需要特殊样式，使用命名空间覆盖：
```css
/* 全局样式 */
.card {
  padding: 20px;
}

/* 首页特殊样式 */
.home-page .card {
  padding: 24px;
}
```

### 开发脚本

```bash
# 开发模式（热更新）
npm run dev

# 构建生产版本
npm run build

# 预览生产版本（验证样式）
npm run preview

# 验证样式（构建+预览）
npm run verify:styles
```

## 核心功能模块

### 1. 应用展示

- **集团应用**：预制的集团级AI应用展示
- **省内应用**：河北省内各单位自研AI应用
- **应用榜单**：龙虎榜展示（优秀应用榜、趋势榜）

### 2. 应用申报流程

```
用户申报 → 管理员审核 → 创建省内 App → 单独配置是否参评
```

- 支持图片上传和预览
- 表单验证（必填项、格式、长度）
- 申报状态跟踪与审批审计
- 审批通过时自动创建 `AppRankingSetting`，默认 `is_enabled=false`

### 3. 排行榜管理

- 榜单类型与维度均由后台配置管理，不再把固定规则写死在文档中。
- 榜单配置由 `RankingConfig` 管理。
- 应用是否参与某个榜单由 `AppRankingSetting` 决定。
- 维度分数由 `AppDimensionScore` 存储。
- 对外展示真相源为 `HistoricalRanking` 快照；读取默认取指定日期的最新 `run_id`。

### 4. 历史榜单

- 通过 `/api/rankings/sync` 发布快照
- 支持按日期与 `run_id` 回放
- 支持历史榜单查询与可用日期查询

## 后端 API

### 鉴权与用户
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 当前登录用户
- `POST /api/auth/logout` - 登出
- `GET /api/admin/users` - 用户列表
- `PUT /api/admin/users/{id}/role` - 调整角色
- `PUT /api/admin/users/{id}/status` - 启停用户

### 应用管理
- `GET /api/apps` - 应用列表（支持 section/status/category/q 过滤）
- `GET /api/apps/{id}` - 应用详情
- `PUT /api/apps/{id}/ranking-params` - 更新应用排行参数
- `PUT /api/apps/{id}/dimension-scores/{dimension_id}` - 更新维度评分
- `POST /api/apps/{app_id}/ranking-settings` - 创建应用参评配置
- `POST /api/apps/{app_id}/ranking-settings/save` - 原子保存参评设置与维度分数

### 榜单管理
- `GET /api/rankings` - 当前榜单数据
- `GET /api/rankings/historical` - 历史榜单查询
- `GET /api/rankings/available-dates` - 可用历史日期
- `POST /api/rankings/sync` - 同步排行榜数据
- `GET /api/ranking-configs` - 榜单配置列表
- `POST /api/ranking-configs` - 创建榜单配置
- `PUT /api/ranking-configs/{id}` - 更新榜单配置
- `DELETE /api/ranking-configs/{id}` - 删除榜单配置

### 排行维度
- `GET /api/ranking-dimensions` - 维度列表
- `POST /api/ranking-dimensions` - 创建维度
- `PUT /api/ranking-dimensions/{id}` - 更新维度
- `DELETE /api/ranking-dimensions/{id}` - 删除维度
- `GET /api/ranking-dimensions/{id}/scores` - 维度评分列表

### 应用申报
- `GET /api/submissions` - 申报列表
- `POST /api/submissions` - 提交申报
- `POST /api/submissions/{id}/approve-and-create-app` - 审核通过

### 图片上传
- `POST /api/upload/image` - 上传图片
- `POST /api/submissions/{id}/images` - 关联图片
- `GET /api/submissions/{id}/images` - 获取图片列表

## 数据结构

### 核心表

| 表 | 说明 | 主要字段 |
| --- | --- | --- |
| `apps` | 应用基础信息 | name, org, section, category, status, monthly_calls, approved_at |
| `ranking_configs` | 榜单配置 | id, name, dimensions_config, calculation_method, is_active |
| `app_ranking_settings` | 应用参评配置 | app_id, ranking_config_id, is_enabled, weight_factor, custom_tags |
| `rankings` | 当前榜单 | ranking_config_id, ranking_type, position, app_id, tag, score |
| `historical_rankings` | 历史榜单快照 | period_date, run_id, ranking_config_id, position, app_id, score |
| `ranking_dimensions` | 排行维度 | name, description, calculation_method, weight, is_active |
| `app_dimension_scores` | 维度评分 | app_id, ranking_config_id, dimension_id, period_date, score |
| `submissions` | 申报记录 | app_name, unit_name, status, approved_at, approved_by_user_id |
| `submission_images` | 申报图片 | submission_id, image_url, thumbnail_url |
| `users` / `auth_sessions` | 用户与会话 | username, role, token_jti, expires_at |
| `action_logs` | 审计日志 | actor_user_id, action, resource_type, resource_id |

## 前端页面

### 主要页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 应用展示、搜索、筛选 |
| 申报指南 | `/guide` | 申报流程说明 |
| 榜单规则 | `/rule` | 排行榜规则说明 |
| 排行榜管理 | `/ranking-management` | 维度管理、应用配置 |
| 申报审核 | `/submission-review` | 审核申报、通过/拒绝 |
| 历史榜单 | `/historical-ranking` | 查询历史排名 |

### 交互特性

- 流畅的弹窗动画
- 悬停效果
- 响应式布局
- 表单验证
- 图片上传预览

## 开发与提交流程

请先阅读并遵循项目内的工作流程说明：`docs/dev-workflow.md`，包含分支命名、PR 流程及数据库切换方式。

- 一个分支对应一个 PR，后续修改持续 push 到该分支，再由 PR 页面合并。
- 分支命名：`snapshot/*`、`fix/*`、`feat/*`、`port/*`。

## 更新日志

详见 [docs/CHANGELOG.md](docs/CHANGELOG.md)

## 项目状态

当前版本：v2.1

### 已实现功能

- ✅ 应用展示（集团/省内/榜单）
- ✅ 应用申报（完整表单+图片上传）
- ✅ 申报审核（通过/拒绝）
- ✅ 登录、会话鉴权与管理员能力
- ✅ 配置化榜单管理（榜单配置 / 维度 / 应用参评设置）
- ✅ 历史榜单快照与 `run_id` 回放
- ✅ 搜索和筛选
- ✅ 响应式布局
- ✅ MySQL Only + Alembic + 显式 bootstrap 初始化

### 待优化项

- [ ] 性能优化（大数据量分页）
- [ ] 缓存策略
- [ ] 更丰富的图表展示
- [ ] 更细粒度的 RBAC

## 联系方式

- 项目邮箱：aiapps@hebei.cn
- 最近更新时间：2026-03-18

## 开发文档
- Backend 环境与自检：docs/dev-setup.md
  - Linux：`bash backend/scripts/dev/doctor.sh`
  - Windows：`powershell -ExecutionPolicy Bypass -File backend\scripts\dev\doctor.ps1`

## 推荐使用 make 命令进行本地开发与验证

```bash
cp backend/.env.example backend/.env
make db-up
make venv
make backend-install
make frontend-install
cd backend && PYTHONPATH=. ../.venv/bin/alembic upgrade head
cd backend && PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
make backend-dev
make frontend-dev
make test
```

## 推荐使用 make 命令进行准生产启动

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env: DATABASE_URL, ENVIRONMENT=production, APP_PORT
make backend-install
make frontend-install
cd backend && PYTHONPATH=. ../.venv/bin/alembic upgrade head
cd backend && PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
cd ..
make app-serve
```
