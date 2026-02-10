# 三层架构排行榜系统设计文档

## 1. 设计背景与目标

### 1.1 当前问题
- 维度权重全局化，无法为不同榜单设置不同权重
- 应用配置不区分榜单，无法单独控制参与某个榜单
- 新增维度成本高，需要修改多处代码
- 缺乏增长相关维度（增长率、用户增长等）

### 1.2 设计目标
- 实现维度、榜单、应用配置的解耦
- 支持灵活配置不同榜单的维度权重
- 支持应用独立配置参与哪些榜单
- 提供良好的可扩展性，新增维度/榜单只需配置

---

## 2. 三层架构设计

### 2.1 架构概览

```
┌─────────────────────────────────────────┐
│  Layer 1: 维度定义层 (Dimensions)        │
│  - 定义有哪些维度可用                    │
│  - 维度的基础信息（名称、描述）           │
│  - 维度的计算方式                        │
│  - 不包含权重                            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 2: 榜单配置层 (RankingConfigs)    │
│  - 榜单ID (excellent, trend, ...)       │
│  - 榜单名称                              │
│  - 包含哪些维度 + 各维度权重              │
│  - 计算规则（综合评分/增长率等）          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 3: 应用参与层 (AppRankingSettings)│
│  - 应用ID                                │
│  - 榜单ID                                │
│  - 是否参与                              │
│  - 该榜单的权重系数                      │
│  - 该榜单的标签                          │
└─────────────────────────────────────────┘
```

### 2.2 数据模型设计

#### 2.2.1 维度定义表 (ranking_dimensions)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 维度ID |
| name | VARCHAR(100) | 维度名称（唯一） |
| description | TEXT | 维度描述 |
| calculation_method | TEXT | 计算方法说明 |
| calculation_logic | VARCHAR(50) | 计算逻辑标识（用于代码路由） |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**现有维度迁移：**
- 用户满意度 (user_satisfaction)
- 业务价值 (business_value)
- 技术创新性 (tech_innovation)
- 使用活跃度 (usage_activity)
- 稳定性和安全性 (stability_security)

**新增维度：**
- 增长趋势 (growth_trend)
- 用户增长 (user_growth)
- 市场热度 (market_heat)

#### 2.2.2 榜单配置表 (ranking_configs) ⭐新增

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) PK | 榜单ID (excellent, trend) |
| name | VARCHAR(100) | 榜单名称 |
| description | TEXT | 榜单说明 |
| dimensions | JSON | 维度配置 [{"dim_id": 1, "weight": 2.5}, ...] |
| calculation_method | VARCHAR(50) | 计算方法 |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**示例数据：**

```json
// 优秀应用榜
{
  "id": "excellent",
  "name": "优秀应用榜",
  "description": "综合评分排名，展示最优秀的AI应用",
  "dimensions": [
    {"dim_id": 1, "weight": 2.5},  // 用户满意度
    {"dim_id": 2, "weight": 3.0},  // 业务价值
    {"dim_id": 3, "weight": 2.5},  // 技术创新性
    {"dim_id": 4, "weight": 1.5},  // 使用活跃度
    {"dim_id": 5, "weight": 1.5}   // 稳定性
  ],
  "calculation_method": "weighted_sum",
  "is_active": true
}

// 趋势榜
{
  "id": "trend",
  "name": "趋势榜",
  "description": "增长趋势排名，展示最具潜力的AI应用",
  "dimensions": [
    {"dim_id": 1, "weight": 1.5},  // 用户满意度
    {"dim_id": 4, "weight": 2.0},  // 使用活跃度
    {"dim_id": 6, "weight": 3.5},  // 增长趋势
    {"dim_id": 7, "weight": 2.5},  // 用户增长
    {"dim_id": 8, "weight": 1.5}   // 市场热度
  ],
  "calculation_method": "weighted_sum",
  "is_active": true
}
```

#### 2.2.3 应用榜单设置表 (app_ranking_settings) ⭐新增

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 设置ID |
| app_id | INT FK | 应用ID |
| ranking_id | VARCHAR(50) FK | 榜单ID |
| enabled | BOOLEAN | 是否参与该榜单 |
| weight_multiplier | FLOAT | 权重系数 (0.1-10.0) |
| tags | VARCHAR(255) | 该榜单的标签 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**唯一约束：** (app_id, ranking_id)

**示例数据：**

```json
// AI会议助手 - 参与优秀榜，不参与趋势榜
{
  "app_id": 7,
  "ranking_id": "excellent",
  "enabled": true,
  "weight_multiplier": 1.2,
  "tags": "推荐"
}

{
  "app_id": 7,
  "ranking_id": "trend",
  "enabled": false,
  "weight_multiplier": 1.0,
  "tags": ""
}
```

---

## 3. 维度详细设计

### 3.1 现有维度（迁移）

| 维度ID | 名称 | 计算逻辑 | 数据依赖 |
|--------|------|---------|---------|
| 1 | 用户满意度 | monthly_calls × 10 | apps.monthly_calls |
| 2 | 业务价值 | 根据effectiveness_type | apps.effectiveness_type |
| 3 | 技术创新性 | 根据difficulty | apps.difficulty |
| 4 | 使用活跃度 | monthly_calls × 5 | apps.monthly_calls |
| 5 | 稳定性和安全性 | 根据status | apps.status |

### 3.2 新增维度

#### 3.2.1 增长趋势 (growth_trend)

| 属性 | 值 |
|------|-----|
| ID | 6 |
| 名称 | 增长趋势 |
| 计算逻辑 | (本月调用量 - 上月调用量) / 上月调用量 × 100 |
| 数据依赖 | apps.monthly_calls, apps.last_month_calls ⭐新增字段 |
| 适用榜单 | 趋势榜 |
| 建议权重 | 3.0-4.0 |

**评分规则：**
- 增长率 > 50%: 100分
- 增长率 30-50%: 80分
- 增长率 10-30%: 60分
- 增长率 0-10%: 40分
- 负增长: 20分

#### 3.2.2 用户增长 (user_growth)

| 属性 | 值 |
|------|-----|
| ID | 7 |
| 名称 | 用户增长 |
| 计算逻辑 | 本月新增用户数 |
| 数据依赖 | apps.new_users_count ⭐新增字段 |
| 适用榜单 | 趋势榜 |
| 建议权重 | 2.0-2.5 |

#### 3.2.3 市场热度 (market_heat)

| 属性 | 值 |
|------|-----|
| ID | 8 |
| 名称 | 市场热度 |
| 计算逻辑 | 搜索量 + 分享次数 + 收藏数 |
| 数据依赖 | apps.search_count, apps.share_count, apps.favorite_count ⭐新增字段 |
| 适用榜单 | 趋势榜 |
| 建议权重 | 1.5-2.0 |

---

## 4. 计算逻辑设计

### 4.1 得分计算公式

```
基础得分 = Σ(维度得分 × 维度权重)
最终得分 = 基础得分 × 应用权重系数
排名 = 按最终得分降序排列
```

### 4.2 计算流程

```python
def calculate_ranking(ranking_id: str, apps: List[App]):
    # 1. 获取榜单配置
    config = get_ranking_config(ranking_id)
    
    # 2. 获取维度配置
    dimensions = config.dimensions
    
    # 3. 计算每个应用的得分
    results = []
    for app in apps:
        # 检查应用是否参与该榜单
        setting = get_app_ranking_setting(app.id, ranking_id)
        if not setting or not setting.enabled:
            continue
            
        # 计算各维度得分
        base_score = 0
        for dim_config in dimensions:
            dimension = get_dimension(dim_config.dim_id)
            dim_score = calculate_dimension_score(app, dimension)
            weighted_score = dim_score * dim_config.weight
            base_score += weighted_score
            
        # 应用权重系数
        final_score = base_score * setting.weight_multiplier
        
        results.append({
            'app_id': app.id,
            'score': final_score,
            'tag': setting.tags
        })
    
    # 4. 排序并分配排名
    results.sort(key=lambda x: x['score'], reverse=True)
    for index, result in enumerate(results, start=1):
        result['position'] = index
        
    return results
```

---

## 5. API设计

### 5.1 榜单配置API

```
GET    /api/ranking-configs              # 获取所有榜单配置
GET    /api/ranking-configs/{id}          # 获取单个榜单配置
POST   /api/ranking-configs              # 创建榜单配置
PUT    /api/ranking-configs/{id}          # 更新榜单配置
DELETE /api/ranking-configs/{id}          # 删除榜单配置
```

### 5.2 应用榜单设置API

```
GET    /api/apps/{app_id}/ranking-settings           # 获取应用的所有榜单设置
GET    /api/apps/{app_id}/ranking-settings/{ranking_id}  # 获取单个设置
PUT    /api/apps/{app_id}/ranking-settings/{ranking_id}  # 更新设置
POST   /api/apps/batch-ranking-settings              # 批量更新
```

### 5.3 排行榜查询API（保持兼容）

```
GET /api/rankings?ranking_type=excellent  # 查询优秀榜
GET /api/rankings?ranking_type=trend      # 查询趋势榜
```

---

## 6. 数据库迁移方案

### 6.1 新增表

```sql
-- 榜单配置表
CREATE TABLE ranking_configs (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    dimensions JSON NOT NULL,
    calculation_method VARCHAR(50) DEFAULT 'weighted_sum',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 应用榜单设置表
CREATE TABLE app_ranking_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    app_id INT NOT NULL,
    ranking_id VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    weight_multiplier FLOAT DEFAULT 1.0,
    tags VARCHAR(255) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_app_ranking (app_id, ranking_id),
    FOREIGN KEY (app_id) REFERENCES apps(id),
    FOREIGN KEY (ranking_id) REFERENCES ranking_configs(id)
);
```

### 6.2 新增字段

```sql
-- 为apps表添加增长相关字段
ALTER TABLE apps ADD COLUMN last_month_calls FLOAT DEFAULT 0;
ALTER TABLE apps ADD COLUMN new_users_count INT DEFAULT 0;
ALTER TABLE apps ADD COLUMN search_count INT DEFAULT 0;
ALTER TABLE apps ADD COLUMN share_count INT DEFAULT 0;
ALTER TABLE apps ADD COLUMN favorite_count INT DEFAULT 0;
```

### 6.3 数据迁移

```sql
-- 初始化榜单配置
INSERT INTO ranking_configs (id, name, description, dimensions) VALUES
('excellent', '优秀应用榜', '综合评分排名', '[{"dim_id":1,"weight":2.5},{"dim_id":2,"weight":3.0},{"dim_id":3,"weight":2.5},{"dim_id":4,"weight":1.5},{"dim_id":5,"weight":1.5}]'),
('trend', '趋势榜', '增长趋势排名', '[{"dim_id":1,"weight":1.5},{"dim_id":4,"weight":2.0},{"dim_id":6,"weight":3.5},{"dim_id":7,"weight":2.5},{"dim_id":8,"weight":1.5}]');

-- 迁移现有应用到新表
INSERT INTO app_ranking_settings (app_id, ranking_id, enabled, weight_multiplier, tags)
SELECT 
    a.id,
    'excellent',
    a.ranking_enabled,
    a.ranking_weight,
    a.ranking_tags
FROM apps a
WHERE a.section = 'province';

-- 趋势榜默认全部参与
INSERT INTO app_ranking_settings (app_id, ranking_id, enabled, weight_multiplier, tags)
SELECT 
    a.id,
    'trend',
    TRUE,
    1.0,
    a.ranking_tags
FROM apps a
WHERE a.section = 'province';
```

---

## 7. 前端界面设计

### 7.1 榜单管理页面增强

**新增功能：**
1. 榜单配置管理（增删改查）
2. 维度权重配置（可视化调整）
3. 应用榜单设置（按榜单筛选）

### 7.2 应用配置弹窗增强

**现有：**
- 优秀榜配置
- 趋势榜配置

**新增：**
- 显示所有可用榜单
- 每个榜单独立配置：参与/不参与、权重系数、标签

---

## 8. 实施计划

### Phase 1: 数据库迁移
- [ ] 创建新表
- [ ] 添加新字段
- [ ] 数据迁移

### Phase 2: 后端开发
- [ ] 新增API接口
- [ ] 修改计算逻辑
- [ ] 单元测试

### Phase 3: 前端开发
- [ ] 榜单配置界面
- [ ] 应用设置界面
- [ ] 排行榜展示优化

### Phase 4: 测试验证
- [ ] 数据完整性测试
- [ ] 功能测试
- [ ] 性能测试

---

## 9. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 数据迁移失败 | 高 | 备份数据，分步迁移 |
| 性能下降 | 中 | 添加索引，优化查询 |
| 兼容性问题 | 中 | 保持API兼容，渐进式迁移 |

---

## 10. 附录

### 10.1 术语表

- **维度**：评分的指标项（如用户满意度、业务价值等）
- **榜单**：排行榜类型（如优秀应用榜、趋势榜）
- **权重系数**：应用级别的得分调整系数

### 10.2 参考文档

- [现有README.md](../README.md)
- [CHANGELOG.md](CHANGELOG.md)
