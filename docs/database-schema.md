# 数据库表结构文档

## ER 图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI应用广场数据库                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│      apps       │         │    rankings     │         │  submissions    │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ PK id           │◄────────┤ PK id           │         │ PK id           │
│    name         │    1:N  │ FK app_id       │         │    app_name     │
│    org          │         │    ranking_type │         │    unit_name    │
│    section      │         │    position     │         │    contact      │
│    category     │         │    tag          │         │    status       │
│    description  │         │    score        │         │    category     │
│    status       │         │    metric_type  │         │    scenario     │
│    monthly_calls│         │    declared_at  │         │    created_at   │
│    ranking_*    │         └─────────────────┘         └─────────────────┘
└─────────────────┘                  │
         │                           │
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│ app_dimension_  │         │ historical_     │
│     scores      │         │   rankings      │
├─────────────────┤         ├─────────────────┤
│ PK id           │         │ PK id           │
│ FK app_id       │         │ FK app_id       │
│ FK dimension_id │         │    ranking_type │
│    score        │         │    period_date  │
│    weight       │         │    position     │
│    period_date  │         │    score        │
└─────────────────┘         └─────────────────┘
         │
         │
         ▼
┌─────────────────┐
│ ranking_        │
│  dimensions     │
├─────────────────┤
│ PK id           │
│    name         │
│    weight       │
│    description  │
│    is_active    │
└─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│ submission_     │         │   ranking_logs  │
│    images       │         ├─────────────────┤
├─────────────────┤         │ PK id           │
│ PK id           │         │ FK app_id       │
│ FK submission_id│         │    action       │
│    image_url    │         │    old_value    │
│    is_cover     │         │    new_value    │
└─────────────────┘         │    created_at   │
                            └─────────────────┘
```

## 表结构详细说明

### 1. apps - 应用表

存储所有AI应用的基本信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| name | String(120) | 应用名称 | Not Null |
| org | String(60) | 所属组织 | Not Null |
| section | String(20) | 区域 | Not Null, group/province |
| category | String(30) | 分类 | Not Null |
| description | Text | 描述 | Not Null |
| status | String(20) | 状态 | Not Null, available/approval/beta/offline |
| monthly_calls | Float | 月调用量 | Not Null |
| release_date | Date | 发布日期 | Not Null |
| api_open | Boolean | 是否开放API | Default: False |
| difficulty | String(20) | 难度等级 | Default: Low |
| ranking_enabled | Boolean | 是否参与排行 | Default: True |
| ranking_weight | Float | 排行权重 | Default: 1.0 |
| ranking_tags | String(255) | 排行标签 | Default: "" |

**索引**: id (Primary Key)

### 2. rankings - 排行榜表

存储当前排行榜数据。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| ranking_type | String(20) | 榜单类型 | Not Null, excellent/trend |
| position | Integer | 排名位置 | Not Null |
| app_id | Integer | 应用ID | FK → apps.id |
| tag | String(20) | 标签 | Default: "推荐" |
| score | Integer | 综合得分 | Default: 0 |
| likes | Integer | 点赞数 | Nullable |
| metric_type | String(20) | 指标类型 | Default: composite |
| value_dimension | String(40) | 价值维度 | Default: cost_reduction |
| usage_30d | Integer | 30天使用量 | Default: 0 |
| declared_at | Date | 榜单日期 | Not Null |
| updated_at | DateTime | 更新时间 | Auto Update |

**索引**: id (Primary Key), app_id (Foreign Key)

### 3. submissions - 申报表

存储应用申报信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| app_name | String(120) | 应用名称 | Not Null |
| unit_name | String(120) | 单位名称 | Not Null |
| contact | String(80) | 联系人 | Not Null |
| category | String(30) | 分类 | Not Null |
| scenario | String(500) | 应用场景 | Not Null |
| problem_statement | String(255) | 问题描述 | Not Null |
| effectiveness_type | String(40) | 成效类型 | Not Null |
| data_level | String(10) | 数据层级 | Not Null, L1/L2/L3/L4 |
| status | String(20) | 申报状态 | Default: pending |
| cover_image_url | String(500) | 封面图URL | Default: "" |
| created_at | DateTime | 创建时间 | Auto |

**索引**: id (Primary Key)

### 4. submission_images - 申报图片表

存储申报相关的图片。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK |
| submission_id | Integer | 申报ID | FK → submissions.id |
| image_url | String(500) | 图片URL | Not Null |
| thumbnail_url | String(500) | 缩略图URL | Default: "" |
| is_cover | Boolean | 是否封面 | Default: False |
| created_at | DateTime | 创建时间 | Auto |

**索引**: id (Primary Key), submission_id (Foreign Key)

### 5. ranking_dimensions - 排行榜维度表

存储排行榜评分维度定义。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK |
| name | String(50) | 维度名称 | Not Null, Unique |
| weight | Float | 维度权重 | Not Null |
| description | String(255) | 描述 | Default: "" |
| is_active | Boolean | 是否启用 | Default: True |

**索引**: id (Primary Key)

**预置维度**:
1. 用户满意度 (weight: 0.25)
2. 业务价值 (weight: 0.25)
3. 技术创新性 (weight: 0.20)
4. 使用活跃度 (weight: 0.20)
5. 稳定性和安全性 (weight: 0.10)

### 6. app_dimension_scores - 应用维度评分表

存储应用在各维度的详细评分。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK |
| app_id | Integer | 应用ID | FK → apps.id |
| dimension_id | Integer | 维度ID | FK → ranking_dimensions.id |
| dimension_name | String(50) | 维度名称 | Not Null |
| score | Integer | 得分 | Not Null |
| weight | Float | 权重 | Not Null |
| calculation_detail | Text | 计算详情 | Default: "" |
| period_date | Date | 统计日期 | Not Null |
| updated_at | DateTime | 更新时间 | Auto |

**索引**: id (Primary Key), app_id, dimension_id, period_date (Composite)

### 7. historical_rankings - 历史排行榜表

存储历史排行榜快照。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK |
| ranking_type | String(20) | 榜单类型 | Not Null |
| period_date | Date | 榜单日期 | Not Null |
| position | Integer | 排名 | Not Null |
| app_id | Integer | 应用ID | FK → apps.id |
| app_name | String(120) | 应用名称 | Not Null |
| app_org | String(60) | 所属组织 | Not Null |
| tag | String(20) | 标签 | Default: "" |
| score | Integer | 得分 | Default: 0 |
| metric_type | String(20) | 指标类型 | Default: composite |

**索引**: id (Primary Key), ranking_type + period_date (Composite)

### 8. ranking_logs - 排行榜操作日志表

存储排行榜相关操作日志。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK |
| app_id | Integer | 应用ID | FK → apps.id |
| action | String(50) | 操作类型 | Not Null |
| old_value | Text | 旧值 | Nullable |
| new_value | Text | 新值 | Nullable |
| created_at | DateTime | 创建时间 | Auto |

**索引**: id (Primary Key), app_id (Foreign Key)

## 关系说明

### 一对多关系 (1:N)

1. **apps → rankings**: 一个应用可以出现在多个榜单中
2. **apps → app_dimension_scores**: 一个应用有多个维度评分
3. **apps → historical_rankings**: 一个应用有多个历史排名记录
4. **apps → ranking_logs**: 一个应用有多个操作日志
5. **submissions → submission_images**: 一个申报可以有多个图片
6. **ranking_dimensions → app_dimension_scores**: 一个维度对应多个应用评分

### 数据流

```
应用申报流程:
submissions (pending) → submissions (approved) → apps (created)

排行榜计算流程:
apps → app_dimension_scores (按维度计算) → rankings (生成排名) → historical_rankings (保存历史)
```

## 性能优化建议

1. **索引优化**:
   - `apps`: (section, status, category) 复合索引用于列表查询
   - `rankings`: (ranking_type, score DESC) 用于排名排序
   - `historical_rankings`: (ranking_type, period_date) 用于历史查询

2. **分区建议**:
   - `historical_rankings` 可按 `period_date` 进行按月分区
   - `app_dimension_scores` 可按 `period_date` 进行按月分区

3. **归档策略**:
   - 历史榜单数据超过1年的可归档到冷存储
   - 维度评分数据超过6个月的可归档
