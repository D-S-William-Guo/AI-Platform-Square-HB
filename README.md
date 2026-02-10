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
│   │   └── styles.css # 全局样式
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
