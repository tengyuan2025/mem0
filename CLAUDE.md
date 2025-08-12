# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

Mem0 是一个为 AI 助手和智能体提供的智能记忆层，支持个性化 AI 交互。该项目提供开源自托管功能和托管云平台。它维护用户偏好，适应个体需求，并从交互中持续学习。

## 开发命令

### 环境设置
```bash
# 安装开发所需的所有依赖
make install_all

# 安装基础依赖
make install

# 使用 hatch 安装（推荐开发使用）
hatch env create
```

### 代码质量和测试
```bash
# 使用 ruff 格式化代码
make format
# 或者: hatch run format

# 使用 isort 排序导入  
make sort

# 使用 ruff 运行代码检查
make lint
# 或者: hatch run lint

# 自动修复代码检查问题
hatch run lint-fix

# 运行测试
make test
# 或者: hatch run test

# 针对特定 Python 版本运行测试
make test-py-3.9
make test-py-3.10  
make test-py-3.11
```

### 构建和发布
```bash
# 构建包
make build

# 清理构建产物
make clean

# 发布到 PyPI（仅维护者）
make publish
```

### 文档
```bash
# 启动文档开发服务器
make docs
```

## 架构概览

### 核心组件

1. **记忆系统 (`mem0/memory/`)**：核心记忆管理系统
   - `main.py`：主要的 Memory 和 AsyncMemory 类，提供 CRUD 操作
   - `base.py`：基础类和接口
   - `storage.py`：基于 SQLite 的历史记录管理
   - `utils.py`：消息解析和处理的实用函数

2. **客户端 (`mem0/client/`)**：Mem0 平台的 API 客户端
   - `main.py`：用于 API 交互的 MemoryClient 和 AsyncMemoryClient
   - `project.py`：项目管理功能

3. **向量存储 (`mem0/vector_stores/`)**：多种向量数据库集成
   - 支持：Chroma、Pinecone、Qdrant、Weaviate、FAISS、Azure AI Search 等
   - 每个提供者都有遵循基础接口的专用实现

4. **嵌入模型 (`mem0/embeddings/`)**：文本嵌入提供者
   - 支持：OpenAI、Azure OpenAI、Hugging Face、Vertex AI、Ollama 等
   - 可配置的嵌入维度和模型

5. **大语言模型 (`mem0/llms/`)**：语言模型集成
   - 支持：OpenAI、Anthropic、Azure OpenAI、Groq、Ollama、vLLM 等
   - 支持结构化和非结构化输出

6. **图存储 (`mem0/graphs/`)**：知识图谱能力
   - Neptune 集成用于增强关系建模
   - 可选的基于图的记忆存储和检索

7. **配置 (`mem0/configs/`)**：集中式配置管理
   - 所有组件的特定提供者配置
   - 使用 Pydantic 模型进行验证

### 关键架构模式

- **工厂模式**：广泛用于创建 LLM、嵌入模型和向量存储实例
- **插件架构**：为不同服务（LLM、向量存储等）提供模块化提供者
- **异步/同步支持**：为同步和异步操作提供双重实现
- **配置驱动**：大量使用配置对象进行自定义
- **遥测集成**：内置事件捕获用于分析

## 记忆操作

### 会话作用域
记忆通过以下至少一个参数进行作用域限定：`user_id`、`agent_id` 或 `run_id`。这实现了：
- 多租户记忆隔离
- 用户特定的个性化  
- 智能体特定的上下文保留
- 运行特定的会话管理

### 记忆类型
- **标准记忆**：通用对话和事实记忆
- **程序记忆**：流程和工作流记忆（需要 `agent_id`）
- **图记忆**：使用知识图谱的关系感知记忆

### 事实提取和更新
系统使用 LLM 来：
1. 从对话中提取事实
2. 确定是否添加、更新或删除现有记忆
3. 维护记忆一致性并避免重复

## 配置系统

### 基于环境的配置
配置从多个源加载：
- 环境变量（例如，`MEM0_API_KEY`）
- 配置文件
- 使用配置对象直接实例化

### 提供者配置结构
每个提供者（LLM、嵌入模型、向量存储）遵循一致的模式：
```python
config = {
    "llm": {
        "provider": "openai",
        "config": {"model": "gpt-4o-mini", "temperature": 0.1}
    },
    "embedder": {
        "provider": "openai", 
        "config": {"model": "text-embedding-3-small"}
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {"collection_name": "memories"}
    }
}
```

## 测试策略

### 测试结构
- `tests/` 目录中的单元测试
- 特定提供者的测试模块
- 核心记忆操作的集成测试
- 外部依赖的模拟实现

### 运行测试
使用 pytest 进行测试执行。测试按组件组织：
- `tests/memory/`：核心记忆功能
- `tests/llms/`：LLM 提供者测试  
- `tests/embeddings/`：嵌入模型提供者测试
- `tests/vector_stores/`：向量存储测试

## API 版本控制

项目通过 API 版本控制维护向后兼容性：
- `api_version="v1.0"`：旧版格式（已弃用）
- `api_version="v1.1"`：当前推荐格式
- 弃用警告指导迁移到更新版本

## 依赖和扩展

### 核心依赖
- `qdrant-client`：默认向量存储
- `pydantic`：配置验证
- `openai`：默认 LLM 和嵌入模型
- `sqlalchemy`：历史记录数据库

### 可选依赖
- `graph`：用于基于图的记忆（Neo4j、Neptune）
- `vector_stores`：额外的向量存储提供者  
- `llms`：额外的 LLM 提供者
- `extras`：扩展功能（Elasticsearch 等）

## 开发技巧

### 添加新提供者
1. 在相应目录中创建实现（`llms/`、`embeddings/`、`vector_stores/`）
2. 在 `mem0/utils/factory.py` 中扩展工厂类
3. 在 `mem0/configs/` 中添加配置架构
4. 在相应的测试目录中添加测试
5. 更新文档

### 记忆系统扩展
- 扩展 `MemoryBase` 以实现自定义记忆实现
- 使用工厂模式进行提供者注册
- 尽可能保持异步/同步兼容性

### 配置最佳实践
- 使用 Pydantic 模型进行验证
- 支持环境变量覆盖
- 提供合理的默认值
- 清楚地记录配置选项