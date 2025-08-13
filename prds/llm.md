# Mem0 LLM 需求与实现

## 需求：LLM支持豆包和deepseek，默认使用豆包
**需求描述**: 添加豆包(字节跳动)和DeepSeek LLM支持，并设置豆包为默认LLM提供商，优化中文场景下的AI对话体验。

### ✅ 已实现的功能

#### 豆包(Doubao) LLM 支持
- **实现文件**: `mem0/llms/doubao.py`
- **配置文件**: `mem0/configs/llms/doubao.py` 
- **支持特性**:
  - 基于OpenAI兼容接口的豆包API调用
  - 支持工具调用(Function Calling)
  - 默认模型: `doubao-pro-32k`
  - 环境变量支持: `DOUBAO_API_KEY`, `ARK_API_KEY`
  - 自定义API端点: `DOUBAO_API_BASE`, `ARK_API_BASE`
  - 端点ID支持: `DOUBAO_ENDPOINT_ID`

#### DeepSeek LLM 支持 
- **实现文件**: `mem0/llms/deepseek.py`
- **配置文件**: `mem0/configs/llms/deepseek.py`
- **支持特性**:
  - 基于OpenAI兼容接口的DeepSeek API调用
  - 支持工具调用(Function Calling)
  - 默认模型: `deepseek-chat`
  - 环境变量支持: `DEEPSEEK_API_KEY`
  - 自定义API端点: `DEEPSEEK_API_BASE`

#### 默认配置更新
- **配置文件**: `mem0/llms/configs.py`
- **默认LLM**: 已设置豆包(doubao)为默认LLM提供商
- **工厂类**: `mem0/utils/factory.py` - 已添加豆包支持

#### 配置示例

**使用豆包LLM**:
```python
from mem0 import Memory

config = {
    "llm": {
        "provider": "doubao",
        "config": {
            "model": "doubao-pro-32k",
            "temperature": 0.1,
            "api_key": "your_doubao_api_key",
            "doubao_base_url": "https://ark.cn-beijing.volces.com/api/v3"
        }
    }
}

memory = Memory(config=config)
```

**使用DeepSeek LLM**:
```python
from mem0 import Memory

config = {
    "llm": {
        "provider": "deepseek", 
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.1,
            "api_key": "your_deepseek_api_key"
        }
    }
}

memory = Memory(config=config)
```

---