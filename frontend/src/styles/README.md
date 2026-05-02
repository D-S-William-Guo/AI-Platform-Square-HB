# CSS 样式架构

## 架构概述

采用命名空间隔离策略，页面特定样式不互相污染。

## 文件分层

### 全局样式

- `frontend/src/styles.css` — CSS 变量、基础元素重置、通用组件（btn/card/modal/form）、布局框架（header/footer/page-container）。由 `main.tsx` 导入。
- `frontend/src/styles/global-layout.css` — 全局布局补充样式。

### 页面样式（命名空间 = 页面根类名）

| 文件 | 命名空间 | 对应页面 |
|---|---|---|
| `home-page.css` | `.home-page` | 首页 |
| `guide-page.css` | `.guide-page` | 申报指南 / 榜单规则 |
| `submission-review-page.css` | `.submission-review-page` | 申报审核 |
| `historical-ranking-page.css` | `.historical-ranking-page` | 历史榜单 |
| `ranking-management.css` | `.ranking-management-page` | 排行榜管理 |
| `ranking-detail.css` | - | 榜单详情 |
| `login-page.css` | - | 登录页 |
| `my-submissions-page.css` | - | 我的申报 |
| `user-management-page.css` | - | 用户管理 |

### 其他

- `modal-redesign.css` — 模态框视觉重设计（`.home-page` 命名空间）
- `pagination.css` — 分页组件样式

## 命名规范

所有页面特定选择器必须以页面根类名开头：

```css
/* ✅ 正确 */
.home-page .card { }
.guide-page .section { }

/* ❌ 错误 */
.card { }
```

全局样式冲突时在页面命名空间下显式重置。

## 添加新页面样式

1. `styles/` 下新建 `[name]-page.css`
2. 所有选择器使用对应命名空间前缀
3. 在页面组件根元素添加类名
