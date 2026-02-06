# AI-Platform-Square-HB

## Figma 原型查看记录

- 首次链接：`https://www.figma.com/make/IPHjRxBK2MVwqrl0wGXVOd/AI-App-Square-Structure?p=f&t=5nmFccCMliI64n0J-0&fullscreen=1`
- 二次链接：`https://www.figma.com/make/IPHjRxBK2MVwqrl0wGXVOd/AI-App-Square-Structure?p=f&t=lGXtqXLhnh434KDY-0`
- 三次链接（已放开权限）：`https://www.figma.com/make/IPHjRxBK2MVwqrl0wGXVOd/AI-App-Square-Structure?t=lGXtqXLhnh434KDY-1`
- 发布页面（可直接查看）：`https://coup-snare-43800026.figma.site/`

### 访问结论

1. 前两条 `figma.com/make` 链接会进入 Figma 登录/注册页。
2. 第三条 `figma.com/make` 链接可访问，不再出现 `Sign up or Log in` 拦截提示。
3. `figma.site` 发布页可直接访问，适合作为后续评审入口。

## 发布页面原型理解（初版）

### 1) 页面定位

- 面向企业内部 AI 应用“广场”场景，强调“统一展示 + 统一申报 + 榜单运营”。
- 头部具备入口动作（`我要申报`）和用户态（头像/昵称），符合 OA 单点后进入业务页面的使用方式。

### 2) 信息架构

- 顶层导航：`集团应用 / 省内应用 / 应用榜单`。
- 中层筛选：状态筛选（`全部 / 可用 / 需申请`）+ 分类筛选（`办公类 / 业务前台 / 运维后台 / 企业管理`）。
- 主体内容：应用卡片列表（示例 6 个应用），包含名称、归属单位、分类、简介、热度/月活和更新时间。

### 3) 运营模块

- `本期推荐`：突出重点应用，适合做专题曝光。
- `榜单速览`：提供 Top 排名及增长率，形成“可比较”的运营抓手。
- `申报统计`：显示待审核、已通过、累计应用，支撑管理看板诉求。
- `快速规则`：提供申报与榜单规则入口，降低使用门槛。

### 4) 与业务目标的匹配判断

- 已覆盖“找应用（浏览/筛选）→ 看价值（榜单/推荐）→ 发起动作（申报）”主链路。
- 对“企业内部应用广场”早期版本而言，这个结构完整度较高，可直接作为 IA 与页面布局基线。

### 5) 建议的下一步对齐点

- 明确 `我要申报` 的实际流转（表单字段、审批流、SLA）。
- 明确 `可用` 与 `需申请` 的权限策略（OA 组织、角色、部门边界）。
- 补齐应用详情页字段清单（能力说明、接入方式、数据安全级别、联系人）。

## 需求确认基线（Prompt）

- 已将当前阶段的页面生成提示词固化为文档：`docs/ai-app-square-requirement-prompt.md`。
- 说明：后续原型评审与前端组件拆分默认以该文档为准。

