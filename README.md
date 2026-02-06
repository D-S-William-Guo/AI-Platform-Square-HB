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

## 需求对齐清单（持续更新）

- v1（接口字段冻结 + 页面状态机）：`docs/alignment-v1.md`
- v2-draft（5个待确认点建议决策）：`docs/alignment-v2-draft.md`
- v2-final（已确认版）：`docs/alignment-v2-final.md`
- 说明：后续每轮讨论先更新该清单，双方确认后再进入对应编码。
## 阶段性成果可视化

- 预览页面：`preview/stage-demo.html`
- 本地查看：在仓库根目录执行 `python -m http.server 8081` 后访问 `http://localhost:8081/preview/stage-demo.html`

