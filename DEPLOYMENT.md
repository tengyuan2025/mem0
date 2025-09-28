# Mem0 云服务器部署指南

本指南将帮助您将Mem0项目部署到云服务器，并通过GitHub Actions实现自动化CI/CD。

## 📋 目录

- [前期准备](#前期准备)
- [服务器初始化](#服务器初始化)
- [GitHub配置](#github配置)
- [部署流程](#部署流程)
- [监控配置](#监控配置)
- [故障排除](#故障排除)

## 🚀 前期准备

### 1. 云服务器要求

**最低配置（测试环境）：**
- CPU: 2核心
- 内存: 4GB
- 存储: 50GB SSD
- 网络: 1Mbps

**推荐配置（生产环境）：**
- CPU: 4核心
- 内存: 8GB
- 存储: 100GB SSD
- 网络: 5Mbps

**支持的操作系统：**
- Ubuntu 20.04/22.04 LTS
- CentOS 7/8
- RHEL 7/8

### 2. 域名准备

您需要准备以下域名（可选）：
- `api.yourdomain.com` - API服务
- `monitor.yourdomain.com` - 监控面板

### 3. GitHub仓库设置

确保您的代码已推送到GitHub仓库，并且有适当的权限设置。

## 🔧 服务器初始化

### 1. 登录服务器

```bash
ssh root@your-server-ip
```

### 2. 运行初始化脚本

```bash
# 下载初始化脚本
curl -fsSL https://raw.githubusercontent.com/your-username/mem0/main/scripts/deployment/setup-server.sh -o setup-server.sh

# 运行初始化脚本
chmod +x setup-server.sh
sudo ./setup-server.sh
```

初始化脚本将自动完成：
- ✅ 系统更新和安全配置
- ✅ Docker和Docker Compose安装
- ✅ Nginx安装和配置
- ✅ 防火墙配置
- ✅ 部署用户创建
- ✅ 监控工具安装
- ✅ 备份脚本设置

### 3. 配置SSH密钥

```bash
# 生成SSH密钥对（在本地机器执行）
ssh-keygen -t rsa -b 4096 -C "deploy@yourdomain.com" -f ~/.ssh/mem0_deploy

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/mem0_deploy.pub deploy@your-server-ip

# 测试连接
ssh -i ~/.ssh/mem0_deploy deploy@your-server-ip
```

## ⚙️ GitHub配置

### 1. 设置Repository Secrets

在GitHub仓库设置中添加以下Secrets：

**SSH连接配置：**
```
STAGING_SSH_PRIVATE_KEY    # 测试环境SSH私钥
STAGING_SSH_HOST          # 测试环境服务器IP
STAGING_SSH_USER          # SSH用户名 (deploy)

PRODUCTION_SSH_PRIVATE_KEY # 生产环境SSH私钥  
PRODUCTION_SSH_HOST       # 生产环境服务器IP
PRODUCTION_SSH_USER       # SSH用户名 (deploy)
```

**应用配置：**
```
API_SECRET_KEY            # API密钥
POSTGRES_PASSWORD         # PostgreSQL密码
REDIS_PASSWORD           # Redis密码
CHROMA_AUTH_CREDENTIALS  # ChromaDB认证凭据
GRAFANA_PASSWORD         # Grafana管理员密码
```

**LLM API密钥：**
```
OPENAI_API_KEY           # OpenAI API密钥
DEEPSEEK_API_KEY         # DeepSeek API密钥
DASHSCOPE_API_KEY        # DashScope API密钥
```

### 2. 配置环境

为不同环境创建对应的配置：

**测试环境 (staging)：**
- 分支：`develop`
- 域名：`staging.yourdomain.com`
- 数据库：较小配置

**生产环境 (production)：**
- 触发：Git标签 (`v*`)
- 域名：`api.yourdomain.com`
- 数据库：生产配置

### 3. 环境变量配置

将 `.env.production.template` 复制为 `.env.production`，并根据环境配置：

```bash
# 在服务器上创建环境配置
sudo -u deploy cp /opt/mem0/.env.production.template /opt/mem0/.env.production
sudo -u deploy nano /opt/mem0/.env.production
```

填入真实的配置值：
- API密钥和密码
- 数据库连接信息
- LLM服务配置
- 域名配置

## 🚀 部署流程

### 1. 自动部署（推荐）

#### 测试环境部署：
```bash
# 推送到develop分支触发自动部署
git checkout develop
git push origin develop
```

#### 生产环境部署：
```bash
# 创建版本标签触发生产部署
git tag v1.0.0
git push origin v1.0.0
```

### 2. 手动部署

如果需要手动部署：

```bash
# 登录服务器
ssh -i ~/.ssh/mem0_deploy deploy@your-server-ip

# 进入应用目录
cd /opt/mem0

# 拉取最新代码
git pull origin main

# 更新环境配置
cp .env.production.template .env.production
nano .env.production

# 构建和启动服务
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 3. 域名和SSL配置

#### 配置Nginx：
```bash
# 编辑Nginx配置
sudo nano /opt/mem0/config/nginx.conf

# 替换域名
sed -i 's/your-domain.com/yourdomain.com/g' /opt/mem0/config/nginx.conf
```

#### 配置SSL证书（Let's Encrypt）：
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d api.yourdomain.com -d monitor.yourdomain.com

# 设置自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控配置

### 1. 访问监控面板

- **Grafana**: `https://monitor.yourdomain.com`
- **Prometheus**: `https://monitor.yourdomain.com:9091`

### 2. 配置Grafana仪表板

1. 登录Grafana（admin/设置的密码）
2. 添加Prometheus数据源：`http://prometheus:9090`
3. 导入预设仪表板
4. 配置告警规则

### 3. 健康检查

系统提供多种健康检查方式：

```bash
# API健康检查
curl https://api.yourdomain.com/health

# 运行完整健康检查
python /opt/mem0/check_health.py --verbose

# 查看服务状态
docker-compose -f /opt/mem0/docker-compose.prod.yml ps

# 查看服务日志
docker-compose -f /opt/mem0/docker-compose.prod.yml logs -f mem0-api
```

## 🔍 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查日志
docker-compose -f docker-compose.prod.yml logs

# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查磁盘空间
df -h

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

#### 2. 数据库连接失败
```bash
# 检查PostgreSQL状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# 检查连接配置
docker-compose -f docker-compose.prod.yml exec mem0-api env | grep DATABASE_URL

# 重置数据库
docker-compose -f docker-compose.prod.yml down postgres
docker volume rm mem0_postgres_data
docker-compose -f docker-compose.prod.yml up -d postgres
```

#### 3. 内存不足
```bash
# 查看内存使用
free -h
docker stats

# 清理Docker镜像
docker system prune -a

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

#### 4. SSL证书问题
```bash
# 检查证书状态
sudo certbot certificates

# 手动续期
sudo certbot renew

# 重启Nginx
sudo systemctl reload nginx
```

### 日志查看

```bash
# 应用日志
tail -f /opt/mem0/logs/app.log

# Nginx日志
tail -f /opt/mem0/logs/nginx/access.log
tail -f /opt/mem0/logs/nginx/error.log

# 系统日志
journalctl -u docker -f

# 备份日志
tail -f /var/log/mem0-backup.log
```

### 性能优化

#### 1. 数据库优化
```bash
# PostgreSQL性能调优
docker-compose -f docker-compose.prod.yml exec postgres psql -U mem0 -c "
  ALTER SYSTEM SET shared_buffers = '256MB';
  ALTER SYSTEM SET effective_cache_size = '1GB';
  SELECT pg_reload_conf();
"
```

#### 2. Redis优化
```bash
# Redis内存优化
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 3. 应用优化
```bash
# 增加工作进程数
sed -i 's/--workers 4/--workers 8/g' docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml restart mem0-api
```

## 🔄 备份和恢复

### 自动备份

系统已配置自动备份：
- **时间**：每天凌晨2点
- **保留**：7天
- **位置**：`/opt/mem0/backups/`

### 手动备份

```bash
# 运行备份脚本
sudo /usr/local/bin/mem0-backup.sh

# 查看备份文件
ls -la /opt/mem0/backups/
```

### 数据恢复

```bash
# 恢复PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U mem0 -d mem0_db < backup.sql

# 恢复ChromaDB
tar -xzf chroma_backup.tar.gz -C /opt/mem0/data/

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

## 📞 技术支持

如需技术支持，请：

1. 查看[故障排除](#故障排除)部分
2. 检查GitHub Issues
3. 联系技术团队

---

**祝您部署顺利！** 🎉