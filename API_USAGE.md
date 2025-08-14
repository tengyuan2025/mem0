# Mem0 API 使用指南

## 🚀 服务状态

当前Mem0本地开发环境已成功启动，包含以下服务：

- **API服务**: http://localhost:8000 ✅
- **API文档**: http://localhost:8000/docs ✅ (使用国内CDN镜像)
- **ReDoc文档**: http://localhost:8000/redoc ✅
- **Qdrant数据库**: http://localhost:6333 ✅
- **Redis缓存**: localhost:6379 ✅

## 📖 API 接口说明

### 1. 健康检查
```bash
GET http://localhost:8000/health
```

**响应示例:**
```json
{
  "status": "healthy",
  "services": {
    "qdrant": "connected",
    "api": "running"
  }
}
```

### 2. 创建记忆
```bash
POST http://localhost:8000/v1/memories/
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "我喜欢中文AI助手"},
    {"role": "assistant", "content": "很高兴为您服务！"}
  ],
  "user_id": "test_user_001",
  "agent_id": "assistant_01",  // 可选
  "run_id": "session_123"      // 可选
}
```

**响应示例:**
```json
{
  "message": "已记录记忆: 用户test_user_001提到: 我喜欢中文AI助手...",
  "status": "success"
}
```

### 3. 获取用户记忆
```bash
GET http://localhost:8000/v1/memories/?user_id=test_user_001&limit=10
```

**响应示例:**
```json
{
  "memories": [
    {
      "id": "mem_0",
      "content": "用户test_user_001的记忆 #0",
      "created_at": "2025-08-13T22:00:00Z"
    }
  ],
  "user_id": "test_user_001",
  "count": 1
}
```

### 4. 根据关键词搜索记忆
```bash
# POST方式 (推荐)
POST http://localhost:8000/v1/memories/search
Content-Type: application/json

{
  "query": "咖啡",
  "user_id": "test_user_001",
  "limit": 10,
  "agent_id": "assistant_01"  // 可选
}

# GET方式 (简单查询)
GET http://localhost:8000/v1/memories/search?user_id=test_user&query=编程&limit=5
```

**搜索响应示例:**
```json
{
  "results": [
    {
      "id": "mem_001",
      "content": "我喜欢喝咖啡，特别是意式浓缩",
      "score": 0.95,
      "relevance_score": 0.95,
      "created_at": "2025-08-13T10:00:00Z"
    }
  ],
  "query": "咖啡",
  "user_id": "test_user_001",
  "count": 1
}
```

### 5. 获取集合信息
```bash
GET http://localhost:8000/v1/collections
```

## 🛠️ 测试命令

### 创建记忆示例
```bash
# 基础记忆创建
curl -X POST http://localhost:8000/v1/memories/ \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [
      {"role": "user", "content": "我的名字是张三，我在北京工作"}
    ],
    "user_id": "user_zhangsan"
  }'

# 带智能体上下文的记忆
curl -X POST http://localhost:8000/v1/memories/ \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [
      {"role": "user", "content": "我喜欢喝咖啡"},
      {"role": "assistant", "content": "咖啡确实是很好的饮品！"}
    ],
    "user_id": "user_coffee_lover",
    "agent_id": "assistant_01"
  }'
```

### 获取记忆示例
```bash
# 获取指定用户的记忆
curl "http://localhost:8000/v1/memories/?user_id=user_zhangsan"

# 限制返回数量
curl "http://localhost:8000/v1/memories/?user_id=user_zhangsan&limit=5"
```

### 搜索记忆示例
```bash
# POST方式搜索
curl -X POST http://localhost:8000/v1/memories/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "咖啡",
    "user_id": "test_user_001",
    "limit": 5
  }'

# 多关键词搜索
curl -X POST http://localhost:8000/v1/memories/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "工作 软件开发",
    "user_id": "developer_user",
    "limit": 10
  }'

# GET方式搜索（中文需要URL编码）
curl "http://localhost:8000/v1/memories/search?user_id=test_user&query=Python&limit=3"
```

### 系统管理示例
```bash
# 查看系统统计信息
curl http://localhost:8000/v1/system/stats

# 清理所有测试数据
curl -X DELETE http://localhost:8000/v1/system/clear

# 删除指定用户的记忆
curl -X DELETE http://localhost:8000/v1/memories/user/demo_user
```

## 🚀 本地资源配置

为了提升访问速度，已将Swagger UI资源下载到本地：

- **CSS**: `/static/swagger-ui.css` (149KB) ✅
- **JS**: `/static/swagger-ui-bundle.js` (1.4MB) ✅  
- **图标**: `/static/favicon-32x32.png` (14B) ✅

**优势：**
- 🚀 **加载速度快**: 无需访问外部CDN，直接从本地加载
- 🔒 **离线可用**: 不依赖网络连接
- 🎯 **稳定可靠**: 避免CDN服务不稳定问题

### 资源管理

使用内置的资源管理工具：

```bash
# 查看资源状态
./manage-static-resources.sh status

# 更新到最新版本  
./manage-static-resources.sh update

# 重新下载资源
./manage-static-resources.sh download

# 查看资源大小
./manage-static-resources.sh size

# 清理本地资源
./manage-static-resources.sh clean
```

### 备用CDN源 (如需回退)

如果需要使用CDN而非本地资源：

1. **BootCDN**: `https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/`
2. **Staticfile CDN**: `https://cdn.staticfile.org/swagger-ui/5.17.14/`
3. **UNPKG 中国镜像**: `https://unpkg.com/swagger-ui-dist@5.17.14/`

## 🎯 真实数据功能

现在API使用**真实数据存储**，不再是模拟数据：

### ✅ 已实现功能
- **真实记忆创建**: 保存用户输入的实际内容和对话历史
- **动态数据检索**: 获取真实创建的记忆，按时间排序
- **关键词搜索**: 基于实际内容的相关性搜索和排序
- **用户隔离**: 不同用户的记忆完全独立存储
- **统计信息**: 实时显示用户数量和记忆总数

### 🔧 管理接口
```bash
# 查看系统统计
GET http://localhost:8000/v1/system/stats

# 清理所有数据 (测试用)
DELETE http://localhost:8000/v1/system/clear

# 删除指定用户记忆
DELETE http://localhost:8000/v1/memories/user/{user_id}
```

### 📝 当前限制

虽然数据是真实的，但仍有一些简化：

1. **内存存储**: 数据存储在内存中，重启后会丢失
2. **简化搜索**: 基于关键词匹配，未使用向量相似度
3. **无AI语义分析**: 未集成LLM进行智能记忆提取
4. **无嵌入模型**: 暂未使用BGE-Large-ZH进行语义搜索

## 🎯 下一步

要启用完整功能，需要：

1. 安装完整的AI依赖包 (`sentence-transformers`, `torch`等)
2. 集成豆包LLM和BGE中文嵌入模型
3. 实现真实的记忆存储和检索逻辑
4. 添加向量相似度搜索功能

## 📱 访问方式

- **浏览器访问**: http://localhost:8000/docs
- **API测试工具**: Postman, Insomnia, 或 curl命令
- **Web界面**: 完整的Swagger UI文档界面