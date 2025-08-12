# Mem0 Docker 部署指南

这个文档介绍如何使用 Docker 部署 Mem0 API 服务。

## 🚀 快速开始

### 1. 环境准备
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，设置必需的 API 密钥
nano .env  # 至少需要设置 OPENAI_API_KEY
```

### 2. 一键部署
```bash
# 开发环境部署
./deploy.sh --env dev

# 生产环境部署
./deploy.sh --env prod --detach --monitoring
```

## 📋 部署选项

### 本地开发部署
```bash
# 启动开发环境（包含 API + Qdrant + Redis）
./deploy.sh --env dev

# 后台运行
./deploy.sh --env dev --detach

# 查看日志
./deploy.sh --logs
```

### 生产环境部署
```bash
# 生产环境部署（优化配置）
./deploy.sh --env prod --detach

# 包含监控服务的完整部署
./deploy.sh --env prod --monitoring --detach

# 强制重新构建并部署
./deploy.sh --env prod --build --detach
```

### 云服务器部署

#### 通用云服务器
```bash
sudo OPENAI_API_KEY='your-key' ./deploy_cloud.sh \
  --domain api.example.com \
  --email admin@example.com \
  --monitoring
```

#### 阿里云 ECS 服务器 ⭐
```bash
sudo OPENAI_API_KEY='your-key' ./deploy_aliyun.sh \
  --domain api.example.com \
  --email admin@example.com \
  --ssl \
  --monitoring \
  --aliyun-mirror
```

## 🏗️ 系统架构

### 开发环境 (docker-compose.yml)
- **mem0-api**: FastAPI 应用主服务
- **qdrant**: 向量数据库，用于存储和检索向量嵌入
- **redis**: 缓存服务，提高查询性能

### 生产环境 (docker-compose.prod.yml)
- **mem0-api**: 生产优化的 FastAPI 服务（2个副本）
- **qdrant**: 向量数据库（生产配置）
- **redis**: Redis 缓存（持久化配置）
- **nginx**: 反向代理和负载均衡
- **prometheus**: 监控数据收集（可选）
- **grafana**: 监控面板（可选）

## 🌐 服务访问地址

### 开发环境
- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Qdrant 面板**: http://localhost:6333/dashboard

### 生产环境
- **API 服务**: https://your-domain.com
- **API 文档**: https://your-domain.com/docs
- **健康检查**: https://your-domain.com/health
- **Prometheus**: http://localhost:9090 (如启用监控)
- **Grafana**: http://localhost:3000 (如启用监控，用户名/密码: admin/admin123)

## 🔧 管理命令

```bash
# 查看服务状态
docker-compose ps

# 停止所有服务
./deploy.sh --stop

# 清理并重新部署
./deploy.sh --clean --env dev

# 查看特定服务日志
docker-compose logs mem0-api
docker-compose logs qdrant

# 备份数据
docker run --rm -v qdrant_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/qdrant_backup.tar.gz -C /data .
```

## 📁 数据持久化

Docker 部署使用命名卷来持久化数据：
- `qdrant_data`: Qdrant 向量数据库数据
- `redis_data`: Redis 缓存数据
- `./data`: 应用数据目录
- `./logs`: 应用日志目录

## 🧪 API 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 创建记忆
curl -X POST "http://localhost:8000/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "I love Italian cuisine", 
    "user_id": "test-user"
  }'

# 搜索记忆
curl -X POST "http://localhost:8000/memories/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "food preferences", 
    "user_id": "test-user"
  }'
```

## 🛠️ 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   lsof -i :8000
   sudo netstat -tulpn | grep 8000
   ```

2. **环境变量未设置**
   ```bash
   docker-compose exec mem0-api env | grep OPENAI
   ```

3. **服务无法启动**
   ```bash
   docker-compose logs mem0-api
   docker-compose ps
   ```

### 完全重置
```bash
# 停止并删除所有容器和数据
docker-compose down --volumes --remove-orphans
docker system prune -f
```

## 📚 详细指南

- 📖 [快速开始指南](DOCKER_QUICKSTART.md)
- ☁️ [阿里云部署指南](ALIYUN_DEPLOY.md)
- 🧪 [API 测试用例](tests/apis/README.md)

## 🔐 生产环境最佳实践

1. **安全配置**
   - 使用 HTTPS（自动配置 Let's Encrypt）
   - 配置防火墙规则
   - 定期更新容器镜像

2. **监控和告警**
   - 启用 Prometheus 和 Grafana 监控
   - 配置日志聚合
   - 设置健康检查告警

3. **备份策略**
   - 定期备份 Qdrant 数据
   - 备份环境配置文件
   - 测试恢复流程

4. **资源优化**
   - 根据负载调整副本数
   - 配置资源限制
   - 监控内存和 CPU 使用