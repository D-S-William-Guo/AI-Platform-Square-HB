# 部署指南

## 系统要求

### 服务器配置

| 环境 | CPU | 内存 | 存储 | 操作系统 |
|------|-----|------|------|----------|
| 最小配置 | 2核 | 4GB | 20GB | Ubuntu 20.04+ / CentOS 8+ |
| 推荐配置 | 4核 | 8GB | 50GB | Ubuntu 22.04 LTS |

### 软件依赖

- Python 3.10+
- Node.js 18+
- SQLite 3 / MySQL 8.0
- Nginx (生产环境)
- Docker & Docker Compose (可选)

## 部署方式

### 方式一：Docker Compose 部署（推荐）

#### 1. 克隆代码

```bash
git clone https://github.com/D-S-William-Guo/AI-Platform-Square-HB.git
cd AI-Platform-Square-HB
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等参数
```

#### 3. 启动服务

```bash
docker-compose up -d
```

#### 4. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 测试API
curl http://localhost/api/health
```

### 方式二：手动部署

#### 后端部署

##### 1. 安装 Python 依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

##### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

`.env` 文件示例：

```env
# 应用配置
APP_NAME="AI App Square API"
API_PREFIX=/api

# 数据库配置
DATABASE_URL=sqlite:///./ai_app_square.db
# 或 MySQL: DATABASE_URL=mysql+pymysql://user:password@localhost/ai_app_square

# OA系统配置（可选）
OA_RULE_BASE_URL=https://oa.example.internal

# 其他配置
DEBUG=false
LOG_LEVEL=INFO
```

##### 3. 初始化数据库

```bash
python init_db.py
```

##### 4. 启动服务

开发模式：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

生产模式：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 前端部署

##### 1. 安装依赖

```bash
cd frontend
npm install
```

##### 2. 配置 API 地址

编辑 `src/api/client.ts`，设置后端 API 地址：

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
```

##### 3. 构建

```bash
npm run build
```

##### 4. 部署

将 `dist` 目录部署到 Web 服务器（Nginx/Apache）

### 方式三：生产环境部署（Nginx + Gunicorn）

#### 1. 后端配置

安装 Gunicorn：
```bash
pip install gunicorn
```

创建 Gunicorn 配置文件 `gunicorn.conf.py`：

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "/var/log/ai-app-square/access.log"
errorlog = "/var/log/ai-app-square/error.log"
```

使用 systemd 管理服务，创建 `/etc/systemd/system/ai-app-square.service`：

```ini
[Unit]
Description=AI App Square API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-app-square/backend
Environment=PATH=/opt/ai-app-square/backend/.venv/bin
ExecStart=/opt/ai-app-square/backend/.venv/bin/gunicorn -c gunicorn.conf.py app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-app-square
sudo systemctl start ai-app-square
```

#### 2. Nginx 配置

创建 `/etc/nginx/sites-available/ai-app-square`：

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /opt/ai-app-square/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态文件上传目录
    location /uploads/ {
        alias /opt/ai-app-square/backend/uploads/;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/ai-app-square /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 数据库迁移

### SQLite 到 MySQL 迁移

```bash
cd backend
python migrations/migrate_sqlite_to_mysql.py
```

## 备份与恢复

### 数据库备份

#### SQLite

```bash
# 备份
cp ai_app_square.db ai_app_square.db.backup.$(date +%Y%m%d)

# 恢复
cp ai_app_square.db.backup.20240101 ai_app_square.db
```

#### MySQL

```bash
# 备份
mysqldump -u root -p ai_app_square > backup_$(date +%Y%m%d).sql

# 恢复
mysql -u root -p ai_app_square < backup_20240101.sql
```

### 文件备份

```bash
# 上传的文件
rsync -avz backend/uploads/ backup/uploads/
```

## 监控与日志

### 日志位置

- 后端日志：`/var/log/ai-app-square/`
- Nginx 日志：`/var/log/nginx/`

### 健康检查

```bash
# API 健康检查
curl http://localhost/api/health

# 预期响应
{"status": "ok", "timestamp": "2024-01-01T00:00:00"}
```

## 故障排查

### 常见问题

#### 1. 端口被占用

```bash
# 查找占用 8000 端口的进程
sudo lsof -i :8000
# 或
sudo netstat -tulpn | grep 8000

# 终止进程
sudo kill -9 <PID>
```

#### 2. 权限问题

```bash
# 修复上传目录权限
sudo chown -R www-data:www-data backend/uploads/
sudo chmod -R 755 backend/uploads/
```

#### 3. 数据库连接失败

检查 `.env` 中的 `DATABASE_URL` 配置：
- SQLite: `sqlite:///./ai_app_square.db`
- MySQL: `mysql+pymysql://user:password@host:port/database`

#### 4. CORS 问题

确保后端 `main.py` 中的 CORS 配置正确：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 生产环境指定域名
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 更新部署

### 更新代码

```bash
git pull origin main
```

### 更新后端

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 如果有数据库迁移
# alembic upgrade head

# 重启服务
sudo systemctl restart ai-app-square
```

### 更新前端

```bash
cd frontend
npm install
npm run build

# 复制到 Nginx 目录
sudo cp -r dist/* /var/www/ai-app-square/
```

## 安全建议

1. **使用 HTTPS**: 生产环境必须配置 SSL 证书
2. **环境变量**: 敏感信息（数据库密码等）使用环境变量
3. **文件上传**: 限制上传文件类型和大小
4. **访问控制**: 配置防火墙，只开放必要端口
5. **定期备份**: 设置自动备份任务

## 性能优化

1. **数据库**: 添加索引，定期清理历史数据
2. **缓存**: 使用 Redis 缓存热点数据
3. **CDN**: 静态资源使用 CDN 加速
4. **Gzip**: 启用 Nginx Gzip 压缩
