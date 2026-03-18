# 开发与提交流程

> 目标：让任何人照着做都能完成一次开发、提交、PR、合并与清理。

## 1. 分支类型与命名

| 类型 | 命名示例 | 用途 | 备注 |
| --- | --- | --- | --- |
| snapshot | `snapshot/feature-optimization-001` | 问题现场快照 | 仅存档，不合并 |
| fix | `fix/ranking-rules` | 修复问题 | 允许进入 PR |
| feat | `feat/new-module` | 新功能 | 允许进入 PR |
| port | `port/ranking-rule-cleanup` | 迁移/拆分变更 | 用于从旧分支拆分有用改动 |

> **禁止** 直接在 `main` 上开发或提交。

## 2. 标准开发流程（完整闭环）

### 2.1 创建工作分支

```bash
git checkout <问题分支或主干>
git pull origin <问题分支或主干>
git checkout -b fix/<topic>
```

### 2.2 修改与提交

```bash
git status -sb
# 进行代码修改

git add <files>
git commit -m "fix(<scope>): <subject>"
```

### 2.3 推送与提 PR

```bash
git push origin fix/<topic>
```

在 GitHub 页面创建 PR：
1. Base 选择 `main`
2. Compare 选择 `fix/<topic>`
3. 填写变更说明与验证信息
4. 提交 PR

### 2.4 合并与清理

在 GitHub PR 页面进行合并（推荐 **Merge**）。
> 一个分支只对应一个 PR，后续补充改动持续 push 到同一分支，避免开多个 PR。

```bash
# 合并后清理本地
 git checkout main
 git pull origin main
 git branch -d fix/<topic>

# 删除远端分支
 git push origin --delete fix/<topic>
```

> 快照分支 `snapshot/*` 仅用于存档，不进入 PR；例如 `snapshot/feature-optimization-001` 属历史问题分支，禁止作为合并目标。

## 3. 数据库运行方式（MySQL Only）

迁移执行顺序、初始化命令与本地/远程 MySQL 最小验证步骤统一维护在：[docs/db-migration-sop.md](db-migration-sop.md)。

本文件仅保留入口：
- 后端与开发脚本统一读取 `backend/.env`；
- 根目录 `.env` 只保留 Docker Compose MySQL 变量；
- 根目录 `.env.local` 已废止；
- 测试使用 `TEST_DATABASE_URL`；
- 结构迁移统一执行 `alembic upgrade head`。

## 4. 业务数据演示规则

- 省内应用必须通过 **申报 → 审批** 产生数据；
- 应用榜单只展示省内应用；
- 排行规则以“排行榜管理”配置为准，榜单页不硬编码规则。
