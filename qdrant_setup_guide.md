# DeepSeek + Qdrant 完整部署指南

本指南将帮助您配置 **DeepSeek API + Qdrant 向量数据库** 的高性能中文记忆系统。

## 🎯 方案优势

- **🚀 高性能**: Qdrant 专为大规模向量检索优化
- **💾 持久化**: 数据自动保存到磁盘，重启不丢失
- **🔧 可扩展**: 支持水平扩展和集群部署
- **🛡️ 数据私有**: 向量数据完全在本地存储
- **💰 成本低**: 只有 DeepSeek API 调用费用

## 📋 环境要求

- Python 3.9+
- Docker（推荐）或 Qdrant 二进制文件
- 4GB+ RAM（推荐 8GB+）
- 2GB+ 磁盘空间

## 🐳 方法1：使用 Docker（推荐）

### 1.1 安装 Docker

```bash
# macOS
brew install --cask docker

# Ubuntu/Debian
sudo apt update && sudo apt install docker.io

# CentOS/RHEL
sudo yum install docker
```

### 1.2 启动 Qdrant

```bash
# 创建数据目录
mkdir -p ./qdrant_storage

# 启动 Qdrant 容器（带数据持久化）
docker run -d \
  --name qdrant-server \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# 检查服务状态
docker ps | grep qdrant
```

### 1.3 验证安装

```bash
# 检查 Qdrant API
curl http://localhost:6333

# 查看集合
curl http://localhost:6333/collections

# 查看健康状态
curl http://localhost:6333/health
```

## 🔧 方法2：本地安装 Qdrant

### 2.1 下载二进制文件

```bash
# macOS (Homebrew)
brew install qdrant

# 或手动下载
# wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
```

### 2.2 配置和启动

```bash
# 创建配置目录
mkdir -p ./qdrant_config

# 创建配置文件
cat > ./qdrant_config/config.yaml << EOF
service:
  host: 0.0.0.0
  http_port: 6333
  grpc_port: 6334

storage:
  storage_path: ./qdrant_storage

log_level: INFO
EOF

# 启动 Qdrant
qdrant --config-path ./qdrant_config/config.yaml
```

## 📦 安装 Python 依赖

```bash
# 基础安装
pip install mem0ai

# 包含向量存储支持
pip install mem0ai[vector_stores]

# Qdrant Python 客户端
pip install qdrant-client

# 中文嵌入模型支持
pip install sentence-transformers

# 可选：如果使用 OpenAI 嵌入
pip install openai
```

## 🚀 快速开始

### 1. 检查 Qdrant 连接

```bash
python deepseek_qdrant_config.py --check
```

### 2. 启动记忆系统

```bash
# 使用 HuggingFace 中文嵌入（推荐）
python deepseek_qdrant_config.py

# 或指定不同的嵌入模型
python deepseek_qdrant_config.py --config huggingface
python deepseek_qdrant_config.py --config ollama
python deepseek_qdrant_config.py --config openai
```

### 3. 基本使用示例

```python
import os
from mem0 import Memory

# 设置 API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# Qdrant 配置
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "chinese_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,  # 匹配嵌入模型维度
            "on_disk": True,  # 持久化存储
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 3000,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",
        },
    },
}

# 初始化记忆系统
m = Memory.from_config(config)

# 添加记忆
m.add("我是一名AI工程师，专注于自然语言处理和RAG技术", user_id="用户1")
m.add("我喜欢用Python开发，特别是FastAPI和Streamlit", user_id="用户1")

# 搜索记忆
results = m.search("Python开发", user_id="用户1", limit=3)
for r in results["results"]:
    print(f"记忆: {r['memory']}")
    print(f"相关度: {r['score']:.4f}")
```

## 🔧 Qdrant 管理

### 查看集合信息

```bash
# 列出所有集合
curl http://localhost:6333/collections

# 查看特定集合信息
curl http://localhost:6333/collections/chinese_memories

# 查看集合统计
curl http://localhost:6333/collections/chinese_memories/cluster
```

### Web UI 管理界面

```bash
# 启动带 Web UI 的 Qdrant
docker run -d \
  --name qdrant-webui \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# 访问 Web 界面
open http://localhost:6333/dashboard
```

### 备份和恢复

```bash
# 创建快照
curl -X POST http://localhost:6333/collections/chinese_memories/snapshots

# 下载快照
curl http://localhost:6333/collections/chinese_memories/snapshots/snapshot_name

# 从快照恢复
curl -X PUT http://localhost:6333/collections/chinese_memories/snapshots/upload \
  -H "Content-Type: application/octet-stream" \
  --data-binary @snapshot.tar
```

## 📊 性能优化

### Qdrant 配置优化

```yaml
# config.yaml
service:
  max_request_size_mb: 32
  max_workers: 4

storage:
  # 使用内存映射提升性能
  mmap_threshold_kb: 100000
  
  # 启用 WAL 以提高写入性能
  wal_capacity_mb: 32
  wal_segments_ahead: 5

# 集合级别优化
quantization:
  scalar:
    type: "int8"  # 量化以节省内存
    quantile: 0.99

indexing:
  # HNSW 索引参数
  hnsw_config:
    m: 16           # 每层连接数
    ef_construct: 100  # 构建时搜索深度
    full_scan_threshold: 10000  # 全扫描阈值
```

### 内存和磁盘优化

```python
# 配置中的优化参数
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "optimized_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,
            "on_disk": True,
            # 优化参数
            "hnsw_config": {
                "m": 16,
                "ef_construct": 100,
                "full_scan_threshold": 10000
            },
            "quantization_config": {
                "scalar": {
                    "type": "int8",
                    "quantile": 0.99
                }
            }
        },
    }
}
```

## 🔍 监控和调试

### 监控 Qdrant 性能

```bash
# 查看系统指标
curl http://localhost:6333/metrics

# 查看集合指标
curl http://localhost:6333/collections/chinese_memories

# 查看内存使用
docker stats qdrant-server
```

### 日志查看

```bash
# Docker 日志
docker logs qdrant-server -f

# 本地安装日志
tail -f /var/log/qdrant/qdrant.log
```

### 性能测试

```python
import time
from mem0 import Memory

# 性能测试脚本
def benchmark_qdrant():
    config = {...}  # 你的配置
    m = Memory.from_config(config)
    
    # 测试写入性能
    start_time = time.time()
    for i in range(100):
        m.add(f"测试记忆 {i}: 这是一条用于性能测试的中文记忆", user_id="test")
    write_time = time.time() - start_time
    
    # 测试搜索性能
    start_time = time.time()
    for i in range(50):
        results = m.search("测试记忆", user_id="test", limit=5)
    search_time = time.time() - start_time
    
    print(f"写入 100 条记忆用时: {write_time:.2f}s")
    print(f"执行 50 次搜索用时: {search_time:.2f}s")
```

## ⚠️ 常见问题

### 1. Qdrant 连接失败

```bash
# 检查端口是否被占用
lsof -i :6333

# 检查 Docker 容器状态
docker ps -a | grep qdrant

# 重启 Qdrant 容器
docker restart qdrant-server
```

### 2. 集合创建失败

```bash
# 检查向量维度是否匹配
curl http://localhost:6333/collections/your_collection/info

# 删除错误的集合
curl -X DELETE http://localhost:6333/collections/wrong_collection
```

### 3. 内存不足

```yaml
# 减少 HNSW 参数
hnsw_config:
  m: 8              # 减少连接数
  ef_construct: 50  # 减少构建时搜索深度

# 启用磁盘存储
on_disk: true

# 启用量化
quantization:
  scalar:
    type: "int8"
```

### 4. 搜索结果不准确

```python
# 调整搜索参数
results = m.search(
    query="搜索关键词",
    user_id="user",
    limit=10,           # 增加返回数量
    # 可以添加过滤条件
    filters={"type": "specific_type"}
)
```

## 📈 扩展部署

### 集群部署

```bash
# 节点 1
docker run -d --name qdrant-node1 \
  -p 6333:6333 -p 6334:6334 \
  -v ./node1_storage:/qdrant/storage \
  qdrant/qdrant

# 节点 2
docker run -d --name qdrant-node2 \
  -p 6335:6333 -p 6336:6334 \
  -v ./node2_storage:/qdrant/storage \
  qdrant/qdrant

# 配置集群
curl -X POST http://localhost:6333/cluster/setup \
  -H "Content-Type: application/json" \
  -d '{"peer_uri": "http://localhost:6335"}'
```

### 负载均衡

```python
# 配置多个 Qdrant 节点
import random

class QdrantLoadBalancer:
    def __init__(self, nodes):
        self.nodes = nodes
    
    def get_node(self):
        return random.choice(self.nodes)

# 使用示例
nodes = ["localhost:6333", "localhost:6335", "localhost:6337"]
balancer = QdrantLoadBalancer(nodes)
```

## 🔒 安全配置

### API Key 认证

```yaml
# config.yaml
service:
  api_key: your_secret_api_key

# 使用时添加认证
headers:
  api-key: your_secret_api_key
```

### 防火墙设置

```bash
# 只允许本地访问
iptables -A INPUT -p tcp --dport 6333 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 6333 -j DROP
```

这套 Qdrant 配置给您提供了生产级的高性能向量存储解决方案！🚀