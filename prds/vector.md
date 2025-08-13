# Mem0 向量嵌入 需求与实现

## 需求：向量数据库的embeddings嵌入模型采用对中文支持程度最好的
**需求描述**: 优化向量嵌入模型配置，选择对中文支持程度最好的嵌入模型，提升中文环境下的语义搜索和记忆检索效果。

### ✅ 已实现的功能

#### 中文优化本地嵌入模型配置
- **配置文件**: `mem0/embeddings/configs.py`
- **默认配置**: 已优化为本地运行的最佳中文嵌入模型
- **默认提供商**: `huggingface` (本地运行，无需API密钥)
- **默认模型**: `BAAI/bge-large-zh-v1.5` (百度开发的中文专用模型)

#### 推荐本地中文嵌入模型选项

**1. BGE-Large-ZH (推荐 - 已设为默认) ⭐⭐⭐⭐⭐**
- **优势**: 
  - 百度开发的中文专用大模型，检索效果优秀
  - 1024维度，语义表示丰富
  - 完全本地运行，无需API密钥
  - 在中文检索任务上表现出色
- **配置示例**:
```python
{
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",
            "embedding_dims": 1024
        }
    }
}
```

**2. BGE-Base-ZH (平衡选择) ⭐⭐⭐⭐**
- **优势**:
  - BGE的基础版本，速度更快但效果略逊
  - 768维度，内存占用更小
  - 适合资源有限的环境
- **配置示例**:
```python
{
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-base-zh-v1.5",
            "embedding_dims": 768
        }
    }
}
```

**3. M3E-Large (中文多模态) ⭐⭐⭐⭐**
- **优势**:
  - Moka AI开发的中文多模态嵌入模型
  - 专门针对中文优化
  - 支持多种中文任务
- **配置示例**:
```python
{
    "embedder": {
        "provider": "huggingface", 
        "config": {
            "model": "moka-ai/m3e-large",
            "embedding_dims": 1024
        }
    }
}
```

**4. M3E-Base (轻量选择) ⭐⭐⭐⭐**
- **优势**:
  - M3E的基础版本，平衡速度和效果
  - 768维度，运行速度快
  - 适合轻量级应用
- **配置示例**:
```python
{
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "moka-ai/m3e-base", 
            "embedding_dims": 768
        }
    }
}
```

**5. Ollama 本地部署 ⭐⭐⭐⭐**
- **优势**:
  - 通过Ollama运行，管理更方便
  - 支持多种中文嵌入模型
  - 可以与本地LLM配合使用
- **安装和配置**:
```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取中文嵌入模型
ollama pull bge-large-zh
```
```python
{
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "bge-large-zh",
            "ollama_base_url": "http://localhost:11434",
            "embedding_dims": 1024
        }
    }
}
```

#### 完整中文优化配置示例

```python
from mem0 import Memory

# 使用默认的本地中文优化配置(推荐)
config = {
    "llm": {
        "provider": "doubao",  # 中文友好的LLM
        "config": {
            "model": "doubao-pro-32k", 
            "temperature": 0.1,
            "api_key": "your_doubao_api_key"
        }
    },
    "embedder": {
        "provider": "huggingface",  # 本地运行，无需API密钥
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",  # 默认本地中文模型
            "embedding_dims": 1024
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "chinese_memories",
            "url": "localhost:6333"
        }
    }
}

# 备选配置：使用轻量级模型
config_lightweight = {
    "llm": {
        "provider": "doubao",
        "config": {
            "model": "doubao-pro-32k",
            "temperature": 0.1,
            "api_key": "your_doubao_api_key"
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "moka-ai/m3e-base",  # 更轻量的中文模型
            "embedding_dims": 768
        }
    }
}

# Ollama配置：完全本地化
config_ollama = {
    "llm": {
        "provider": "ollama",  # 完全本地LLM
        "config": {
            "model": "qwen2:7b",  # 或其他中文Ollama模型
            "ollama_base_url": "http://localhost:11434"
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "bge-large-zh",
            "ollama_base_url": "http://localhost:11434",
            "embedding_dims": 1024
        }
    }
}

memory = Memory(config=config)

# 中文记忆添加示例
memory.add("我喜欢吃川菜，特别是麻婆豆腐和宫保鸡丁", user_id="chinese_user")
memory.add("我的工作是软件工程师，主要使用Python开发", user_id="chinese_user")

# 中文语义搜索
results = memory.search("我喜欢什么菜系", user_id="chinese_user")
```

#### 本地中文嵌入模型性能对比

| 模型 | 中文效果 | 运行速度 | 内存占用 | 模型大小 | 推荐度 |
|------|----------|----------|----------|----------|--------|
| BGE-Large-ZH | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ~1.3GB | ⭐⭐⭐⭐⭐ |
| BGE-Base-ZH | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~400MB | ⭐⭐⭐⭐ |
| M3E-Large | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ~1.1GB | ⭐⭐⭐⭐ |
| M3E-Base | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~400MB | ⭐⭐⭐⭐ |
| Text2Vec-Large | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ~1.0GB | ⭐⭐⭐ |

#### 安装和使用指南

**1. 安装依赖**
```bash
# 安装句子嵌入库
pip install sentence-transformers transformers

# 如果使用Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

**2. 首次使用**
- 首次运行时会自动下载指定的模型文件
- BGE-Large-ZH约1.3GB，请确保有足够存储空间
- 下载完成后，后续使用无需网络连接

**3. 推荐配置**
- **高性能场景**: BGE-Large-ZH (默认配置)
- **平衡场景**: BGE-Base-ZH 
- **轻量场景**: M3E-Base
- **完全本地**: Ollama + BGE-Large-ZH

**4. 性能优化建议**
- 在GPU环境下运行可显著提升速度
- 使用SSD存储可加快模型加载速度
- 根据内存大小选择合适的模型版本

---