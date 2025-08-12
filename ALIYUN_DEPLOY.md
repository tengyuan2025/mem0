# Mem0 API 阿里云服务器部署指南

## 🚀 阿里云 ECS 一键部署

### 前置条件

1. **阿里云 ECS 实例**
   - 推荐配置: 2核4G，带宽5M以上
   - 系统: Ubuntu 20.04/22.04 或 CentOS 7/8
   - 已分配公网IP

2. **安全组配置**
   在阿里云控制台配置安全组，开放以下端口：
   ```
   HTTP: 80/tcp (如使用域名+SSL)
   HTTPS: 443/tcp (如使用域名+SSL)  
   自定义: 8000/tcp (API端口)
   SSH: 22/tcp (管理用)
   ```

3. **域名解析** (可选)
   如需使用自定义域名，请先将域名解析到ECS公网IP

## 📦 快速部署步骤

### 步骤 1: 连接到阿里云服务器
```bash
# SSH 连接到你的阿里云 ECS
ssh root@your-ecs-public-ip

# 或使用阿里云控制台的 VNC 连接
```

### 步骤 2: 下载部署脚本
```bash
# 下载项目
git clone https://github.com/mem0ai/mem0.git
cd mem0/tests/apis

# 或直接下载阿里云部署脚本
wget https://raw.githubusercontent.com/mem0ai/mem0/main/tests/apis/deploy_aliyun.sh
chmod +x deploy_aliyun.sh
```

### 步骤 3: 设置环境变量
```bash
# 设置必需的 OpenAI API 密钥
export OPENAI_API_KEY='your-openai-api-key-here'

# 可选：设置 Mem0 API 密钥
export MEM0_API_KEY='your-mem0-api-key-here'
```

### 步骤 4: 开始部署

#### 方案 A: 简单 HTTP 部署
```bash
# 基本部署 (仅 HTTP，适合开发测试)
sudo ./deploy_aliyun.sh --port 8000 --aliyun-mirror

# 包含监控服务
sudo ./deploy_aliyun.sh --port 8000 --monitoring --aliyun-mirror
```

#### 方案 B: 完整 HTTPS 部署 (推荐)
```bash
# 需要先购买域名并解析到ECS公网IP
sudo ./deploy_aliyun.sh \
  --domain api.yourdomain.com \
  --email your-email@example.com \
  --ssl \
  --monitoring \
  --aliyun-mirror
```

## 🎯 部署后验证

### 检查服务状态
```bash
# 检查所有服务运行状态
docker-compose ps

# 检查API健康状态
curl http://your-ecs-ip:8000/health

# 如果启用了域名+SSL
curl https://api.yourdomain.com/health
```

### 访问服务面板
- **API文档**: `http://your-ecs-ip:8000/docs` 或 `https://yourdomain.com/docs`
- **Qdrant控制台**: `http://your-ecs-ip:6333/dashboard`
- **Grafana监控** (如启用): `http://your-ecs-ip:3000` (admin/admin123)
- **Prometheus** (如启用): `http://your-ecs-ip:9090`

## 🧪 API 测试

```bash
# 创建记忆测试
curl -X POST "http://your-ecs-ip:8000/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "我喜欢在阿里云上部署应用",
    "user_id": "test-user"
  }'

# 搜索记忆测试
curl -X POST "http://your-ecs-ip:8000/memories/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "部署偏好",
    "user_id": "test-user",
    "limit": 5
  }'
```

## 🔧 管理命令

```bash
# 查看服务日志
docker-compose logs mem0-api

# 重启服务
docker-compose restart

# 更新服务 (拉取最新代码)
git pull && docker-compose up --build -d

# 备份数据
docker run --rm -v mem0_qdrant_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/qdrant_backup.tar.gz -C /data .

# 停止所有服务
docker-compose down

# 完全重置 (删除所有数据)
docker-compose down --volumes
```

## 🛡️ 安全最佳实践

### 1. 服务器安全
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu
sudo yum update -y  # CentOS

# 配置防火墙 (Ubuntu)
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # API

# 配置防火墙 (CentOS)  
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 2. 环境变量安全
```bash
# 检查环境变量文件权限
ls -la .env

# 确保只有root用户可以读取
chmod 600 .env
```

### 3. 监控和日志
```bash
# 查看系统资源使用
htop

# 查看Docker资源使用
docker stats

# 设置日志轮转
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' | \
sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

## 📊 性能优化

### 阿里云 ECS 优化
1. **选择合适的实例规格**
   - 开发/测试: 2核4G (ecs.t5-large)
   - 生产环境: 4核8G+ (ecs.c6.xlarge)

2. **存储优化**
   - 使用 SSD 云盘
   - 开启多重挂载提升IO性能

3. **网络优化**  
   - 配置合适的带宽
   - 使用内网通信减少延迟

### Docker 优化
```bash
# 配置 Docker 镜像加速 (脚本已自动配置)
sudo systemctl daemon-reload
sudo systemctl restart docker

# 清理无用镜像和容器
docker system prune -f
```

## ❓ 常见问题

### 1. 端口访问不了
```bash
# 检查端口监听
sudo netstat -tlnp | grep :8000

# 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# 检查阿里云安全组是否开放端口
```

### 2. Docker 镜像拉取慢
```bash
# 脚本已配置阿里云镜像加速，如需手动配置：
sudo mkdir -p /etc/docker
echo '{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}' | sudo tee /etc/docker/daemon.json

sudo systemctl restart docker
```

### 3. SSL 证书获取失败
```bash
# 确保域名已正确解析
nslookup yourdomain.com

# 检查80端口是否被占用
sudo netstat -tlnp | grep :80

# 手动获取证书
sudo certbot certonly --standalone -d yourdomain.com
```

### 4. 内存不足
```bash
# 检查内存使用
free -h

# 添加swap空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 🆘 技术支持

- **阿里云文档**: https://help.aliyun.com/product/25365.html
- **Docker 文档**: https://docs.docker.com/
- **Mem0 项目**: https://github.com/mem0ai/mem0

## 🎉 部署完成

恭喜！你的 Mem0 API 现在已在阿里云上运行。

立即开始使用: `http://your-ecs-ip:8000/docs`

享受基于记忆的 AI 应用开发！