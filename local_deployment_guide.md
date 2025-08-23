# Mem0 本地部署指南

本指南将帮助你在本机完全部署 mem0，不依赖任何外部 API 服务。

## 前置要求

### 1. 安装 Ollama（本地 LLM）

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# 从 https://ollama.ai/download 下载安装包
```

启动 Ollama 服务：
```bash
ollama serve
```

下载需要的模型（**中文场景优化**）：
```bash
# 下载中文 LLM 模型（按优先级推荐）
ollama pull qwen2.5:14b           # 🌟 最佳中文支持，推荐
ollama pull qwen2.5:32b           # 更强但更慢
ollama pull yi:34b                # Yi 系列中文很好
ollama pull deepseek-v2:16b       # DeepSeek 中文不错
ollama pull llama3.1:8b           # 备选，多语言

# 下载中文嵌入模型（必需，中文语义理解）
ollama pull bge-m3:latest         # 🌟 BAAI 中文嵌入模型，最佳
ollama pull nomic-embed-text:latest  # 备选，多语言支持
```

### 2. 选择并安装向量数据库

#### 方案 A: 使用 FAISS（最简单，纯本地）

```bash
# CPU 版本
pip install faiss-cpu

# GPU 版本（如果有 CUDA）
pip install faiss-gpu
```

#### 方案 B: 使用 Chroma（功能更丰富）

```bash
pip install chromadb
```

#### 方案 C: 使用 Qdrant（推荐，性能好）

```bash
# 使用 Docker 运行 Qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant

# 或者直接下载二进制文件
# macOS
brew install qdrant

# 其他系统参考：https://qdrant.tech/documentation/guides/installation/
```

### 3. 安装 mem0

```bash
# 基础安装
pip install mem0ai

# 包含所有本地依赖
pip install mem0ai[llms,vector_stores]

# 或者从源码安装（开发版本）
cd /Users/yushuangyang/workspace/mem0
pip install -e ".[llms,vector_stores]"
```

## 配置示例

### 🌟 中文优化配置（推荐）

针对中文内容优化的配置：

创建文件 `chinese_config.py`：

```python
from mem0 import Memory

# 中文优化配置
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "chinese_memories",
            "path": "./chinese_faiss_index",
            "embedding_model_dims": 1024,  # BGE 模型维度
            "distance_strategy": "cosine",  # 余弦相似度更适合中文
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5:14b",  # 中文支持最佳
            "temperature": 0.7,
            "max_tokens": 3000,
            "ollama_base_url": "http://localhost:11434",
            # 中文优化参数
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "bge-m3:latest",  # BAAI 中文嵌入模型
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

# 初始化
m = Memory.from_config(config)

# 中文测试
def test_chinese():
    # 添加中文记忆
    m.add("我喜欢在周末去公园散步，特别是樱花盛开的时候", user_id="用户1")
    m.add("我对机器学习和人工智能很感兴趣，正在学习PyTorch", user_id="用户1") 
    m.add("我住在北京，工作是软件工程师", user_id="用户1")
    
    # 搜索测试
    print("搜索'公园'相关记忆：")
    results = m.search("公园", user_id="用户1", limit=3)
    for r in results["results"]:
        print(f"- {r['memory']} (相关度: {r['score']:.3f})")

if __name__ == "__main__":
    test_chinese()
```

### 1. 使用 FAISS + Ollama（基础配置）

创建文件 `local_mem0_faiss.py`：

```python
from mem0 import Memory

# FAISS 配置（完全本地，无需额外服务）
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "my_memories",
            "path": "./faiss_index",  # 本地存储路径
            "embedding_model_dims": 768,  # nomic-embed-text 的维度
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",  # 或使用你下载的其他模型
            "temperature": 0.7,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

# 初始化 Memory
m = Memory.from_config(config)

# 使用示例
def test_memory():
    # 添加记忆
    m.add("我喜欢喝咖啡，特别是拿铁", user_id="user1")
    m.add("我对Python编程很感兴趣", user_id="user1")
    m.add("我住在北京", user_id="user1")
    
    # 搜索相关记忆
    print("搜索咖啡相关的记忆：")
    results = m.search("咖啡", user_id="user1", limit=3)
    for r in results["results"]:
        print(f"- {r['memory']} (相关度: {r['score']:.3f})")
    
    # 获取所有记忆
    print("\n所有记忆：")
    all_memories = m.get_all(user_id="user1")
    for mem in all_memories["results"]:
        print(f"- {mem['memory']}")

if __name__ == "__main__":
    test_memory()
```

### 2. 使用 Chroma + Ollama

创建文件 `local_mem0_chroma.py`：

```python
from mem0 import Memory
import chromadb

# 创建本地 Chroma 客户端
chroma_client = chromadb.PersistentClient(path="./chroma_db")

config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "my_memories",
            "client": chroma_client,  # 使用本地客户端
            "embedding_model_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5:latest",  # 使用中文模型
            "temperature": 0.7,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

m = Memory.from_config(config)
```

### 3. 使用 Qdrant + Ollama（推荐配置）

创建文件 `local_mem0_qdrant.py`：

```python
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "my_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",
            "temperature": 0.7,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

m = Memory.from_config(config)
```

## 完整应用示例

创建文件 `local_chat_app.py`：

```python
from mem0 import Memory
import sys

# 使用 FAISS 配置（最简单）
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "chat_memories",
            "path": "./chat_faiss_index",
            "embedding_model_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",
            "temperature": 0.7,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

class LocalChatBot:
    def __init__(self, user_id="default_user"):
        self.memory = Memory.from_config(config)
        self.user_id = user_id
        print("本地聊天机器人已启动！")
        print("输入 '/memories' 查看所有记忆")
        print("输入 '/clear' 清除记忆")
        print("输入 '/exit' 退出\n")
    
    def chat(self, message):
        # 搜索相关记忆
        relevant_memories = self.memory.search(
            query=message, 
            user_id=self.user_id, 
            limit=3
        )
        
        # 添加新记忆
        self.memory.add(message, user_id=self.user_id)
        
        # 返回相关记忆
        if relevant_memories["results"]:
            print("\n相关记忆：")
            for mem in relevant_memories["results"]:
                print(f"  - {mem['memory']}")
            print()
    
    def show_memories(self):
        memories = self.memory.get_all(user_id=self.user_id)
        if memories["results"]:
            print("\n所有记忆：")
            for i, mem in enumerate(memories["results"], 1):
                print(f"  {i}. {mem['memory']}")
                print(f"     ID: {mem['id']}")
        else:
            print("\n暂无记忆")
    
    def clear_memories(self):
        # 获取所有记忆并删除
        memories = self.memory.get_all(user_id=self.user_id)
        for mem in memories["results"]:
            self.memory.delete(memory_id=mem['id'])
        print("所有记忆已清除")
    
    def run(self):
        while True:
            try:
                user_input = input("你: ").strip()
                
                if user_input.lower() == '/exit':
                    print("再见！")
                    break
                elif user_input.lower() == '/memories':
                    self.show_memories()
                elif user_input.lower() == '/clear':
                    self.clear_memories()
                elif user_input:
                    self.chat(user_input)
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except Exception as e:
                print(f"错误: {e}")

if __name__ == "__main__":
    # 可以指定用户 ID
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default_user"
    bot = LocalChatBot(user_id=user_id)
    bot.run()
```

## 🚀 快速开始（中文优化版本）

### 方法1：使用提供的中文优化脚本

```bash
# 1. 启动 Ollama
ollama serve

# 2. 下载中文模型（在另一个终端）
ollama pull qwen2.5:14b
ollama pull bge-m3:latest

# 3. 运行中文对话系统
python chinese_local_deployment.py
```

### 方法2：逐步配置

1. **启动必要服务**：
   ```bash
   # 启动 Ollama
   ollama serve
   
   # 如果使用 Qdrant，启动 Qdrant
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **测试中文配置**：
   ```bash
   python chinese_config.py
   ```

3. **运行完整应用**：
   ```bash
   python local_chat_app.py
   ```

## 性能优化建议

### 1. 中文模型选择（重要！）
- **中文 LLM 推荐**:
  - 🥇 **最佳**: `qwen2.5:14b` - 阿里通义千问，中文理解和生成最佳
  - 🥈 **备选**: `yi:34b` - 零一万物，中文语义理解好
  - 🥉 **经济**: `qwen2.5:7b` - 较快，中文支持仍然很好
  - **高端**: `qwen2.5:32b` - 最强中文能力，需要更多资源
  
- **中文嵌入模型推荐**:
  - 🥇 **最佳**: `bge-m3:latest` - BAAI 出品，专门优化中文语义
  - 🥈 **备选**: `nomic-embed-text:latest` - 多语言支持，包含中文
  - **说明**: 中文嵌入模型对语义搜索质量影响巨大！

### 2. 向量数据库选择
- **FAISS**: 最快，适合中小规模数据（<100万条）
- **Chroma**: 功能丰富，支持元数据过滤
- **Qdrant**: 生产级，支持大规模数据和分布式部署

### 3. 硬件要求
- **最低配置**: 8GB RAM, 4核 CPU
- **推荐配置**: 16GB RAM, 8核 CPU, NVIDIA GPU（可选）
- **存储空间**: 模型约需 10-50GB（取决于选择的模型）

## 故障排查

1. **Ollama 连接失败**：
   - 检查 Ollama 是否运行: `curl http://localhost:11434/api/tags`
   - 确认模型已下载: `ollama list`

2. **内存不足**：
   - 使用更小的模型: `ollama pull llama3.1:7b`
   - 减少 `max_tokens` 参数

3. **向量维度不匹配**：
   - 确认 `embedding_model_dims` 与实际嵌入模型输出维度一致
   - nomic-embed-text: 768
   - snowflake-arctic-embed: 1024

## 总结

通过以上配置，你可以完全在本地运行 mem0，无需依赖任何外部 API。主要组件包括：
- **Ollama**: 提供本地 LLM 和嵌入模型
- **向量数据库**: FAISS/Chroma/Qdrant 存储向量
- **mem0**: 管理记忆和对话历史

这种部署方式特别适合：
- 数据安全性要求高的场景
- 无网络或内网环境
- 需要完全控制模型和数据的应用

## 🌟 中文使用专门建议

### 语义搜索效果优化
1. **使用专门的中文嵌入模型**：`bge-m3` 比通用模型在中文语义理解上有明显优势
2. **设置余弦相似度**：`distance_strategy: "cosine"` 对中文文本更准确
3. **合适的向量维度**：中文嵌入模型通常需要更高维度（1024维）来捕捉语义

### 中文分词和处理
- 中文没有天然的词边界，BGE-M3 模型已经内置了优秀的中文分词能力
- 无需额外的分词预处理，直接使用完整句子效果更好

### 存储建议
- 中文记忆通常比英文记忆更长，建议增加 `max_tokens` 到 3000+
- 使用更大的搜索限制（`limit=5-10`）来获得更全面的相关记忆

### 性能调优
- 中文模型通常需要更多计算资源，建议至少 16GB RAM
- 如果硬件有限，推荐使用 `qwen2.5:7b` + `bge-m3`
- GPU 加速对中文模型效果更明显，建议使用 `faiss-gpu`