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
- 子路径模式下，代理层需要同时正确转发页面路由、静态资源以及 `/api`、静态文件请求

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

### 远程主机

```bash
tar -xzf ai-platform-square-hb-*.tar.gz
cp backend/.env.example backend/.env
make venv
make backend-install
make app-run
```

正式常驻服务统一走：

```bash
make service-install
make service-start
```
