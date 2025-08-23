# DeepSeek + Qdrant 记忆系统 API 文档

## 🌐 服务地址

- **Web 界面**: http://localhost:9000
- **API 基础地址**: http://localhost:9000/api
- **Swagger 文档**: http://localhost:9000/docs
- **ReDoc 文档**: http://localhost:9000/redoc

## 📋 接口列表

### 1. 添加记忆 - POST /api/memories

**功能**: 向系统中添加新的记忆内容

**请求方式**: `POST`
**请求地址**: `http://localhost:9000/api/memories`

#### 请求参数 (JSON Body)
```json
{
  "text": "要记住的内容",
  "user_id": "用户标识",
  "metadata": {
    "type": "分类标签",
    "source": "来源",
    "timestamp": "时间戳"
  }
}
```

#### 参数说明
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| text | string | 是 | 要添加的记忆内容 | "我喜欢使用Python进行AI开发" |
| user_id | string | 否 | 用户标识，默认 "default_user" | "zhang_san" |
| metadata | object | 否 | 记忆的元数据 | {"type": "技能", "source": "对话"} |

#### 响应示例
```json
{
  "success": true,
  "message": "记忆添加成功",
  "result": {
    "id": "memory_12345",
    "message": "Memory added successfully"
  }
}
```

#### cURL 示例
```bash
curl -X POST "http://localhost:9000/api/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我是一名AI工程师，专注于自然语言处理",
    "user_id": "demo_user",
    "metadata": {"type": "职业", "category": "个人信息"}
  }'
```

---

### 2. 搜索记忆 - POST /api/search

**功能**: 根据关键词搜索相关的记忆内容

**请求方式**: `POST`
**请求地址**: `http://localhost:9000/api/search`

#### 请求参数 (JSON Body)
```json
{
  "query": "搜索关键词",
  "user_id": "用户标识",
  "limit": 5
}
```

#### 参数说明
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| query | string | 是 | 搜索关键词 | "Python开发" |
| user_id | string | 否 | 用户标识，默认 "default_user" | "zhang_san" |
| limit | integer | 否 | 返回结果数量，默认 5 | 10 |

#### 响应示例
```json
{
  "success": true,
  "memories": [
    {
      "id": "memory_12345",
      "memory": "我是一名AI工程师，专注于自然语言处理",
      "score": 0.9234,
      "metadata": {
        "type": "职业",
        "category": "个人信息"
      }
    }
  ]
}
```

#### cURL 示例
```bash
curl -X POST "http://localhost:9000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python开发",
    "user_id": "demo_user",
    "limit": 3
  }'
```

---

### 3. 获取所有记忆 - GET /api/memories/{user_id}

**功能**: 获取指定用户的所有记忆

**请求方式**: `GET`
**请求地址**: `http://localhost:9000/api/memories/{user_id}`

#### 路径参数
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| user_id | string | 是 | 用户标识 | "demo_user" |

#### 响应示例
```json
{
  "success": true,
  "memories": [
    {
      "id": "memory_12345",
      "memory": "我是一名AI工程师，专注于自然语言处理",
      "metadata": {
        "type": "职业",
        "category": "个人信息"
      }
    },
    {
      "id": "memory_67890",
      "memory": "我喜欢使用Python进行AI开发",
      "metadata": {
        "type": "技能",
        "source": "对话"
      }
    }
  ]
}
```

#### cURL 示例
```bash
curl -X GET "http://localhost:9000/api/memories/demo_user"
```

---

### 4. 删除记忆 - DELETE /api/memories/{memory_id}

**功能**: 删除指定的记忆

**请求方式**: `DELETE`
**请求地址**: `http://localhost:9000/api/memories/{memory_id}`

#### 路径参数
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| memory_id | string | 是 | 记忆ID | "memory_12345" |

#### 响应示例
```json
{
  "success": true,
  "message": "记忆删除成功"
}
```

#### cURL 示例
```bash
curl -X DELETE "http://localhost:9000/api/memories/memory_12345"
```

---

### 5. 系统状态 - GET /api/status

**功能**: 获取系统运行状态

**请求方式**: `GET`
**请求地址**: `http://localhost:9000/api/status`

#### 响应示例
```json
{
  "qdrant_status": true,
  "memory_system": true,
  "collection_name": "deepseek_web_memories",
  "embedder_model": "BAAI/bge-large-zh-v1.5",
  "llm_model": "deepseek-chat"
}
```

#### cURL 示例
```bash
curl -X GET "http://localhost:9000/api/status"
```

---

## 🔧 错误码说明

| HTTP状态码 | 说明 | 示例响应 |
|------------|------|----------|
| 200 | 请求成功 | `{"success": true, ...}` |
| 400 | 请求参数错误 | `{"detail": "请求参数不正确"}` |
| 500 | 服务器内部错误 | `{"detail": "Qdrant 连接失败"}` |

## 📊 使用示例

### Python 客户端示例

```python
import requests
import json

# API 基础地址
BASE_URL = "http://localhost:9000/api"

class MemoryAPI:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def add_memory(self, text, user_id="default_user", metadata=None):
        """添加记忆"""
        url = f"{self.base_url}/memories"
        data = {
            "text": text,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def search_memories(self, query, user_id="default_user", limit=5):
        """搜索记忆"""
        url = f"{self.base_url}/search"
        data = {
            "query": query,
            "user_id": user_id,
            "limit": limit
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def get_all_memories(self, user_id):
        """获取所有记忆"""
        url = f"{self.base_url}/memories/{user_id}"
        response = requests.get(url)
        return response.json()
    
    def delete_memory(self, memory_id):
        """删除记忆"""
        url = f"{self.base_url}/memories/{memory_id}"
        response = requests.delete(url)
        return response.json()
    
    def get_status(self):
        """获取系统状态"""
        url = f"{self.base_url}/status"
        response = requests.get(url)
        return response.json()

# 使用示例
if __name__ == "__main__":
    api = MemoryAPI()
    
    # 1. 添加记忆
    result = api.add_memory(
        text="我喜欢在周末阅读AI相关的技术博客",
        user_id="test_user",
        metadata={"type": "爱好", "category": "学习"}
    )
    print("添加记忆:", result)
    
    # 2. 搜索记忆
    results = api.search_memories("AI技术", user_id="test_user", limit=3)
    print("搜索结果:", results)
    
    # 3. 获取所有记忆
    all_memories = api.get_all_memories("test_user")
    print("所有记忆:", all_memories)
    
    # 4. 获取系统状态
    status = api.get_status()
    print("系统状态:", status)
```

### JavaScript 客户端示例

```javascript
class MemoryAPI {
    constructor(baseUrl = 'http://localhost:9000/api') {
        this.baseUrl = baseUrl;
    }
    
    async addMemory(text, userId = 'default_user', metadata = {}) {
        const response = await fetch(`${this.baseUrl}/memories`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                user_id: userId,
                metadata: metadata
            })
        });
        return await response.json();
    }
    
    async searchMemories(query, userId = 'default_user', limit = 5) {
        const response = await fetch(`${this.baseUrl}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                user_id: userId,
                limit: limit
            })
        });
        return await response.json();
    }
    
    async getAllMemories(userId) {
        const response = await fetch(`${this.baseUrl}/memories/${userId}`);
        return await response.json();
    }
    
    async deleteMemory(memoryId) {
        const response = await fetch(`${this.baseUrl}/memories/${memoryId}`, {
            method: 'DELETE'
        });
        return await response.json();
    }
    
    async getStatus() {
        const response = await fetch(`${this.baseUrl}/status`);
        return await response.json();
    }
}

// 使用示例
const api = new MemoryAPI();

// 添加记忆
api.addMemory('我正在学习大语言模型的应用开发', 'js_user')
    .then(result => console.log('添加记忆:', result));

// 搜索记忆
api.searchMemories('大语言模型', 'js_user', 3)
    .then(results => console.log('搜索结果:', results));
```

## 🧪 接口测试工具

### 1. Swagger UI (推荐)
- **地址**: http://localhost:9000/docs
- **特点**: 交互式文档，可直接测试所有接口
- **功能**: 参数填写、实时请求、响应查看

### 2. ReDoc
- **地址**: http://localhost:9000/redoc  
- **特点**: 美观的静态文档
- **功能**: 接口规范展示、代码示例

### 3. Postman 集合

可以将以下 JSON 导入 Postman：

```json
{
  "info": {
    "name": "DeepSeek Memory API",
    "description": "DeepSeek + Qdrant 记忆系统 API 集合"
  },
  "item": [
    {
      "name": "添加记忆",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"text\": \"测试记忆内容\",\n  \"user_id\": \"test_user\",\n  \"metadata\": {\"type\": \"测试\"}\n}"
        },
        "url": {
          "raw": "http://localhost:9000/api/memories",
          "protocol": "http",
          "host": ["localhost"],
          "port": "9000",
          "path": ["api", "memories"]
        }
      }
    },
    {
      "name": "搜索记忆",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"测试\",\n  \"user_id\": \"test_user\",\n  \"limit\": 5\n}"
        },
        "url": {
          "raw": "http://localhost:9000/api/search",
          "protocol": "http",
          "host": ["localhost"],
          "port": "9000",
          "path": ["api", "search"]
        }
      }
    }
  ]
}
```

## 🔐 安全说明

- 当前版本为开发测试版，无身份验证
- 生产环境需要添加 API Key 或 JWT 认证
- 建议在防火墙后运行，或添加访问限制

## 📈 性能建议

- 搜索限制建议不超过 50 条
- 大量数据操作建议使用批量接口
- 定期清理无用的记忆数据
- 监控 Qdrant 内存使用情况