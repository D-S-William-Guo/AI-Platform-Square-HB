# GOVERNANCE（当前定版）

## 1. 产品边界

- 对外聚焦：集团应用、省内应用、双榜单、申报入口
- 管理能力仅管理员可见，且后端必须有权限保护
- 远程部署以发布包为准，远程主机不承担前端构建

## 2. 榜单规则

- 双榜单固定为：
  - `excellent`：总应用榜
  - `trend`：增长趋势榜
- 默认核心维度：
  - 总应用榜：用户满意度、业务价值、使用活跃度、稳定性和安全性
  - 增长趋势榜：使用活跃度、增长趋势、用户增长
- 系统默认权重统一为 `1.0`
- “技术创新性”“市场热度”保留为系统维度，但不是默认榜单主维度

## 3. 真相源

- 榜单参与与控制输入唯一真相源：`AppRankingSetting`
- 对外榜单读取唯一真相源：`HistoricalRanking`
- `App` / `Submission` 中的 `ranking_*` 字段仅保留兼容或展示用途

## 4. 数据库与初始化

- 结构变更统一走 `alembic upgrade head`
- `init-base` 只负责基础初始化，不覆盖已有默认密码
- `reset-default-users` 用于显式重置 `zhangsan` / `lisi`
- `sync-system-presets` 用于显式同步系统维度与系统榜单默认值

## 5. 身份模式

- 默认身份模式：`local`
- 预留：
  - `oa`
  - `external_sso`
- 当前轮次只做统一身份适配层和登录入口预留，不直接接真实 OA / 第三方协议

## 6. 文档治理规则

- 根 `README.md` 只承担项目首页、最短入口和文档导航职责，不长期维护完整运维细节。
- `docs/README.md` 是当前有效文档索引，新增、重命名或废弃有效文档时必须同步更新。
- `AGENTS.md` 用于仓库级智能体工作约束、文档入口说明和最近关键文档变更摘要。
- `backend/scripts/README.md` 只解释脚本用途，不承担后端主入口或治理结论职责。
- `docs/archive/` 仅保留历史材料，不作为当前产品、部署或运维规则入口。

## 7. 规则变化时的同步要求

- 产品边界、榜单规则、数据真相源变化时，同步检查：
  - `docs/GOVERNANCE.md`
  - 根 `README.md`
  - `docs/README.md`
- 开发、部署、数据库命令变化时，同步检查：
  - 根 `README.md`
  - `docs/dev-setup.md`
  - `docs/dev-workflow.md`
  - `docs/db-migration-sop.md`
  - `docs/README.md`
- 文档入口或文档职责变化时，同步检查：
  - `AGENTS.md`
  - 根 `README.md`
  - `docs/README.md`
