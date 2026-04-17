# 开发与发布流程

## 分支规则

- `main`：始终保持可发布
- 功能/修复/文档改动统一走独立分支
- 一个分支只对应一个 PR

推荐分支前缀：

- `feat/*`
- `fix/*`
- `docs/*`
- `chore/*`
- `refactor/*`

## 标准流程

### 1. 从最新 main 开分支

```bash
git checkout main
git pull origin main
git checkout -b chore/your-change
```

### 2. 开发与提交

```bash
git add .
git commit -m "chore: your change"
git push -u origin chore/your-change
```

### 3. 开 PR

```bash
gh pr create --base main --head chore/your-change --fill
```

### 4. 合并后清理

```bash
git checkout main
git pull origin main
git branch -d chore/your-change
git fetch origin --prune
```

## 当前发布流程

当前正式部署不再依赖远程主机构建前端。

前端发布支持两类构建形态：

- 根路径模式：应用直接作为独立入口对外访问，构建基路径使用 `/`
- 子路径模式：应用挂在已有入口的某个前缀路径下，构建基路径使用对应前缀（例如 `/some-prefix/`）

无论前置代理与应用是否在同一主机，本次规则都只关注“外部入口是否以子路径挂载应用”：

- 同主机不同端口，由前置 Nginx/网关按子路径反代到应用服务，适用
- 不同主机之间，由网关/反向代理按子路径转发到应用服务，适用
- 若未来改为独立域名、独立端口且直接运行在根路径 `/`，继续使用默认构建即可

注意：

- `FRONTEND_BASE_PATH` 是前端构建期变量，不写入 `backend/.env` 作为后端运行时真相源
- 后端公开 API 前缀仍保持 `/api`
- 子路径模式下，前端页面路由、前端 API 与媒体资源统一跟随同一前缀
- 子路径模式下，推荐把整个应用收敛到同一前缀下，例如：
  - 页面入口：`/AISquare/`
  - API 入口：`/AISquare/api/...`
  - 媒体资源：`/AISquare/api/static/...`
- 这样部署时不会额外抢占宿主站点根路径 `/api`，更适合挂到已有系统或他人 Nginx 下

### 开发机

```bash
git checkout main
git pull origin main
make frontend-install
make frontend-build
make release-bundle
```

如需构建子路径发布物，可在构建命令前临时指定前端基路径：

```bash
FRONTEND_BASE_PATH=/some-prefix/ make frontend-build
FRONTEND_BASE_PATH=/some-prefix/ make release-bundle
```

未指定 `FRONTEND_BASE_PATH` 时，默认按根路径 `/` 构建。

如果本次目标就是挂载到 `/AISquare/`，开发机可直接使用：

```bash
git checkout main
git pull origin main
make frontend-install
FRONTEND_BASE_PATH=/AISquare/ make frontend-build
FRONTEND_BASE_PATH=/AISquare/ make release-bundle
```

构建完成后，发布包中的前端页面、API 与媒体资源都会统一走 `/AISquare/` 前缀。

当前已验证的远程场景：

- 远程应用服务运行在 `127.0.0.1:30888`
- 宿主 Nginx 对外入口为 `:38878`
- 外部访问路径为 `/AISquare/`
- 该场景下应用已完成远程启动与页面访问验证

### 远程主机

```bash
tar -xzf ai-platform-square-hb-*.tar.gz
cp backend/.env.example backend/.env
make venv
make backend-install
make app-run
```

如为更新已有服务，推荐使用以下顺序：

```bash
make service-stop
tar -xzf ai-platform-square-hb-*.tar.gz
# 如已有 backend/.env，保留现有配置，不要用示例文件覆盖
make venv
make backend-install
make service-start
```

为降低长时间运行后的登录抖动，建议在 `backend/.env` 增加以下运行参数：

```bash
UVICORN_WORKERS=2
DB_POOL_SIZE=10
DB_POOL_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=10
DB_POOL_RECYCLE_SECONDS=300
DB_CONNECT_TIMEOUT=5
DB_READ_TIMEOUT=10
DB_WRITE_TIMEOUT=10
```

如果你是通过覆盖现有目录更新源码，也遵循同样原则：

- 先停服务
- 再替换源码/发布物
- 保留现有 `backend/.env`
- 最后重新启动服务

正式常驻服务统一走：

```bash
make service-install
make service-start
```

### 代理层建议

子路径发布时，代理层应把应用前缀整段转发给运行中的应用服务，例如 `/AISquare/ -> 127.0.0.1:30888`。

推荐目标是让以下路径都能从同一个外部前缀访问：

- `/AISquare/`
- `/AISquare/assets/...`
- `/AISquare/api/...`
- `/AISquare/api/static/...`

这样可保证页面、接口、上传文件与图片预览都落在同一命名空间下。

如果宿主 Nginx 还承载其他系统，优先保持 AI 广场只占用 `/AISquare/` 这一整棵路径，不再额外暴露宿主根路径 `/api`。
