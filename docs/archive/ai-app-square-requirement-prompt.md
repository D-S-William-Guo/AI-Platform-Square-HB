# AI 应用广场需求确认提示词（冻结稿）

> 状态：需求确认阶段（用于后续前端组件化实现与 Figma 对齐）。
> 说明：以下内容由业务方提供，作为当前阶段的页面结构基线。

# 《AI 应用广场》Figma 页面结构说明（前端可直接按此建组件）

## 🎨 1. 页面总体规格

* **页面宽度建议**：1440px（适配 OA 内嵌）
* **布局结构**：三栏（左侧导航栏 + 中央主内容区 + 右侧氛围栏）
* **栅格建议**：12 列，中央主内容区占 8 列左右
* **组件风格**：卡片式、轻量阴影、圆角 8px、配色清爽（蓝/白/灰）

---

# 🧱 2. 页面顶层结构（Figma Frame 层级）

```text
Page Frame: AI App Square (1440 x Auto)
 ├── Header
 ├── Body
 │    ├── Left Sidebar
 │    ├── Main Content
 │    └── Right Sidebar
 └── Footer
```

---

# 🔹 3. Header（顶部栏）

**Frame 名称：Header**  
**高度：72px，宽度 100%**

内容结构：

* 左：公司 LOGO（40×40）+ 标题文字“H E B E I · AI 应用广场”
* 中：搜索框（Input，长约 500px）
* 右：
  * “我要申报”按钮（Primary）
  * 用户头像（32×32）+ 下拉箭头

> 建议：Header 固定（fixed），滚动时保持可见。

---

# 🔹 4. 左侧导航栏（Left Sidebar）

**Frame 名称：Left Sidebar**  
**宽度：220px，高度自适应页面**

结构：

```text
Section: 导航
 - NavItem: 集团应用
 - NavItem: 省内应用
 - NavItem: 应用榜单

Section: 分类筛选
 - Tag/Checkbox: 办公类
 - Tag/Checkbox: 业务前台
 - Tag/Checkbox: 运维后台
 - Tag/Checkbox: 企业管理

Section: 快速入口
 - Link: 申报指南
 - Link: 榜单规则
```

交互说明：

* 选中项背景色高亮
* Hover 有轻微背景色

---

# 🔹 5. 中央主内容区（Main Content）

**Frame 名称：Main Content（建议宽度 900–1100px）**  
采用 Tab 或导航联动切换 3 个主块：

## 📌 Block A — 集团应用展示

Frame 名称：Block A – Group Apps

结构：

**A1. Block Header**

* 标题：集团应用整合
* 说明文案（12px 灰）
* 下方放筛选组件：
  * 可用状态（Dropdown）
  * 分类（Dropdown）
  * 关键词（Mini Search）

**A2. 卡片网格区（Grid）**

* 建议列数：3 或 4 列
* 卡片大小：宽 280–320px，高 180–200px

**卡片字段：**

* 应用名（16px）
* 所属单位（12px 灰）
* 分类标签（Tag）
* 封面图（小缩略图）
* 一行简述（最多 35 字）
* 状态标签（可用 / 需申请）
* 底部：关键小指标（调用量/月、上线日期）

**交互：**

* Hover 展示两个按钮（查看详情 / 申请试用）
* 点击进入右侧抽屉（Side Sheet）

## 📌 Block B — 省内可调用应用

Frame 名称：Block B – Province Apps

结构：

**B1. Header**

* 标题：河北省自研应用/可调用应用
* Tab：业务前台 / 运维后台 / 企业管理

**B2. 卡片网格（同 Block A）**

* 卡片字段增加：
  * API 是否开放（icon）
  * 接入难度（Low/Medium/High）
  * 联系人（姓名+标签）

**B3. 侧边弹出层（Side Sheet）**

* 名称：App Detail Panel
* 宽：420px
* 内容：
  * 应用名、图标
  * 场景介绍（段落）
  * 接入说明（分步骤）
  * 示例调用（代码块）
  * 维护联系人

## 📌 Block C — AI 应用龙虎榜（核心氛围）

Frame 名称：Block C – Ranking

结构：

**C1. Header**

* Tab：优秀应用榜 / 趋势榜
* 左右切换按钮（若有）

**C2. Top3 轮播区（Carousel）**

* 每张轮播卡高度 180–220px
* 字段：
  * 排名（大号数字）
  * 应用名
  * 所属单位
  * 价值亮点一句话
  * 关键指标（如节省工时、提升效率）

**C3. 排名列表（Table/List）**  
每行字段：

* 排名号
* 应用名（可展开）
* 所属单位
* 标签（历史优秀/推荐/新星）
* 申报日期
* 点赞数（趋势榜使用）

行点击 → 打开侧边详情（复用 B3 结构）

---

# 🔹 6. 右侧氛围栏（Right Sidebar）

**Frame 名称：Right Sidebar**  
**宽度：260px**

内容区块：

**D1. 本期推荐（3 张小卡）**

* 小卡：图标+标题+一句话场景

**D2. 榜单速览**

* Trending Top5（小号列表）

**D3. 申报统计（仅显示数字）**

* “待审核：12”
* “本期已通过：7”
* “累计应用：86”

**D4. 快速规则**

* 小卡片：如何申报、上榜规则（点开弹窗）

---

# 🔹 7. 页面底部（Footer）

**Frame 名称：Footer**  
内容：

* 最近更新时间：YYYY-MM-DD
* 联系邮箱
* 简短说明（如“数据来源于省公司各单位申报与集团应用目录”）

---

# 🧩 8. 组件清单（供 Figma 制作）

### 必做组件：

* Header（含搜索框 + 按钮）
* NavItem（左右导航栏）
* Tag（分类标签）
* Card – 应用卡（集团、省内通用）
* Card – 小推荐卡
* Ranking Carousel Card（Top3）
* Ranking List Row
* Side Sheet（详情抽屉）
* Tab（一级切换）
* Filter Bar（筛选区）
* OA 表单入口按钮

### 可复用统一样式：

* 8px 圆角、轻阴影
* 12/14/16 px 三层字体体系
* 图标统一 16px or 20px

---

# 📦 9. 额外提供：Figma 原型层级树（前端最爱）

```text
AI 应用广场
 ├── Header
 ├── Body
 │    ├── Left Sidebar
 │    │     ├── Nav Group
 │    │     ├── Filter Group
 │    │     └── Link Group
 │    ├── Main Content
 │    │     ├── Block A – Group Apps
 │    │     │      ├── Block Header
 │    │     │      └── Card Grid
 │    │     ├── Block B – Province Apps
 │    │     │      ├── Tabs
 │    │     │      ├── Card Grid
 │    │     │      └── Side Sheet
 │    │     └── Block C – Ranking
 │    │            ├── Tabs
 │    │            ├── Carousel
 │    │            └── Ranking List
 │    └── Right Sidebar
 │           ├── 推荐区
 │           ├── 榜单速览
 │           ├── 申报统计
 │           └── 规则卡
 └── Footer
```
