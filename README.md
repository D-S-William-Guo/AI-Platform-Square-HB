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

### 0) 准备本地环境变量

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

> `.env` 提供 docker-compose MySQL 默认账号，`backend/.env` 控制后端数据库连接。

### 1) 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 1.5) 使用 Docker Compose 启动 MySQL

```bash
docker compose up -d mysql
```

### 2) 前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

## 开发与提交流程

请先阅读并遵循项目内的工作流程说明：`docs/dev-workflow.md`，包含分支命名、PR 流程及数据库切换方式。

- 一个分支对应一个 PR，后续修改持续 push 到该分支，再由 PR 页面合并。
- 分支命名：`snapshot/*`、`fix/*`、`feat/*`、`port/*`。

## 后端 API（核心）

### 应用管理
- `GET /api/apps`：应用列表（支持 section/status/category/q 过滤）
- `GET /api/apps/{id}`：应用详情
- `GET /api/rankings`：龙虎榜数据
- `GET /api/recommendations`：本期推荐
- `GET /api/stats`：申报统计

### 应用申报
- `POST /api/submissions`：提交应用申报
  - 请求体包含完整应用信息、联系人、成效评估等
  - 支持图片关联（通过 cover_image_url 字段）

### 图片上传
- `POST /api/upload/image`：上传图片文件
  - 支持格式：JPG、JPEG、PNG
  - 最大文件大小：5MB
  - 自动生成缩略图（300x200）
  - 返回：图片URL、缩略图URL、文件信息
  
- `POST /api/submissions/{submission_id}/images`：关联图片到申报
  - 参数：image_url, thumbnail_url, original_name, file_size, is_cover
  
- `GET /api/submissions/{submission_id}/images`：获取申报关联的图片列表

### 元数据
- `GET /api/meta/enums`：获取枚举值列表（应用状态、成效类型、数据级别等）

## 数据结构

### 核心表

| 表 | 说明 | 主要字段 | 关系 |
| --- | --- | --- | --- |
| `apps` | 应用基础信息 | name/org/section/category/status/monthly_calls/release_date/cover_image_url 等 | `rankings.app_id -> apps.id` |
| `rankings` | 应用榜单条目 | ranking_type/position/tag/score/likes/usage_30d/declared_at | 关联 `apps` |
| `submissions` | 申报记录 | app_name/unit_name/contact/contact_phone/contact_email/category/scenario/cover_image_id/status/created_at | 与 `apps` 暂未强关联（申报通过后可转化为 `apps`） |
| `submission_images` | 申报图片 | submission_id/image_url/thumbnail_url/original_name/file_size/is_cover | 关联 `submissions` |

### migrations（SQL 快照）

本仓库提供 `backend/migrations/001_init.sql`，用于初始化 MySQL 表结构（SQL 形式快照）。在本地快速验证可继续使用 SQLite + `Base.metadata.create_all` 的方式自动建表。若需使用 MySQL，可先执行该 SQL 文件再启动后端服务。

### 图片存储结构

```
backend/
  static/
    uploads/
      submissions/    # 申报图片
        {submission_id}/
          original/   # 原图
          thumbnail/  # 缩略图
      apps/           # 应用封面图
        {app_id}/
```

## 前端功能特性

### 应用展示
- 三栏布局：左侧导航、中央内容、右侧信息栏
- 应用卡片：封面图/渐变色背景、状态标签、分类、调用量
- 应用详情弹窗：居中模态框，展示完整应用信息

### 应用申报
- 居中模态弹窗表单
- 表单分组：基础信息、应用信息、成效评估
- 字段验证：
  - 必填项检查
  - 长度限制（实时字符计数）
  - 手机号格式验证
  - 邮箱格式验证
  - 实时错误提示
- 图片上传：
  - 点击或拖拽上传
  - 格式验证（JPG/PNG）
  - 大小限制（5MB）
  - 实时预览
  - 上传进度显示

### 交互体验
- 流畅的弹窗动画（淡入 + 上滑 + 缩放）
- 悬停效果（卡片上浮、按钮变色）
- 点击外部关闭弹窗
- 响应式布局适配

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
- 如果需要在本地执行"前后端联调"，可先按"快速启动"步骤分别拉起后端与前端。

## 阶段性成果可视化

- 预览页面：`preview/stage-demo.html`
- 本地查看：在仓库根目录执行 `python -m http.server 8081` 后访问 `http://localhost:8081/preview/stage-demo.html`

## 路由配置规范

### 概述
前端页面调整后必须同步更新路由配置，确保所有页面可正常访问。

### 更新流程
1. **页面创建**：创建新页面组件后，在 `frontend/src/App.tsx` 中添加对应路由
2. **路由配置**：使用 `React Router` 的 `Route` 组件，指定路径和对应的组件
3. **导航链接**：更新所有相关导航链接，使用 `Link` 组件替代直接 URL 跳转
4. **测试验证**：确保新路由可正常访问，无 404 错误
5. **文档更新**：在 README.md 中记录新路由信息

### 命名规范
- 路由路径使用小写字母，单词间用连字符（-）分隔
- 页面组件文件命名使用 PascalCase（如 `GuidePage.tsx`）
- 路由名称应与页面功能保持一致，便于理解和维护

### 审核机制
- 代码提交前，需检查路由配置是否完整
- 团队成员应互相审核路由变更，确保无遗漏或错误
- 集成测试应包含路由访问测试，验证所有页面可正常加载

## 更新日志

### 2024-12-11
- 新增图片上传功能（前后端完整实现）
- 重构申报表单为居中模态弹窗
- 新增表单验证功能（必填项、格式、长度）
- 新增数据库表 `submission_images`
- 更新 `apps` 和 `submissions` 表，添加图片相关字段

### 2026-02-09
- 添加路由配置规范文档
- 开发排行榜管理功能
