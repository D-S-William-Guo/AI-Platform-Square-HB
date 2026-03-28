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

### 开发机

```bash
git checkout main
git pull origin main
make frontend-install
make frontend-build
make release-bundle
```

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
