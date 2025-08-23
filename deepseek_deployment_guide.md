# DeepSeek + Mem0 本地部署指南

本指南展示如何使用 **DeepSeek API** 作为大模型，配合**本地向量存储**，实现完全的记忆数据私有化。

## 🎯 方案特点

- **LLM**: DeepSeek API（强大的中文理解和生成能力）
- **向量存储**: 本地 Qdrant/FAISS/Chroma（数据完全私有）
- **嵌入模型**: 多种选择（HuggingFace/OpenAI/Ollama）
- **成本**: 只有 LLM 调用费用，向量存储和嵌入免费
- **🌟 推荐**: Qdrant + HuggingFace 中文嵌入（高性能 + 免费）

## 📋 前置准备

### 1. DeepSeek API Key
已为您配置：`sk-760dd8899ad54634802aafb839f8bda9`

### 2. 安装依赖

```bash
# 基础安装
pip install mem0ai

# 包含向量存储依赖
pip install mem0ai[vector_stores]

# 如果选择 HuggingFace 嵌入
pip install sentence-transformers

# 如果选择本地 FAISS
pip install faiss-cpu  # 或 faiss-gpu（有CUDA时）

# Qdrant 向量数据库（推荐高性能选项）
pip install qdrant-client
```

## 🚀 快速开始

### 🌟 方法1：Qdrant 高性能版本（推荐）

```bash
# 1. 启动 Qdrant 向量数据库
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# 2. 安装依赖
pip install mem0ai[vector_stores] sentence-transformers qdrant-client

# 3. 快速测试
python quick_start_qdrant.py

# 4. 运行完整系统
python deepseek_qdrant_config.py
```

### 方法2：FAISS 简化版本

```bash
# 1. 安装依赖
pip install mem0ai[vector_stores] sentence-transformers

# 2. 快速测试  
python quick_start_deepseek.py

# 3. 运行完整系统
python deepseek_chinese_config.py
```

## 🔧 配置选项

### 🌟 方案 1: Qdrant + HuggingFace 中文嵌入（推荐）

高性能向量存储 + 免费中文嵌入：

```python
import os
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_chinese_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,  # BAAI/bge-large-zh-v1.5
            "on_disk": True,  # 持久化存储
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",  # 中文语义最佳
        },
    },
}

m = Memory.from_config(config)
```

### 方案 2: FAISS + HuggingFace 中文嵌入

完全免费，中文语义理解优秀：

```python
import os
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "deepseek_chinese_memories",
            "path": "./deepseek_faiss_index",
            "embedding_model_dims": 1024,  # BAAI/bge-large-zh-v1.5
            "distance_strategy": "cosine",
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",  # 中文语义最佳
        },
    },
}

m = Memory.from_config(config)
```

### 方案 2: OpenAI 嵌入（需要 OpenAI Key）

如果您有 OpenAI API Key，效果也很好：

```python
# 需要额外设置 OpenAI API Key
os.environ["OPENAI_API_KEY"] = "your-openai-key"

config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "deepseek_openai_memories",
            "path": "./deepseek_openai_index", 
            "embedding_model_dims": 1536,
            "distance_strategy": "cosine",
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
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
        },
    },
}
```

### 方案 3: Ollama 本地嵌入

需要先安装和运行 Ollama：

```bash
# 安装 Ollama
brew install ollama  # macOS

# 启动服务
ollama serve

# 下载中文嵌入模型
ollama pull bge-m3:latest
```

配置：
```python
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "deepseek_ollama_memories",
            "path": "./deepseek_ollama_index",
            "embedding_model_dims": 1024,
            "distance_strategy": "cosine",
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
        "provider": "ollama",
        "config": {
            "model": "bge-m3:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}
```

## 🚀 快速开始

### 1. 运行现成的脚本

```bash
# 使用 HuggingFace 嵌入（推荐，完全免费）
python deepseek_chinese_config.py

# 或指定其他配置
python deepseek_chinese_config.py --config huggingface
python deepseek_chinese_config.py --config ollama
python deepseek_chinese_config.py --config openai
```

### 2. 测试所有配置

```bash
python deepseek_chinese_config.py --test
```

### 3. 简单使用示例

```python
from mem0 import Memory
import os

os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# 使用 HuggingFace 配置
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "test_memories",
            "path": "./test_index",
            "embedding_model_dims": 1024,
            "distance_strategy": "cosine",
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
    },
    "embedder": {
        "provider": "huggingface", 
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",
        },
    },
}

m = Memory.from_config(config)

# 添加中文记忆
m.add("我最喜欢的编程语言是Python，特别喜欢用它做数据分析", user_id="张三")
m.add("我住在上海，是一名AI工程师", user_id="张三")
m.add("我的爱好是读书和跑步，周末经常去公园", user_id="张三")

# 搜索相关记忆
results = m.search("Python编程", user_id="张三", limit=3)
print("相关记忆:")
for r in results["results"]:
    print(f"- {r['memory']} (相关度: {r['score']:.3f})")

# 获取所有记忆
all_memories = m.get_all(user_id="张三")
print(f"\n总共有 {len(all_memories['results'])} 条记忆")
```

## 📊 性能和成本

### DeepSeek API 优势
- **成本低**: 输入 ¥0.14/万tokens，输出 ¥0.28/万tokens
- **中文优秀**: 专门优化的中文理解能力
- **响应快**: 平均延迟较低
- **模型强**: 接近 GPT-4 级别能力

### 本地向量存储优势
- **完全免费**: 向量存储和搜索无额外费用
- **数据私有**: 敏感信息不会上传到云端
- **速度快**: 本地检索延迟极低
- **可控制**: 完全控制数据存储和索引

### 嵌入模型选择建议
| 方案 | 费用 | 中文效果 | 安装复杂度 | 推荐指数 |
|------|------|----------|------------|----------|
| HuggingFace | 免费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 🥇 推荐 |
| Ollama | 免费 | ⭐⭐⭐⭐ | ⭐⭐ | 🥈 不错 |  
| OpenAI | 付费 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥉 备选 |

## 🛠️ 常见问题

### 1. HuggingFace 模型下载慢
```bash
# 设置国内镜像
export HF_ENDPOINT=https://hf-mirror.com
```

### 2. FAISS 安装问题
```bash
# macOS with Apple Silicon
pip install faiss-cpu

# Linux with CUDA
pip install faiss-gpu
```

### 3. DeepSeek API 错误
- 检查 API Key 是否正确设置
- 确认网络连接正常
- 注意 rate limit（每分钟请求限制）

### 4. 中文搜索效果不好
- 确保使用中文优化的嵌入模型（如 bge-large-zh-v1.5）
- 设置 distance_strategy 为 "cosine"
- 增加搜索的 limit 参数

## 💡 使用技巧

### 1. 提高中文语义搜索质量
- 使用完整句子而不是单词作为记忆
- 在记忆中包含上下文信息
- 使用一致的表达方式

### 2. 优化存储结构
- 按主题或时间组织记忆
- 使用 metadata 添加标签和分类
- 定期清理无用的记忆

### 3. 控制成本
- 合理设置 max_tokens 避免过长生成
- 使用本地嵌入模型减少API调用
- 批量处理多个记忆操作

## 🔧 高级配置

### 自定义 DeepSeek 参数
```python
"llm": {
    "provider": "deepseek",
    "config": {
        "model": "deepseek-chat",
        "temperature": 0.7,        # 创造性
        "max_tokens": 3000,        # 最大输出长度
        "top_p": 0.9,             # 核采样
        "frequency_penalty": 0.1,  # 频率惩罚
        "presence_penalty": 0.1,   # 存在惩罚
    },
}
```

### 🗄️ 向量数据库选择

#### 方案 A: Qdrant（🌟 推荐高性能）
```python
"vector_store": {
    "provider": "qdrant", 
    "config": {
        "collection_name": "deepseek_memories",
        "host": "localhost",
        "port": 6333,
        "embedding_model_dims": 1024,
        "on_disk": True,  # 持久化存储
    },
}
```

**优势**: 
- 🚀 高性能向量检索
- 💾 数据持久化
- 🔧 可扩展到集群
- 📊 Web 管理界面

**启动 Qdrant**:
```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

#### 方案 B: FAISS（简单本地）
```python
"vector_store": {
    "provider": "faiss",
    "config": {
        "collection_name": "deepseek_memories",
        "path": "./faiss_index",
        "embedding_model_dims": 1024,
        "distance_strategy": "cosine",
    },
}
```

#### 方案 C: Chroma（功能丰富）
```python
"vector_store": {
    "provider": "chroma",
    "config": {
        "collection_name": "deepseek_memories",
        "path": "./chroma_db",
    },
}
```

这套配置可以给您最佳的中文记忆体验：DeepSeek 的强大理解能力 + 本地数据完全私有 + 专业的中文嵌入模型！