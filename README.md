# AI-Platform-Square-HB

企业内部 **AI 应用广场** 全栈实现（需求确认版 MVP）。

## 技术栈

- 前端：React + TypeScript + Vite
- 后端：Python FastAPI + SQLAlchemy
- 数据库：MySQL（生产建议）/ SQLite（本地快速启动默认）

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
│   ├── migrations/    # 数据库迁移脚本
│   └── requirements.txt
├── docs/              # 项目文档
│   ├── ai-app-square-requirement-prompt.md
│   ├── dev-workflow.md
│   └── CHANGELOG.md   # 更新日志
└── README.md
```

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

后端目录相关配置（可选，均有默认值）：
- `STATIC_DIR`（默认：`static`）
- `UPLOAD_DIR`（默认：`static/uploads`）
- `IMAGE_DIR`（默认：`static/images`）
- 以上相对路径统一以 `backend/` 目录为基准解析（与启动时 cwd 无关），也可配置为绝对路径。
- 启动校验要求：`UPLOAD_DIR` 必须解析到 `STATIC_DIR/uploads`，否则服务将启动失败并提示配置错误（避免返回 `/static/uploads/...` 出现 404）。

### 后端最小验证（建议）

```bash
curl -sS http://127.0.0.1:8000/api/health
```

期望返回：`{"status":"ok"}`

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
用户申报 → 管理员审核 → 应用上架 → 参与排行
```

- 支持图片上传和预览
- 表单验证（必填项、格式、长度）
- 申报状态跟踪

### 3. 排行榜管理

#### 5个排行维度

| 维度 | 权重 | 计算方法 |
|------|------|---------|
| 用户满意度 | 3.0 | 基于月调用量计算 |
| 业务价值 | 2.5 | 基于成效类型计算 |
| 技术创新性 | 2.0 | 基于难度等级计算 |
| 使用活跃度 | 1.5 | 基于月调用量计算 |
| 稳定性和安全性 | 1.0 | 基于应用状态计算 |

#### 榜单类型

- **优秀应用榜**：综合评分排名
- **趋势榜**：增长趋势排名

#### 配置方式

- 以应用为单位配置榜单参数
- 支持优秀榜和趋势榜分开配置
- 可手动调整维度评分
- 实时同步排行榜数据

### 4. 历史榜单

- 每日自动保存榜单快照
- 支持按日期查询历史排名
- 支持按维度筛选历史数据

## 后端 API

### 应用管理
- `GET /api/apps` - 应用列表（支持 section/status/category/q 过滤）
- `GET /api/apps/{id}` - 应用详情
- `PUT /api/apps/{id}/ranking-params` - 更新应用排行参数
- `PUT /api/apps/{id}/dimension-scores/{dimension_id}` - 更新维度评分

### 榜单管理
- `GET /api/rankings` - 当前榜单数据
- `GET /api/rankings/historical` - 历史榜单查询
- `GET /api/rankings/available-dates` - 可用历史日期
- `POST /api/rankings/sync` - 同步排行榜数据

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
| `apps` | 应用基础信息 | name, org, section, category, status, monthly_calls, ranking_enabled, ranking_weight |
| `rankings` | 当前榜单 | ranking_type, position, app_id, tag, score, value_dimension |
| `historical_rankings` | 历史榜单 | period_date, ranking_type, position, app_id, score |
| `ranking_dimensions` | 排行维度 | name, description, calculation_method, weight, is_active |
| `app_dimension_scores` | 维度评分 | app_id, dimension_id, period_date, score |
| `submissions` | 申报记录 | app_name, unit_name, status, created_at |
| `submission_images` | 申报图片 | submission_id, image_url, thumbnail_url |

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

当前版本：v2.0

### 已实现功能

- ✅ 应用展示（集团/省内/榜单）
- ✅ 应用申报（完整表单+图片上传）
- ✅ 申报审核（通过/拒绝）
- ✅ 排行榜管理（5维度+双榜单）
- ✅ 历史榜单查询
- ✅ 搜索和筛选
- ✅ 响应式布局

### 待优化项

- [ ] 性能优化（大数据量分页）
- [ ] 缓存策略
- [ ] 更丰富的图表展示
- [ ] 用户权限管理

## 联系方式

- 项目邮箱：aiapps@hebei.cn
- 最近更新时间：2026-02-10
