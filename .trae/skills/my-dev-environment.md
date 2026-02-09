# 个人开发环境配置指南

## 1. 硬件配置

| 项目 | 配置 |
|------|------|
| 设备类型 | 英特尔笔记本 |
| 内存 | 32GB |
| 显卡 | NVIDIA RTX 4070 (移动端) |

## 2. 技术栈偏好

### 后端技术
- **编程语言**：Python、Java
- **数据库**：MySQL
- **容器化**：Docker Desktop

### 前端技术
- **当前计划**：暂无特定计划

## 3. 开发工具规范

### 命令行环境
- **默认 Shell**：PowerShell
- **执行原则**：所有命令必须使用 PowerShell 语法
- **注意**：避免使用 Bash 特有语法

### 容器化部署
- **Docker**：Docker Desktop 已安装
- **使用原则**：
  - MySQL 等数据库服务必须使用 Docker 部署
  - 避免在本地直接安装服务
  - 优先使用 docker-compose 管理服务

### 数据库配置
- **MySQL**：通过 Docker 容器运行
- **端口策略**：使用高位端口避免冲突
  - MySQL: 13306 (映射到容器 3306)
  - Redis: 16379 (映射到容器 6379)
  - PostgreSQL: 15432 (映射到容器 5432)

## 4. 开发工作流

### 1. 本地开发
- 使用 PowerShell 执行命令
- 代码编辑器：VS Code
- 版本控制：Git

### 2. 服务管理
- 使用 Docker Desktop 管理容器
- 服务启动：`docker-compose up -d`
- 服务状态检查：`docker ps`

### 3. 数据库操作
- MySQL 通过 Docker 运行
- 连接工具：MySQL Workbench 或 VS Code 插件
- 端口：13306

### 4. 版本控制
- **主分支**：main
- **开发分支**：feature/*、fix/*
- **工作流程**：
  1. 从 main 创建分支
  2. 开发并提交代码
  3. 推送远程并创建 PR
  4. 审核后合并到 main
  5. 删除本地和远程分支

## 5. 常用命令参考

### Docker 命令

```powershell
# 启动服务
docker-compose up -d

# 查看容器状态
docker ps

# 停止服务
docker-compose down

# 查看日志
docker logs <container-name>

# 进入容器
docker exec -it <container-name> bash
```

### MySQL 相关

```powershell
# 启动 MySQL 容器
docker-compose up -d mysql

# 连接 MySQL
mysql -h localhost -P 13306 -u ai_app_user -p

# 导入 SQL 文件
docker exec -i <mysql-container> mysql -u ai_app_user -pai_app_password ai_app_square < init.sql
```

### Git 命令

```powershell
# 创建功能分支
git checkout -b feature/new-feature

# 提交代码
git add -A
git commit -m "feat: 添加新功能"

# 推送远程
git push origin feature/new-feature

# 切换到主分支
git checkout main

# 拉取更新
git pull origin main

# 删除本地分支
git branch -d feature/new-feature

# 删除远程分支
git push origin --delete feature/new-feature
```

### Python 开发

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 运行应用
uvicorn app.main:app --reload
```

## 6. 注意事项

### 禁止事项
- ❌ 禁止直接提交到 main 分支
- ❌ 禁止在本地直接安装数据库服务（必须使用 Docker）
- ❌ 禁止使用标准端口（如 3306），必须使用高位端口
- ❌ 禁止使用 Bash 语法执行命令

### 推荐做法
- ✅ 优先使用 docker-compose 管理服务
- ✅ 遵循 Git PR 流程（即使是单人项目）
- ✅ 使用虚拟环境管理 Python 依赖
- ✅ 保持代码风格一致性
- ✅ 定期清理未使用的分支和容器

## 7. 故障排查

### Docker 问题
- **容器启动失败**：检查端口是否被占用
- **网络连接**：检查 Docker 网络配置
- **数据持久化**：确保使用数据卷

### MySQL 连接问题
- **端口映射**：确认使用 13306 端口
- **密码验证**：检查环境变量配置
- **权限**：确认用户权限设置

### 命令执行错误
- **PowerShell 语法**：确保使用正确的 PowerShell 命令
- **路径问题**：使用绝对路径或正确的相对路径
- **权限**：以管理员身份运行 PowerShell

## 8. 项目结构规范

### 后端项目结构
```
backend/
├── app/
│   ├── main.py          # 应用入口
│   ├── models.py        # 数据模型
│   ├── schemas.py       # 数据校验
│   ├── database.py      # 数据库连接
│   └── config.py        # 配置管理
├── requirements.txt     # 依赖管理
├── .env                 # 环境变量
└── docker-compose.yml   # 服务配置
```

### 前端项目结构
```
frontend/
├── src/
│   ├── App.tsx          # 应用组件
│   ├── components/      # 组件库
│   ├── api/             # API 调用
│   ├── types/           # 类型定义
│   └── styles.css       # 样式
├── package.json         # 依赖管理
└── vite.config.ts       # 构建配置
```

## 9. 环境变量配置

### 后端环境变量
```env
# .env 文件
DATABASE_URL=mysql+pymysql://ai_app_user:ai_app_password@localhost:13306/ai_app_square
API_KEY=your-api-key
DEBUG=True
```

### Docker Compose 配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    ports:
      - "13306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=ai_app_square
      - MYSQL_USER=ai_app_user
      - MYSQL_PASSWORD=ai_app_password
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  mysql_data:
```

## 10. 快捷操作脚本

### 启动开发环境
```powershell
# scripts/start-dev.ps1
Write-Host "Starting development environment..."

# 启动 Docker 服务
docker-compose up -d

# 激活虚拟环境
.venv\Scripts\Activate.ps1

Write-Host "Development environment ready!"
```

### 停止开发环境
```powershell
# scripts/stop-dev.ps1
Write-Host "Stopping development environment..."

# 停止 Docker 服务
docker-compose down

Write-Host "Development environment stopped!"
```

## 11. 版本控制规范

### 分支命名
- **功能分支**：`feature/feature-name`
- **修复分支**：`fix/bug-description`
- **文档分支**：`docs/documentation-update`
- **重构分支**：`refactor/code-refactoring`

### 提交信息

#### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型
- `feat`：新功能
- `fix`：Bug 修复
- `docs`：文档更新
- `style`：代码格式
- `refactor`：代码重构
- `perf`：性能优化
- `test`：测试
- `chore`：构建/工具

#### 示例
```
feat(api): 添加用户认证接口

- 实现 JWT 认证
- 添加密码哈希
- 集成用户模型

Closes #123
```

## 12. 总结

本配置指南旨在：
1. **统一开发环境**：确保一致的开发体验
2. **提高效率**：提供常用命令和工作流
3. **避免错误**：规范操作流程和注意事项
4. **便于协作**：清晰的项目结构和版本控制规范

遵循本指南可以减少环境配置问题，提高开发效率，确保代码质量。
