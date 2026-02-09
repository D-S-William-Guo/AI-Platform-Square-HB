# Git 工作流程规范

> 即使是单人项目，也要遵循规范的 Git 工作流程

## 分支策略

### 主分支
- `main` - 生产环境代码，始终保持稳定

### 开发分支
- `snapshot/*` - 问题现场快照，仅存档，不进入 PR
- `feature/*` - 新功能开发
- `fix/*` - Bug 修复
- `docs/*` - 文档更新
- `refactor/*` - 代码重构

## 工作流程

> 更完整的流程（含数据库切换、合并后清理规则）请参考 `docs/dev-workflow.md`。

### 1. 开始新功能

```bash
# 从 main 分支创建新分支
git checkout main
git pull origin main
git checkout -b feature/new-feature
```

### 2. 开发过程中

```bash
# 定期提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature
```

### 3. 创建 Pull Request（必须通过 GitHub Web 界面）

**禁止直接合并到 main！**

1. 打开 GitHub 仓库页面
2. 点击 "Pull requests" → "New pull request"
3. 选择源分支和目标分支
4. 填写 PR 描述（使用模板）
5. 创建 PR
6. 自我审查代码
7. 确认无误后合并

### 4. 合并后清理

```bash
# 切换到 main 分支
git checkout main
git pull origin main

# 删除本地分支
git branch -d feature/new-feature

# 删除远程分支
git push origin --delete feature/new-feature
```

## 提交信息规范

### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档
- `style`: 代码格式
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建/工具

### 示例
```
feat(api): 添加图片上传功能

- 支持 JPG/PNG 格式
- 最大文件大小 5MB
- 自动生成缩略图

Closes #123
```

## 禁止事项

- ❌ 禁止直接提交到 `main` 分支
- ❌ 禁止本地合并后推送
- ❌ 禁止跳过 PR 流程
- ❌ 禁止无意义的提交信息

## 单人项目 PR 的好处

1. **代码审查**: 给自己一个回顾代码的机会
2. **变更记录**: 清晰的变更历史
3. **回滚安全**: 发现问题可以快速回滚
4. **习惯养成**: 为团队协作做准备
5. **文档沉淀**: PR 描述成为变更文档

## 紧急修复流程

如果确实需要紧急修复：

1. 创建 `hotfix/*` 分支
2. 快速修复
3. 创建 PR
4. 简化审查流程（但仍需创建 PR）
5. 合并后立即删除分支

---

**记住：规范的工作流程是代码质量的保证！**
