
# DragonAI 完整部署指南

> 从零开始：租服务器 -> 域名配置 -> 部署应用 -> HTTPS -> 上线

---

## 目录

1. [准备工作](#一准备工作)
2. [租用云服务器](#二租用云服务器)
3. [购买和配置域名](#三购买和配置域名)
4. [服务器初始化](#四服务器初始化)
5. [部署应用](#五部署应用)
6. [配置 HTTPS](#六配置-https)
7. [后续维护](#七后续维护)
8. [常见问题](#八常见问题)

---

## 一、准备工作

### 1.1 需要准备的内容

| 项目 | 说明 | 获取方式 |
|------|------|---------|
| 云服务器 | 2核4G以上 | 阿里云/腾讯云 |
| 域名（可选） | 用于 HTTPS | 阿里云/腾讯云/Cloudflare |
| 通义千问 API Key | AI 对话功能 | [阿里云 DashScope](https://dashscope.console.aliyun.com/) |
| Tavily API Key | 网络搜索功能 | [tavily.com](https://tavily.com/) |

### 1.2 费用预估

| 项目 | 配置 | 月费用 |
|------|------|--------|
| 云服务器 | 2核4G | ¥80-150 |
| 域名 | .com | ¥50-70/年 |
| SSL 证书 | Let's Encrypt | 免费 |
| 通义千问 API | 按量付费 | ¥0-100 |
| **总计** | | **¥80-250/月** |

---

## 二、租用云服务器

### 2.1 阿里云 ECS（推荐）

#### 步骤 1：注册/登录阿里云

访问 [阿里云官网](https://www.aliyun.com/)，注册并登录账号。

#### 步骤 2：进入 ECS 购买页面

```
控制台 -> 云服务器 ECS -> 创建实例
```

或直接访问：https://ecs.console.aliyun.com/

#### 步骤 3：选择配置

**基础配置：**

| 配置项 | 推荐选择 | 说明 |
|--------|---------|------|
| 付费模式 | 按量付费 / 包年包月 | 测试选按量，生产选包年 |
| 地域 | 华东/华北/华南 | 选择离用户最近的区域 |
| 实例规格 | 2核4G (ecs.c6.large) | 入门推荐 |
| 镜像 | Ubuntu 22.04 64位 | 推荐 LTS 版本 |
| 存储 | 40-100G SSD | 根据需求选择 |

**网络和安全组：**

| 配置项 | 推荐选择 |
|--------|---------|
| 网络类型 | 专有网络 VPC |
| 公网 IP | 分配 |
| 带宽 | 按使用流量 / 5Mbps |
| 安全组 | 自动创建（后续配置） |

**系统配置：**

| 配置项 | 推荐选择 |
|--------|---------|
| 登录凭证 | 自定义密码 |
| 用户名 | root |
| 密码 | 设置强密码（记住！） |
| 实例名称 | DragonAI-Server |

#### 步骤 4：确认订单并创建

确认配置无误后，点击「确认订单」创建实例。

创建完成后，记录下 **公网 IP 地址**。

### 2.2 腾讯云 CVM

#### 步骤 1：注册/登录腾讯云

访问 [腾讯云官网](https://cloud.tencent.com/)，注册并登录账号。

#### 步骤 2：进入 CVM 购买页面

```
控制台 -> 云服务器 -> 新建
```

或直接访问：https://buy.cloud.tencent.com/cvm

#### 步骤 3：选择配置

| 配置项 | 推荐选择 |
|--------|---------|
| 计费模式 | 包年包月 / 按量计费 |
| 地域 | 广州/上海/北京 |
| 机型 | 标准型 S5 / 2核4G |
| 镜像 | Ubuntu 22.04 LTS |
| 存储 | 50G 高性能云硬盘 |
| 网络 | 默认 VPC |
| 带宽 | 按流量 / 5Mbps |
| 安全组 | 放通全部端口（后续调整） |

#### 步骤 4：设置登录信息

| 配置项 | 推荐选择 |
|--------|---------|
| 登录方式 | 密码 |
| 用户名 | root / ubuntu |
| 密码 | 设置强密码 |

### 2.3 配置安全组（防火墙）

#### 阿里云安全组配置

1. 进入 ECS 控制台 -> 网络与安全 -> 安全组
2. 点击「配置规则」->「入方向」->「手动添加」

添加以下规则：

| 协议 | 端口范围 | 授权对象 | 说明 |
|------|---------|---------|------|
| TCP | 22 | 0.0.0.0/0 或 你的IP | SSH 登录 |
| TCP | 80 | 0.0.0.0/0 | HTTP |
| TCP | 443 | 0.0.0.0/0 | HTTPS |

#### 腾讯云安全组配置

1. 进入 CVM 控制台 -> 安全组
2. 点击「修改规则」->「入站规则」

添加相同的规则。

---

## 三、购买和配置域名

### 3.1 购买域名

#### 阿里云（万网）

1. 访问 [阿里云域名注册](https://wanwang.aliyun.com/domain/)
2. 搜索想要的域名
3. 选择后缀（.com / .cn / .net 等）
4. 加入购物车并结算
5. 完成实名认证

#### 腾讯云

1. 访问 [腾讯云域名注册](https://dnspod.cloud.tencent.com/)
2. 搜索并购买域名
3. 完成实名认证

### 3.2 域名解析

#### 阿里云解析配置

1. 进入域名控制台 -> 解析设置
2. 点击「添加记录」

| 记录类型 | 主机记录 | 记录值 | TTL |
|---------|---------|--------|-----|
| A | @ | 你的服务器IP | 10分钟 |
| A | www | 你的服务器IP | 10分钟 |

#### 腾讯云 DNSPod 配置

1. 进入 DNSPod 控制台
2. 添加域名
3. 添加记录（同上）

### 3.3 等待生效

DNS 解析通常需要 10分钟 - 48小时 生效。

验证解析是否生效：

```bash
# Windows
nslookup your-domain.com

# Linux/Mac
dig your-domain.com
```

---

## 四、服务器初始化

### 4.1 连接服务器

#### Windows 用户

**方式一：使用 PowerShell**

```powershell
ssh root@your-server-ip
# 输入密码
```

**方式二：使用 PuTTY / Xshell / MobaXterm**

1. 下载并安装 SSH 客户端
2. 主机：your-server-ip
3. 端口：22
4. 用户名：root
5. 密码：购买时设置的密码

#### Mac/Linux 用户

```bash
ssh root@your-server-ip
# 输入密码
```

### 4.2 更新系统

```bash
# 更新软件包列表
apt update

# 升级已安装的软件包
apt upgrade -y

# 安装常用工具
apt install -y curl wget git vim htop
```

### 4.3 创建普通用户（可选但推荐）

```bash
# 创建用户
adduser dragonai

# 添加 sudo 权限
usermod -aG sudo dragonai

# 切换用户
su - dragonai
```

### 4.4 配置 SSH 密钥登录（推荐）

**本地电脑执行：**

```bash
# 生成密钥对（如果已有可跳过）
ssh-keygen -t ed25519 -C "your-email@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub
# 复制输出的内容
```

**服务器执行：**

```bash
# 创建 .ssh 目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 添加公钥
vim ~/.ssh/authorized_keys
# 粘贴公钥内容，保存退出

chmod 600 ~/.ssh/authorized_keys
```

**禁用密码登录（可选）：**

```bash
sudo vim /etc/ssh/sshd_config

# 修改以下配置
PasswordAuthentication no
PubkeyAuthentication yes

# 重启 SSH 服务
sudo systemctl restart sshd
```

### 4.5 安装 Docker

```bash
# 1. 更新包索引
sudo apt update

# 2. 安装依赖
sudo apt install -y ca-certificates curl gnupg

# 3. 创建 keyrings 目录
sudo install -m 0755 -d /etc/apt/keyrings

# 4. 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 5. 添加 Docker 软件源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 6. 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 7. 启动 Docker
sudo systemctl enable docker
sudo systemctl start docker

# 8. 添加当前用户到 docker 组（免 sudo）
sudo usermod -aG docker $USER

# 9. 使组权限生效
newgrp docker

# 10. 验证安装
docker --version
docker compose version
```

### 4.6 配置防火墙

```bash
# 安装 ufw
sudo apt install -y ufw

# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 五、部署应用

### 5.1 克隆代码

```bash
# 创建工作目录
mkdir -p ~/projects
cd ~/projects

# 克隆代码（替换为你的仓库地址）
git clone https://github.com/your-username/dragonai-v2-local.git
cd dragonai-v2-local
```

### 5.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.production .env

# 编辑配置
vim .env
```

**必须修改的配置：**

```env
# ========== 应用配置 ==========
APP_NAME=DragonAI
APP_ENV=production
APP_DEBUG=false

# ========== 安全配置（必须修改！）==========
# 生成方式: openssl rand -hex 32
SECRET_KEY=生成一个32位以上的随机字符串填在这里
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ========== 数据库配置 ==========
DB_USER=dragonai
DB_PASSWORD=设置一个安全的数据库密码
DB_NAME=dragonai

# ========== AI API 配置 ==========
# 从 https://dashscope.console.aliyun.com/ 获取
QWEN_API_KEY=sk-你的通义千问API密钥
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 从 https://tavily.com/ 获取
TAVILY_API_KEY=tvly-你的Tavily密钥

# ========== 日志配置 ==========
LOG_LEVEL=INFO
```

**生成 SECRET_KEY：**

```bash
openssl rand -hex 32
```

### 5.3 一键部署

```bash
# 添加执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh deploy
```

部署脚本会自动：
1. 检查依赖
2. 构建前端
3. 构建 Docker 镜像
4. 启动所有服务

### 5.4 验证部署

```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f

# 健康检查
curl http://localhost/health
```

**预期输出：**

```
NAME                  STATUS    PORTS
dragonai-postgres     running   5432/tcp
dragonai-redis        running   6379/tcp
dragonai-backend      running   0.0.0.0:8000->8000/tcp
dragonai-nginx        running   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 5.5 访问应用

- **前端页面**: http://your-server-ip
- **API 文档**: http://your-server-ip/docs
- **健康检查**: http://your-server-ip/health

---

## 六、配置 HTTPS

### 6.1 前提条件

- 已有域名并完成解析
- 域名已指向服务器 IP

### 6.2 安装 Certbot

```bash
sudo apt install -y certbot
```

### 6.3 申请 SSL 证书

```bash
# 停止 nginx 容器（释放 80 端口）
docker compose stop nginx

# 申请证书（替换 your-domain.com）
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 按提示输入邮箱，同意条款
```

### 6.4 配置证书

```bash
# 创建 SSL 目录
mkdir -p nginx/ssl

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 修改权限
sudo chown -R $USER:$USER nginx/ssl
chmod 600 nginx/ssl/*.pem
```

### 6.5 更新 Nginx 配置

创建 HTTPS 配置文件：

```bash
vim nginx/nginx-ssl.conf
```

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;

    upstream backend {
        server backend:8000;
    }

    # HTTP -> HTTPS 重定向
    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 服务
    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        # SSL 配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;

        # 安全头
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        root /usr/share/nginx/html;
        index index.html;

        # 前端静态文件
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api/ {
            limit_req zone=api burst=50 nodelay;
            
            proxy_pass http://backend/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            proxy_read_timeout 300s;
        }

        # 健康检查
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }

        # API 文档
        location ~ ^/(docs|redoc|openapi.json) {
            proxy_pass http://backend;
        }
    }
}
```

### 6.6 重启服务

```bash
# 更新 docker-compose.yml 使用新配置
# 将 nginx.conf 改为 nginx-ssl.conf

# 重启 nginx
docker compose restart nginx
```

### 6.7 设置自动续期

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下行（每月1号凌晨3点续期）
0 3 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /home/your-user/projects/dragonai-v2-local/nginx/ssl/ && cd /home/your-user/projects/dragonai-v2-local && docker compose restart nginx >> /var/log/certbot-renew.log 2>&1
```

### 6.8 验证 HTTPS

访问 `https://your-domain.com`，确认：
- 浏览器显示安全锁图标
- 证书有效
- 网站正常访问

---

## 七、后续维护

### 7.1 常用命令

```bash
# 进入项目目录
cd ~/projects/dragonai-v2-local

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 启动服务
docker compose up -d

# 重新构建
docker compose build --no-cache
docker compose up -d
```

### 7.2 更新代码

```bash
cd ~/projects/dragonai-v2-local

# 拉取最新代码
git pull origin main

# 重新构建前端
cd frontend && npm install && npm run build && cd ..

# 重启服务
docker compose down
docker compose build
docker compose up -d
```

### 7.3 数据备份

```bash
# 添加执行权限
chmod +x scripts/backup.sh

# 手动备份
./scripts/backup.sh

# 设置定时备份
crontab -e

# 每天凌晨2点备份
0 2 * * * /home/your-user/projects/dragonai-v2-local/scripts/backup.sh >> /var/log/dragonai-backup.log 2>&1
```

### 7.4 监控资源

```bash
# 查看系统资源
htop

# 查看 Docker 资源使用
docker stats

# 查看磁盘使用
df -h

# 清理 Docker 资源
docker system prune -a
```

### 7.5 查看日志

```bash
# 应用日志
docker compose logs -f backend

# Nginx 日志
docker compose logs -f nginx

# 数据库日志
docker compose logs -f postgres
```

---

## 八、常见问题

### Q1: 无法连接服务器

**检查清单：**
1. 服务器是否启动（控制台查看状态）
2. 安全组是否开放 22 端口
3. 密码是否正确
4. 本地网络是否正常

```bash
# 测试连通性
ping your-server-ip
telnet your-server-ip 22
```

### Q2: 网站无法访问

**检查清单：**
1. 容器是否正常运行：`docker compose ps`
2. 端口是否开放：`sudo ufw status`
3. 安全组是否配置
4. 查看日志：`docker compose logs`

```bash
# 检查端口监听
sudo netstat -tlnp | grep -E '80|443|8000'

# 检查容器日志
docker compose logs --tail=100 backend
```

### Q3: 数据库连接失败

```bash
# 检查 PostgreSQL 容器
docker compose logs postgres

# 进入数据库容器
docker exec -it dragonai-postgres psql -U dragonai -d dragonai

# 检查数据库是否存在
\l
```

### Q4: SSL 证书申请失败

**常见原因：**
1. 域名未正确解析到服务器 IP
2. 80 端口被占用
3. 防火墙阻止了 80 端口

```bash
# 检查域名解析
dig your-domain.com

# 检查 80 端口
sudo lsof -i :80

# 临时停止所有服务
docker compose down
```

### Q5: 内存不足

```bash
# 查看内存使用
free -h

# 创建交换空间（临时解决）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Q6: Docker 镜像构建失败

```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker compose build --no-cache

# 查看构建日志
docker compose build 2>&1 | tee build.log
```

---

## 九、快速命令参考

```bash
# ========== 服务器连接 ==========
ssh root@your-server-ip

# ========== Docker 命令 ==========
docker compose ps          # 查看状态
docker compose logs -f     # 查看日志
docker compose restart     # 重启服务
docker compose down        # 停止服务
docker compose up -d       # 启动服务
docker compose build       # 构建镜像

# ========== 系统命令 ==========
htop                       # 系统监控
df -h                      # 磁盘使用
docker stats               # 容器资源

# ========== 备份命令 ==========
./scripts/backup.sh        # 执行备份

# ========== SSL 续期 ==========
sudo certbot renew         # 手动续期
```

---

## 十、部署检查清单

| 步骤 | 状态 | 说明 |
|------|------|------|
| ☐ 租用服务器 | | 选择合适配置 |
| ☐ 配置安全组 | | 开放 22/80/443 |
| ☐ 连接服务器 | | SSH 登录成功 |
| ☐ 安装 Docker | | docker --version |
| ☐ 克隆代码 | | git clone |
| ☐ 配置环境变量 | | 修改 .env |
| ☐ 部署应用 | | ./deploy.sh deploy |
| ☐ 验证访问 | | curl http://ip/health |
| ☐ 配置域名 | | DNS 解析 |
| ☐ 申请证书 | | certbot |
| ☐ 配置 HTTPS | | nginx-ssl.conf |
| ☐ 设置备份 | | crontab |
| ☐ 完成 | | 🎉 |

---

**恭喜！部署完成！** 🎉

访问 `https://your-domain.com` 开始使用 DragonAI。
