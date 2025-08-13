# 中文优化 Mem0 部署指南
# Chinese-Optimized Mem0 Deployment Guide

本指南介绍如何在云服务器上部署针对中文优化的 Mem0 系统，包含本地嵌入模型和豆包LLM支持。

## 🚀 快速部署

### 方案1: 使用 Docker (推荐)

```bash
# 1. 克隆仓库
git clone https://github.com/mem0ai/mem0.git
cd mem0

# 2. 构建支持中文的Docker镜像
docker build -t mem0-chinese .

# 3. 运行容器
docker run -d \
  --name mem0-chinese \
  -p 8000:8000 \
  -e DOUBAO_API_KEY="your_doubao_api_key" \
  -v $(pwd)/data:/app/data \
  mem0-chinese

# 4. 检查运行状态
docker logs mem0-chinese
```

### 方案2: 直接部署

```bash
# 1. 安装Python环境 (推荐3.11+)
python3 -m venv mem0-env
source mem0-env/bin/activate

# 2. 安装中文优化依赖
pip install -r requirements-chinese.txt

# 3. 设置环境变量
export DOUBAO_API_KEY="your_doubao_api_key"
export MEM0_DIR="/path/to/mem0/data"

# 4. 启动服务
python -m mem0.api.main
```

## ⚙️ 配置说明

### 环境变量配置

```bash
# 必需的环境变量
export DOUBAO_API_KEY="your_doubao_api_key"        # 豆包API密钥
export ARK_API_KEY="your_ark_api_key"              # 火山引擎ARK API密钥（可选）

# 可选的环境变量  
export DOUBAO_API_BASE="https://ark.cn-beijing.volces.com/api/v3"  # 豆包API地址
export DOUBAO_ENDPOINT_ID="your_endpoint_id"       # 豆包端点ID
export MEM0_DIR="/app/data"                         # 数据存储目录
export QDRANT_URL="http://localhost:6333"          # Qdrant向量数据库地址
```

### 应用配置文件

创建 `config.json`:

```json
{
  "llm": {
    "provider": "doubao",
    "config": {
      "model": "doubao-pro-32k",
      "temperature": 0.1,
      "api_key": "${DOUBAO_API_KEY}"
    }
  },
  "embedder": {
    "provider": "huggingface",
    "config": {
      "model": "BAAI/bge-large-zh-v1.5",
      "embedding_dims": 1024
    }
  },
  "vector_store": {
    "provider": "qdrant",
    "config": {
      "collection_name": "chinese_memories",
      "url": "${QDRANT_URL}"
    }
  }
}
```

## 🖥️ 服务器要求

### 最小配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间
- **网络**: 稳定的互联网连接（用于下载模型）

### 推荐配置
- **CPU**: 4核心以上（推荐GPU）
- **内存**: 8GB+ RAM
- **存储**: 20GB+ SSD存储
- **GPU**: 可选，但能显著提升嵌入模型性能

### 模型存储需求
- **BGE-Large-ZH**: ~1.3GB
- **BGE-Base-ZH**: ~400MB  
- **M3E-Large**: ~1.1GB
- **M3E-Base**: ~400MB

## 🐳 Docker Compose 部署

创建 `docker-compose-chinese.yml`:

```yaml
version: '3.8'
services:
  mem0-chinese:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DOUBAO_API_KEY=${DOUBAO_API_KEY}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - qdrant
    restart: unless-stopped
    
  qdrant:
    image: qdrant/qdrant:v1.8.1
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage
    restart: unless-stopped

networks:
  default:
    name: mem0-network
```

部署命令：
```bash
# 启动服务栈
docker-compose -f docker-compose-chinese.yml up -d

# 查看日志
docker-compose -f docker-compose-chinese.yml logs -f mem0-chinese

# 停止服务
docker-compose -f docker-compose-chinese.yml down
```

## 🔧 性能优化

### GPU加速配置

如果服务器有GPU，修改Dockerfile：

```dockerfile
# 使用CUDA基础镜像
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# 安装PyTorch GPU版本
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 内存优化

对于内存受限的服务器，使用轻量级模型：

```python
config = {
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "moka-ai/m3e-base",  # 使用轻量版本
            "embedding_dims": 768
        }
    }
}
```

## 🌐 负载均衡配置

### Nginx配置示例

```nginx
upstream mem0_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # 如果有多个实例
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://mem0_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## 🔍 监控和日志

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查中文功能
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "我是软件工程师"}],
    "user_id": "test_user"
  }'
```

### 日志配置

在生产环境中启用结构化日志：

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': record.created,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        }
        return json.dumps(log_entry, ensure_ascii=False)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/mem0.log')
    ]
)
```

## 🚨 故障排除

### 常见问题

**1. 模型下载失败**
```bash
# 手动下载模型
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
print('模型下载完成')
"
```

**2. 内存不足**
```bash
# 检查内存使用
docker stats mem0-chinese

# 使用轻量模型
export MODEL_NAME="moka-ai/m3e-base"
```

**3. API连接失败**
```bash
# 测试豆包API连接
curl -X POST "https://ark.cn-beijing.volces.com/api/v3/chat/completions" \
  -H "Authorization: Bearer $DOUBAO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"doubao-pro-32k","messages":[{"role":"user","content":"测试"}]}'
```

## 📈 扩展部署

### 多实例部署

```bash
# 启动多个实例
for i in {8000..8002}; do
  docker run -d \
    --name mem0-chinese-$i \
    -p $i:8000 \
    -e DOUBAO_API_KEY="$DOUBAO_API_KEY" \
    mem0-chinese
done
```

### 数据备份

```bash
# 备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf mem0_backup_$DATE.tar.gz \
  ./data \
  ./qdrant_data \
  ./logs

# 定时备份 (crontab)
0 2 * * * /path/to/backup_script.sh
```

## 🔐 安全配置

### API认证

```python
# 添加API密钥认证
from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=403, detail="Invalid authentication")
    return credentials.credentials
```

### 防火墙配置

```bash
# Ubuntu/Debian
ufw allow 8000/tcp
ufw allow 6333/tcp  # Qdrant
ufw enable

# CentOS/RHEL  
firewall-cmd --add-port=8000/tcp --permanent
firewall-cmd --add-port=6333/tcp --permanent
firewall-cmd --reload
```

---

## 📞 获取支持

- **文档**: 查看 `prds/vector.md` 和 `prds/llm.md`
- **测试**: 运行 `python -m pytest tests/`
- **配置验证**: 运行健康检查端点

部署成功后，你将拥有一个完全针对中文优化的Mem0系统，支持本地嵌入和豆包LLM！