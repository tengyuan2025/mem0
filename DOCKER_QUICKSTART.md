# Mem0 API 快速开始指南

## 🚀 5分钟快速部署

### 方法一：Docker 一键部署（推荐）

#### 1. 准备环境
```bash
# 克隆项目
git clone https://github.com/mem0ai/mem0.git
cd mem0/tests/apis

# 复制环境配置
cp .env.example .env
```

#### 2. 配置 API 密钥
编辑 `.env` 文件，至少设置：
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

#### 3. 一键启动
```bash
# 开发环境（前台运行，方便调试）
./deploy.sh --env dev

# 或者后台运行
./deploy.sh --env dev --detach
```

#### 4. 验证部署
```bash
# 检查健康状态
curl http://localhost:8000/health

# 访问 API 文档
open http://localhost:8000/docs
```

### 方法二：云服务器部署

在云服务器（Ubuntu/CentOS）上一键部署：

```bash
# 设置环境变量
export OPENAI_API_KEY='your-api-key'

# 一键部署（需要 root 权限）
sudo ./deploy_cloud.sh \
  --domain api.example.com \
  --email admin@example.com \
  --monitoring
```

## 🎯 快速测试

### API 测试
```bash
# 创建记忆
curl -X POST "http://localhost:8000/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "I love Italian cuisine, especially pasta and pizza",
    "user_id": "user-123"
  }'

# 搜索记忆
curl -X POST "http://localhost:8000/memories/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "food preferences", 
    "user_id": "user-123",
    "limit": 5
  }'
```

### Python 客户端测试
```python
import requests

# API 基础 URL
BASE_URL = "http://localhost:8000"

# 创建记忆
response = requests.post(f"{BASE_URL}/memories", json={
    "messages": "I prefer tea over coffee in the morning",
    "user_id": "user-456"
})
print("Created memory:", response.json())

# 搜索记忆
response = requests.post(f"{BASE_URL}/memories/search", json={
    "query": "beverage preferences",
    "user_id": "user-456",
    "limit": 3
})
print("Search results:", response.json())
```

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
./deploy.sh --logs

# 停止服务
./deploy.sh --stop

# 重新部署
./deploy.sh --env dev --build

# 清理重置
./deploy.sh --clean
```

## 📊 访问面板

启动后可访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Qdrant 面板**: http://localhost:6333/dashboard

## ⚡ 生产环境部署

```bash
# 生产环境 + 监控
./deploy.sh --env prod --monitoring --detach

# 访问监控面板
open http://localhost:3000  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
```

## 🆘 故障排除

### 端口被占用
```bash
# 检查端口占用
lsof -i :8000
sudo netstat -tulpn | grep 8000

# 更改端口
./deploy.sh --env dev --port 8080
```

### API 密钥问题
```bash
# 检查环境变量
cat .env | grep OPENAI_API_KEY

# 重新设置
echo "OPENAI_API_KEY=your_new_key" >> .env
./deploy.sh --env dev --build
```

### 服务无法启动
```bash
# 查看详细日志
docker-compose logs mem0-api

# 检查容器状态
docker-compose ps

# 重新构建
./deploy.sh --env dev --build --clean
```

## 📚 更多文档

- [完整 API 文档](README.md)
- [测试指南](test_memory_api.py)
- [配置说明](.env.example)

## 🎉 完成！

现在您的 Mem0 API 已经运行在 http://localhost:8000

可以开始通过 API 管理 AI 记忆了！