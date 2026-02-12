# CSS 模块化架构文档

## 架构概述

本项目采用 **命名空间隔离** 的 CSS 模块化架构，确保页面特定样式不会相互污染，同时保持全局样式的一致性。

## 样式分层结构

### 1. 全局/基础样式 (Global/Base Styles)

**文件**: `styles.css`

**作用**: 定义整个应用的基础样式、CSS 变量、通用组件样式

**包含内容**:
- CSS 变量（颜色、间距、阴影、圆角等）
- 基础元素重置样式（body, html, *）
- 通用组件样式（按钮、卡片、表单等）
- 布局框架样式（header, footer, page-container 等）

**命名规范**:
- 使用通用类名：`.btn`, `.card`, `.modal`, `.page-container`
- 不使用命名空间前缀

**示例**:
```css
:root {
  --primary-color: #4f7cff;
  --card-bg: #ffffff;
  /* ... */
}

.btn {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  /* ... */
}
```

### 2. 页面特定样式 (Page-Specific Styles)

**文件**: `[page-name]-page.css`

**作用**: 定义特定页面的布局和组件样式，完全隔离不影响其他页面

**包含内容**:
- 页面布局（grid/flex 布局）
- 页面特定组件样式
- 页面状态样式

**命名规范**:
- **必须使用命名空间前缀**：`.[page-name]-page`
- 所有选择器都以页面根类名开头

**现有页面样式文件**:
- `home-page.css` - 首页样式（命名空间：`.home-page`）
- `ranking-management.css` - 排名管理页面样式（命名空间：`.ranking-management-page`）
- `guide-page.css` - 申报指南/榜单规则页面样式（命名空间：`.guide-page`）
- `submission-review-page.css` - 申报审核页面样式（命名空间：`.submission-review-page`）
- `historical-ranking-page.css` - 历史榜单页面样式（命名空间：`.historical-ranking-page`）

**示例**:
```css
/* ==================== 首页样式 ==================== */
/* 使用 .home-page 命名空间，确保样式只作用于首页 */

.home-page {
  width: 100%;
  min-height: 100vh;
}

.home-page .body {
  display: grid;
  grid-template-columns: 240px 1fr 300px;
  /* ... */
}

.home-page .card {
  /* 重置全局 .card 样式的影响 */
  padding: 0;
  margin-bottom: 0;
}
```

### 3. 组件特定样式 (Component-Specific Styles)

**文件**: `components/[ComponentName].css`（如需独立文件）

**作用**: 定义可复用组件的样式

**命名规范**:
- 使用组件名作为前缀：`.component-name-element`
- 或使用 CSS Modules（如需更严格的隔离）

## 样式导入顺序

在 `main.tsx` 中按以下顺序导入样式：

```typescript
import './styles.css'                          // 1. 全局样式
import './styles/home-page.css'               // 2. 页面特定样式
import './styles/ranking-management.css'
import './styles/guide-page.css'
import './styles/submission-review-page.css'
import './styles/historical-ranking-page.css'
```

## 命名空间规范

### 页面根元素类名

每个页面的根元素必须包含页面特定的类名：

```tsx
// 首页
<div className="home-page">
  {/* 页面内容 */}
</div>

// 排名管理页面
<div className="ranking-management-page">
  {/* 页面内容 */}
</div>

// 申报指南页面
<div className="guide-page">
  {/* 页面内容 */}
</div>
```

### 样式选择器规范

所有页面特定样式必须使用命名空间前缀：

```css
/* ✅ 正确：使用命名空间前缀 */
.home-page .card { }
.home-page .sidebar { }
.ranking-management-page .config-card { }

/* ❌ 错误：缺少命名空间前缀 */
.card { }
.sidebar { }
.config-card { }
```

## 全局样式冲突处理

当页面特定样式需要覆盖全局样式时，必须显式重置：

```css
/* 全局样式 */
.card {
  padding: 24px;
  margin-bottom: 24px;
}

/* 首页特定样式 - 重置全局影响 */
.home-page .card {
  padding: 0;           /* 重置全局 padding */
  margin-bottom: 0;     /* 重置全局 margin */
  /* 添加首页特定的样式 */
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
```

## 响应式设计

每个页面样式文件应包含自己的响应式规则：

```css
/* 桌面端样式 */
.home-page .body {
  grid-template-columns: 240px 1fr 300px;
}

/* 平板端 */
@media (max-width: 992px) {
  .home-page .body {
    grid-template-columns: 1fr;
  }
}

/* 移动端 */
@media (max-width: 768px) {
  .home-page .body {
    padding: 16px;
  }
}
```

## 最佳实践

### 1. 避免样式泄漏

- 始终使用命名空间前缀
- 不要使用过于通用的选择器
- 避免使用 `!important`

### 2. 保持特异性一致

- 页面特定选择器使用两级：`.page-name .element`
- 避免过深的选择器嵌套

### 3. 复用全局变量

- 使用 CSS 变量保持一致性
- 不要硬编码颜色、间距值

### 4. 文档注释

每个样式文件顶部应包含：

```css
/* ==================== 页面名称 ==================== */
/* 使用 .page-name 命名空间，确保样式只作用于该页面 */
```

## 添加新页面样式的步骤

1. 创建新文件：`styles/[page-name]-page.css`
2. 添加命名空间根样式：`.[page-name]-page { }`
3. 定义页面特定样式，所有选择器使用命名空间前缀
4. 在 `main.tsx` 中导入新样式文件
5. 在页面组件根元素添加对应类名

## 故障排除

### 样式不生效

检查：
1. 选择器是否正确使用命名空间前缀
2. 样式文件是否在 `main.tsx` 中导入
3. 页面根元素是否有正确的类名

### 样式冲突

检查：
1. 是否有其他页面使用了相同的类名但没有命名空间
2. 全局样式是否需要显式重置
3. 选择器特异性是否足够

## 文件结构

```
frontend/src/
├── styles/
│   ├── README.md                    # 本文档
│   ├── styles.css                   # 全局样式
│   ├── home-page.css               # 首页样式
│   ├── ranking-management.css      # 排名管理页面样式
│   ├── guide-page.css              # 申报指南/榜单规则页面样式
│   ├── submission-review-page.css  # 申报审核页面样式
│   ├── historical-ranking-page.css # 历史榜单页面样式
│   └── modal-redesign.css          # 模态框视觉重设计样式（最后导入）
└── main.tsx                         # 样式导入入口
```

## 特殊样式文件

### modal-redesign.css

**用途**: 模态框视觉重设计，提供现代、专业且富有层次感的设计风格

**命名空间**: `.home-page`（仅作用于首页模态框）

**导入顺序**: 在 `styles.css` 中最后导入，确保最高优先级

**设计特点**:
- 使用CSS变量保持主题一致性
- 精致的阴影和动画效果
- 响应式适配移动端
- 统一的模态框结构（`.modal-body` + `.modal-footer`）

**注意事项**:
- 此文件使用CSS变量而非硬编码颜色值
- 所有选择器都使用 `.home-page` 命名空间
- 不影响其他页面的样式
