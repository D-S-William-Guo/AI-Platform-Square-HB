# 前后端需求对齐清单（v1）

> 用途：逐条确认并冻结，确认后进入下一轮编码。
> 范围：AI 应用广场（列表、榜单、详情抽屉、申报）

## A. 接口字段冻结清单（v1）

### 1) GET `/api/apps`（应用列表）

**Query 参数**

| 字段 | 类型 | 必填 | 说明 | 当前值域 |
|---|---|---:|---|---|
| section | string | 否 | 数据域过滤 | `group` / `province` |
| status | string | 否 | 可用性过滤 | `available` / `approval` |
| category | string | 否 | 分类过滤 | `办公类`/`业务前台`/`运维后台`/`企业管理` |
| q | string | 否 | 名称/描述关键词 | 任意字符串 |

**Response Item（AppDetail）**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | number | 是 | 应用ID |
| name | string | 是 | 应用名称 |
| org | string | 是 | 归属单位 |
| section | string | 是 | 分区（集团/省内） |
| category | string | 是 | 分类 |
| description | string | 是 | 简介 |
| status | string | 是 | 状态（可用/需申请） |
| monthly_calls | number | 是 | 月调用量（单位k） |
| release_date | string(date) | 是 | 上线日期 |
| api_open | boolean | 是 | API是否开放 |
| difficulty | string | 是 | 接入难度（Low/Medium/High） |
| contact_name | string | 是 | 维护联系人 |
| highlight | string | 是 | 亮点文案 |

---

### 2) GET `/api/apps/{app_id}`（应用详情）

- 入参：`app_id`（path，number）
- 出参：同 `AppDetail`
- 异常：`404 App not found`

---

### 3) GET `/api/rankings`（榜单）

**Query 参数**

| 字段 | 类型 | 必填 | 说明 | 当前值域 |
|---|---|---:|---|---|
| ranking_type | string | 否 | 榜单类型 | `excellent` / `trend`（默认 excellent） |

**Response Item（RankingItem）**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| position | number | 是 | 名次 |
| tag | string | 是 | 标签（历史优秀/推荐/新星） |
| score | number | 是 | 趋势分值（示例按增长率） |
| declared_at | string(date) | 是 | 申报日期 |
| app | object | 是 | 应用对象（AppBase） |

---

### 4) GET `/api/recommendations`（本期推荐）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| title | string | 是 | 应用名称 |
| scene | string | 是 | 场景一句话 |

---

### 5) GET `/api/stats`（申报统计）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| pending | number | 是 | 待审核数量 |
| approved_period | number | 是 | 本期通过数量 |
| total_apps | number | 是 | 累计应用数量 |

---

### 6) GET `/api/rules`（快速规则）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| title | string | 是 | 规则标题 |
| href | string | 是 | 跳转链接 |

---

### 7) POST `/api/submissions`（我要申报）

**Request**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| app_name | string | 是 | 申报应用名 |
| unit_name | string | 是 | 申报单位 |
| contact | string | 是 | 联系人 |

**Response（SubmissionOut）**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | number | 是 | 主键 |
| app_name | string | 是 | 应用名 |
| unit_name | string | 是 | 单位名 |
| contact | string | 是 | 联系人 |
| status | string | 是 | 状态（默认 pending） |
| created_at | string(datetime) | 是 | 创建时间 |

---

## B. 页面状态机清单（v1）

### 1) 顶层导航状态机

- 状态：`group` / `province` / `ranking`
- 事件：点击左侧导航项
- 转移：
  - 任意状态 -> `group`：加载 `GET /api/apps?section=group`
  - 任意状态 -> `province`：加载 `GET /api/apps?section=province`
  - 任意状态 -> `ranking`：加载 `GET /api/rankings?ranking_type=excellent`

### 2) 列表筛选状态机（group/province）

- 状态变量：`statusFilter`, `categoryFilter`, `keyword`
- 事件：选择状态、选择分类、输入关键词
- 副作用：重新请求 `/api/apps`（query 参数联动）

### 3) 榜单切换状态机（ranking）

- 状态：`excellent` / `trend`
- 事件：点击“优秀应用榜”或“趋势榜”
- 副作用：请求 `/api/rankings?ranking_type=...`

### 4) 详情抽屉状态机（Side Sheet）

- 状态：`closed` / `open(appId)`
- 事件：点击应用卡片或榜单行 -> `open`
- 事件：点击遮罩 -> `closed`

### 5) 申报流程状态机（当前MVP）

- 状态：`idle` -> `submitting` -> `success | failed`
- 事件：点击“我要申报”并提交表单
- 接口：`POST /api/submissions`
- 说明：当前 UI 尚未接入完整申报弹窗，本状态机作为下一轮实现基线

---

## C. 待你逐条确认的问题（v1 -> v2）

1. `status` 是否固定为 `available/approval`，还是要扩展 `offline`、`beta`？
2. 榜单 `score` 语义是否固定为“增长率%”？是否需要同时返回 `likes`？
3. `POST /api/submissions` 是否要加字段：`scenario`, `data_level`, `expected_benefit`？
4. 规则链接 `href` 是否接 OA 内部地址（需配置白名单）？
5. 是否需要“集团应用/省内应用”分表，还是继续单表 + `section` 枚举？
