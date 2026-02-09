# 项目开发环境配置

> 此文件记录开发者偏好，AI 助手执行任务前应先阅读

## 开发环境

### 硬件
- 设备：英特尔笔记本
- 内存：32GB
- 显卡：NVIDIA RTX 4070 (移动端)

### 技术栈
- **后端**：Python、Java
- **数据库**：MySQL
- **容器**：Docker Desktop

### 命令行
- **Shell**：PowerShell
- **注意**：所有命令必须使用 PowerShell 语法

### 服务部署原则
- **数据库**（MySQL 等）：必须使用 Docker 部署
- **端口策略**：使用高位端口避免冲突
  - MySQL: 13306 (映射到 3306)
  - 其他服务类似

## 开发工作流

1. **本地开发**：PowerShell 执行命令
2. **数据库**：Docker 运行，不本地安装
3. **版本控制**：Git，遵循 PR 流程
4. **代码规范**：遵循项目既有风格

## 常用命令参考

### Docker
```powershell
# 启动 MySQL
docker-compose up -d mysql

# 查看容器状态
docker ps
```

### Git
```powershell
# 创建功能分支
git checkout -b feature/xxx

# 提交代码
git add -A
git commit -m "feat: xxx"

# 推送并创建 PR（必须通过 GitHub Web）
git push origin feature/xxx
```

## 注意事项

- ⚠️ 禁止直接提交到 `main` 分支
- ⚠️ 所有数据库服务必须用 Docker
- ⚠️ 命令使用 PowerShell 语法，不是 Bash
