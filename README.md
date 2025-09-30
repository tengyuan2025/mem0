# Mem0 自托管部署方案

一个完全自托管的智能记忆系统，支持国内LLM服务，专为中文场景优化。

## 🌟 特性

- ✅ **完全自托管**：所有数据和服务都在您的服务器上运行
- ✅ **支持国内LLM**：集成通义千问、文心一言、智谱AI、DeepSeek等国内服务
- ✅ **中文优化**：专门针对中文场景进行优化
- ✅ **多种存储方案**：支持向量数据库、图数据库、关系型数据库
- ✅ **Docker部署**：一键部署所有服务
- ✅ **RESTful API**：标准的HTTP API接口
- ✅ **安全认证**：内置API密钥认证

## 📋 系统要求

- Python 3.9+ 或 Docker
- 4GB+ RAM
- 10GB+ 磁盘空间
- Linux/macOS/Windows

## 🚀 快速开始

### 方式一：Docker Compose部署（推荐）

1. **克隆项目**
```bash
git clone <your-repo>
cd mem0
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置您的LLM API密钥
vim .env
```

3. **启动服务**
```bash
chmod +x start.sh
./start.sh
# 选择选项 1 (Docker Compose)
```

4. **测试服务**
```bash
python test_api.py
```

### 方式二：本地Python环境

1. **安装依赖**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
vim .env
```

3. **启动必要的服务**
```bash
# 需要手动启动PostgreSQL、Redis、ChromaDB等服务
# 或使用docker-compose只启动数据库服务：
docker-compose up -d postgres redis chromadb neo4j
```

4. **启动API服务**
```bash
python app.py
```

## 🔧 配置说明

### LLM配置

支持以下国内LLM服务，在 `.env` 文件中选择配置：

#### 阿里云通义千问（推荐）
```env
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_MODEL=qwen-max
```

#### 百度文心一言
```env
LLM_PROVIDER=qianfan
QIANFAN_AK=your-ak
QIANFAN_SK=your-sk
QIANFAN_MODEL=ERNIE-Bot-4
```

#### 智谱AI
```env
LLM_PROVIDER=zhipu
ZHIPUAI_API_KEY=your-api-key
ZHIPUAI_MODEL=glm-4
```

#### DeepSeek
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_MODEL=deepseek-chat
```

### Embedding配置

支持API调用和完全本地的嵌入模型：

#### 本地中文嵌入模型（推荐，无需API）
```env
EMBEDDING_PROVIDER=local_huggingface
HF_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 最佳中文嵌入模型
```

推荐的中文本地模型（按性能排序）：
- `BAAI/bge-large-zh-v1.5` - 最佳中文效果
- `BAAI/bge-base-zh-v1.5` - 平衡性能和速度  
- `BAAI/bge-small-zh-v1.5` - 最快速度

首次使用会自动下载模型文件（约1-2GB）。

#### API调用方式
```env
# 阿里云通义千问
EMBEDDING_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
```

### 向量数据库配置

默认使用ChromaDB，也支持Qdrant和FAISS：

```env
# ChromaDB（默认）
VECTOR_DB=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Qdrant
VECTOR_DB=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# FAISS（本地文件）
VECTOR_DB=faiss
FAISS_INDEX_PATH=./data/faiss_index
```

## 📚 API文档

### 认证

所有API请求需要在Header中包含Bearer Token：

```http
Authorization: Bearer your-secret-key-change-this
```

### 主要端点

#### 1. 添加记忆
```http
POST /api/v1/memories/add
Content-Type: application/json

{
  "user_id": "user_001",
  "messages": [
    {"role": "user", "content": "我喜欢喝咖啡"},
    {"role": "assistant", "content": "了解了"}
  ],
  "metadata": {"category": "preference"}
}
```

#### 2. 搜索记忆
```http
POST /api/v1/memories/search
Content-Type: application/json

{
  "user_id": "user_001",
  "query": "咖啡",
  "limit": 10
}
```

#### 3. 聊天（带记忆）
```http
POST /api/v1/chat
Content-Type: application/json

{
  "user_id": "user_001",
  "message": "你知道我喜欢喝什么吗？",
  "use_memory": true
}
```

#### 4. 获取用户所有记忆
```http
GET /api/v1/users/{user_id}/memories?limit=100
```

#### 5. 更新记忆
```http
POST /api/v1/memories/update
Content-Type: application/json

{
  "memory_id": "memory_id_here",
  "content": "新的记忆内容",
  "metadata": {"updated": true}
}
```

#### 6. 删除记忆
```http
POST /api/v1/memories/delete
Content-Type: application/json

{
  "memory_id": "memory_id_here"
}
```

完整的API文档可在服务启动后访问：http://localhost:9000/docs

## 🚢 部署到阿里云

### 1. 准备阿里云服务器

- ECS实例：4核8G或以上
- 操作系统：Ubuntu 20.04/22.04 或 CentOS 7/8
- 开放端口：9000（API）、8001（ChromaDB，可选）

### 2. 安装Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 部署服务

```bash
# 上传项目文件到服务器
scp -r ./* user@your-server:/home/user/mem0/

# SSH登录服务器
ssh user@your-server

# 进入项目目录
cd /home/user/mem0

# 配置环境变量
cp .env.example .env
vim .env  # 配置您的API密钥

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f mem0-api
```

### 4. 配置Nginx反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5. 配置SSL证书（可选）

使用Let's Encrypt免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🔍 监控和维护

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 所有服务
docker-compose logs

# 特定服务
docker-compose logs -f mem0-api
```

### 备份数据
```bash
# 备份PostgreSQL
docker-compose exec postgres pg_dump -U mem0 mem0_db > backup.sql

# 备份向量数据库
docker-compose exec chromadb tar -czf /tmp/chroma-backup.tar.gz /chroma/data
docker cp mem0-chromadb:/tmp/chroma-backup.tar.gz ./
```

### 更新服务
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## 🐛 故障排查

### 1. 服务无法启动

检查端口占用：
```bash
sudo lsof -i :9000
sudo lsof -i :8001
```

### 2. LLM调用失败

- 检查API密钥是否正确
- 检查网络连接
- 查看详细日志：`docker-compose logs mem0-api`

### 3. 向量数据库连接失败

确保ChromaDB服务正在运行：
```bash
docker-compose ps chromadb
curl http://localhost:8001/api/v1/heartbeat
```

## 📊 性能优化

### 1. 增加并发处理能力

编辑 `Dockerfile`，修改启动命令：
```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "4"]
```

### 2. 配置Redis缓存

在 `.env` 中启用Redis：
```env
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3. 优化向量搜索

- 使用Qdrant代替ChromaDB以获得更好的性能
- 调整搜索参数和索引配置

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请：
1. 查看[故障排查](#-故障排查)部分
2. 提交GitHub Issue
3. 查看日志：`docker-compose logs`

---

**注意**：请务必修改默认的API密钥和数据库密码以确保安全！