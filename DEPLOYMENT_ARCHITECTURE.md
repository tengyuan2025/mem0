# Mem0 本地部署架构说明

## 🏗️ 部署架构概述

本项目是**完整的Mem0源代码自托管部署**，而不是使用Mem0云服务的API客户端。

### 📦 镜像内容构成

Docker镜像包含以下组件：

#### 1. 🐍 Python运行环境
- **基础镜像**: `python:3.11-slim`
- **系统工具**: gcc, git, curl等编译和网络工具
- **Python包管理**: pip, 虚拟环境支持

#### 2. 🧠 Mem0核心框架 (本地源代码)
```
/app/mem0/              # 📁 Mem0源代码 (本项目)
├── api/                # 🌐 FastAPI接口层
├── memory/             # 🧠 记忆管理核心
├── llms/               # 🤖 LLM提供商接口
├── embeddings/         # 📊 嵌入模型接口  
├── vector_stores/      # 🔍 向量数据库接口
├── configs/            # ⚙️ 配置管理
└── utils/              # 🛠️ 工具函数
```

**重要**: 镜像**不安装**`mem0ai`PyPI包，而是直接使用本地源代码！

#### 3. 🚀 Web服务框架
```python
fastapi>=0.104.0          # 现代Python Web框架
uvicorn[standard]>=0.24.0 # ASGI服务器
pydantic>=2.7.3           # 数据验证
python-multipart>=0.0.6   # 文件上传支持
```

#### 4. 🇨🇳 中文AI能力栈
```python
sentence-transformers>=3.0.0  # 句子嵌入框架
transformers>=4.30.0          # HuggingFace模型
torch>=1.11.0                 # PyTorch深度学习
huggingface-hub>=0.20.0       # 模型管理
```

**预配置模型**:
- `BAAI/bge-large-zh-v1.5` - 中文语义嵌入
- 支持本地运行，无需外部API

#### 5. 🔌 外部服务接口
```python
qdrant-client>=1.9.1     # Qdrant向量数据库
openai>=1.33.0           # OpenAI兼容API (豆包等)
sqlalchemy>=2.0.31       # 关系数据库ORM
```

## 🏛️ 系统架构图

```
┌─────────────────────────────────────────┐
│           Docker Container              │
│  ┌─────────────────────────────────┐    │
│  │        Mem0 API Service         │    │
│  │     (FastAPI + Uvicorn)         │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐    │    │
│  │  │     Memory Core         │    │    │
│  │  │   (本地源代码)           │    │    │
│  │  └─────────────────────────┘    │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐    │    │
│  │  │   BGE-Large-ZH Model    │    │    │
│  │  │    (中文嵌入模型)        │    │    │
│  │  └─────────────────────────┘    │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
           │                    │
           │                    │
    ┌─────────────┐      ┌─────────────┐
    │   Qdrant    │      │   豆包API   │
    │ Vector DB   │      │  (External) │
    └─────────────┘      └─────────────┘
```

## 🎯 与Mem0云服务的区别

| 特性 | 本地部署 (本项目) | Mem0云服务 |
|------|------------------|------------|
| **代码位置** | 本地源代码 | 远程API调用 |
| **数据控制** | 完全本地 | 存储在Mem0服务器 |
| **定制能力** | 完全可定制 | 有限定制 |
| **中文优化** | 深度优化 | 标准支持 |
| **成本** | 仅基础设施 | 按使用量付费 |
| **隐私** | 完全私有 | 数据上传到云端 |

## 📋 部署模式对比

### 🏠 本地开发模式
```bash
./start-local.sh
```
- Python虚拟环境
- Docker只运行数据库
- 最快的开发体验

### 🐳 完整容器化模式  
```bash
./start-dev.sh
```
- 所有服务都在Docker中
- 与生产环境一致
- 完全隔离的环境

### 🚀 生产部署模式
```bash
docker-compose -f docker-compose.yml up -d
```
- 多实例负载均衡
- 数据持久化
- 监控和日志

## 🔧 核心配置

### 环境变量配置
```bash
# LLM配置 (不依赖Mem0云服务)
MEM0_LLM_PROVIDER=doubao
DOUBAO_API_KEY=your_key

# 嵌入模型 (完全本地)
MEM0_EMBEDDER_PROVIDER=huggingface
MEM0_EMBEDDER_MODEL=BAAI/bge-large-zh-v1.5

# 向量数据库 (本地Qdrant)
MEM0_VECTOR_STORE_PROVIDER=qdrant
QDRANT_HOST=localhost
```

### 目录挂载
```yaml
volumes:
  - .:/app                          # 源代码挂载 (开发模式)
  - mem0_data:/app/data            # 数据持久化
  - huggingface_cache:/root/.cache # 模型缓存
```

## 💡 关键优势

1. **📚 完整源代码控制**
   - 可以修改任何功能
   - 添加自定义特性
   - 深度集成其他系统

2. **🇨🇳 中文深度优化**
   - 专用中文嵌入模型
   - 优化的中文分词和语义理解
   - 豆包LLM原生支持

3. **🔒 数据完全私有**
   - 所有数据保存在本地
   - 不依赖外部云服务
   - 符合数据安全要求

4. **💰 成本控制**
   - 只需要LLM API费用
   - 嵌入模型完全免费
   - 无按量付费

5. **🚀 高性能**
   - 本地嵌入模型推理
   - 减少网络延迟
   - 可以使用GPU加速

这就是为什么镜像里不包含`mem0ai`包的原因 - 我们直接使用和修改源代码，实现真正的自托管部署！