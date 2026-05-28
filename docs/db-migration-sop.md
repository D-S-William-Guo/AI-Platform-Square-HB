# 数据库迁移与运维 SOP

## 默认原则

- 结构变更统一走 Alembic
- 默认保留旧数据，不把清库重建做成常规流程
- 默认账号、系统榜单、系统维度都通过显式 bootstrap 命令处理
- 应用变更申请等业务表新增后，只执行 `alembic upgrade head`，不回写历史榜单快照

## 正式命令

### 1. 结构升级

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
```

### 2. 基础初始化

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
```

说明：

- `init-base` 只补基础数据
- 不覆盖已有默认账号密码
- 不覆盖已有系统榜单和系统维度默认值

### 3. 默认账号重置

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap reset-default-users
```

适用场景：

- 修改了 `USER_DEFAULT_PASSWORD`
- 修改了 `ADMIN_DEFAULT_PASSWORD`
- 旧库中 `zhangsan` / `lisi` 无法用新密码登录

要求：

- 默认密码必须满足本地强口令规则：至少 10 位，且大写字母、小写字母、数字、符号四类中至少三类
- 重置后的默认密码按临时密码处理，用户下次登录后必须先改为个人强口令

### 4. 系统预置同步

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap sync-system-presets
```

适用场景：

- 老库需要同步新的系统榜单名称
- 老库需要同步新的默认榜单维度
- 老库需要把系统维度/系统榜单权重统一改为 `1.0`

同步范围只包括：

- 系统维度
- `excellent`
- `trend`

不会修改：

- 自定义榜单
- 自定义维度
- 业务应用
- 榜单历史快照
- 应用变更申请历史

## 推荐顺序

### 新库

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap init-base
```

### 老库升级

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap sync-system-presets
```

如果默认账号密码也改了，再执行：

```bash
PYTHONPATH=. ../.venv/bin/python -m app.bootstrap reset-default-users
```

## 高风险例外路径

整库删除、清空后重建，属于 DBA / 人工确认后的高风险操作，不纳入日常部署主链路。
