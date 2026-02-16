
# DragonAI 部署文档

## 系统要求

- Python 3.13+
- PostgreSQL 14+
- Redis 7+
- 8GB+ RAM

## 快速开始

### 1. 环境准备

#### 安装 Python 依赖

```bash
pip install -r requirements.txt
```

#### 安装 PostgreSQL

**Windows:**
```bash
# 使用官方安装程序或 Chocolatey
choco install postgresql
```

**MacOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### 安装 Redis

**Windows:**
```bash
# 使用 Chocolatey 或下载官方安装包
choco install redis-64
```

**MacOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

### 2. 数据库配置

#### 创建数据库和用户

```sql
-- 连接到 PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE dragonai;

-- 创建用户
CREATE USER dragonai_user WITH PASSWORD 'your_secure_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE dragonai TO dragonai_user;
\c dragonai
GRANT ALL ON SCHEMA public TO dragonai_user;
```

### 3. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```env
# 应用配置
APP_NAME=DragonAI
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# JWT 密钥（生产环境务必修改！）
SECRET_KEY=your-very-secure-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 数据库连接
DATABASE_URL=postgresql://dragonai_user:your_secure_password@localhost:5432/dragonai

# Redis 连接
REDIS_URL=redis://localhost:6379/0

# ChromaDB 存储目录
CHROMA_PERSIST_DIR=./chroma_db

# 通义千问 API 密钥（从阿里云获取）
QWEN_API_KEY=your-qwen-api-key-here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Tavily 搜索 API 密钥（从 tavily.com 获取）
TAVILY_API_KEY=your-tavily-api-key-here

# 文件存储
STORAGE_DIR=./storage

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### 4. 初始化数据库

运行数据库初始化脚本：

```bash
# Windows
python scripts/init_db.py

# Linux/Mac
python3 scripts/init_db.py
```

或者使用 SQLAlchemy 创建表：

```python
from app.core.database import engine, Base
from app.models import user, conversation, message

Base.metadata.create_all(bind=engine)
```

### 5. 启动服务

#### 使用启动脚本（推荐）

**Windows:**
```powershell
.\scripts\start.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

#### 手动启动

```bash
# 开发模式（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 验证部署

访问以下 URL 验证服务是否正常运行：

- 健康检查: http://localhost:8000/health
- API 文档: http://localhost:8000/docs
- API 备用文档: http://localhost:8000/redoc

## Docker 部署

### 使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: dragonai_user
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: dragonai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dragonai_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://dragonai_user:your_secure_password@postgres:5432/dragonai
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./storage:/app/storage
      - ./chroma_db:/app/chroma_db
      - ./logs:/app/logs

volumes:
  postgres_data:
  redis_data:
```

启动服务：

```bash
docker-compose up -d
```

## 生产环境部署建议

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（用于 SSE）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件
    location /storage {
        alias /path/to/dragonai-v2-local/storage;
    }
}
```

### 使用 systemd 管理服务

创建 `/etc/systemd/system/dragonai.service`：

```ini
[Unit]
Description=DragonAI Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=your_user
WorkingDirectory=/path/to/dragonai-v2-local
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable dragonai
sudo systemctl start dragonai
sudo systemctl status dragonai
```

## 监控和日志

### 查看日志

```bash
# 应用日志
tail -f logs/app.log

# systemd 日志
sudo journalctl -u dragonai -f
```

### 备份数据

定期备份 PostgreSQL 数据库：

```bash
pg_dump -U dragonai_user dragonai &gt; backup_$(date +%Y%m%d).sql
```

## 常见问题

### 数据库连接失败

检查 PostgreSQL 是否运行：
```bash
# Linux
sudo systemctl status postgresql

# MacOS
brew services list
```

### Redis 连接失败

检查 Redis 是否运行：
```bash
redis-cli ping
```

### 端口被占用

修改 `.env` 中的 `APP_PORT`，或停止占用端口的进程。

### 权限问题

确保应用有读写 `storage`、`chroma_db`、`logs` 目录的权限。

## 下一步

- 配置 HTTPS（使用 Let's Encrypt）
- 设置定期备份
- 配置监控告警
- 进行性能优化

