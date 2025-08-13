# Mem0 本地开发环境指南
# Local Development Guide for Mem0 with Chinese Optimization

本指南介绍如何在本地使用Docker运行Mem0项目，并使用记忆相关的API接口。

## 🚀 快速开始

### 1. 环境要求

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **系统内存**: >= 4GB (推荐8GB)
- **存储空间**: >= 5GB (模型文件需要空间)

### 2. 一键启动

```bash
# 克隆项目 (如果还没有)
git clone https://github.com/mem0ai/mem0.git
cd mem0

# 运行启动脚本
./start-dev.sh
```

启动脚本会：
- ✅ 检查Docker环境
- ✅ 创建.env配置文件模板
- ✅ 构建开发环境镜像
- ✅ 启动所有服务
- ✅ 验证服务健康状态

### 3. 配置API密钥

编辑 `.env` 文件，添加你的API密钥：

```bash
# 推荐：使用豆包API (中文优化)
DOUBAO_API_KEY=your_doubao_api_key_here

# 备选：使用OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
```

## 🏗️ 服务架构

启动后的服务栈包括：

| 服务 | 端口 | 说明 |
|------|------|------|
| **mem0-api** | 8000 | 主API服务，支持热重载 |
| **qdrant** | 6333 | 向量数据库，存储嵌入向量 |
| **redis** | 6379 | 缓存服务 (可选) |

### 服务地址

- 🌐 **API服务**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs  
- 📊 **Qdrant控制台**: http://localhost:6333/dashboard
- 🔍 **健康检查**: http://localhost:8000/health

## 🛠️ 开发配置详解

### 默认配置 (中文优化)

```yaml
LLM配置:
  提供商: doubao (豆包)
  模型: doubao-pro-32k
  用途: 中文对话和记忆生成

嵌入模型:
  提供商: huggingface (本地运行)
  模型: BAAI/bge-large-zh-v1.5
  用途: 中文文本向量化

向量数据库:
  提供商: qdrant
  集合: mem0_memories
  维度: 1024 (BGE-Large-ZH)
```

### 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEM0_LLM_PROVIDER` | doubao | LLM提供商 |
| `MEM0_LLM_MODEL` | doubao-pro-32k | LLM模型 |
| `MEM0_EMBEDDER_PROVIDER` | huggingface | 嵌入提供商 |
| `MEM0_EMBEDDER_MODEL` | BAAI/bge-large-zh-v1.5 | 嵌入模型 |
| `QDRANT_HOST` | qdrant | Qdrant主机 |
| `QDRANT_PORT` | 6333 | Qdrant端口 |

## 📡 API 接口使用

### 核心记忆操作API

#### 1. 添加记忆
```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "我是软件工程师，专注Python开发"}],
    "user_id": "user_123"
  }'
```

#### 2. 搜索记忆
```bash
curl -X POST http://localhost:8000/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我的职业是什么",
    "user_id": "user_123",
    "limit": 5
  }'
```

#### 3. 获取所有记忆
```bash
curl -X POST http://localhost:8000/memories/all \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```

#### 4. 更新记忆
```bash
curl -X PUT http://localhost:8000/memories/{memory_id} \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我是高级软件工程师，专注Python和Go开发"
  }'
```

#### 5. 删除记忆
```bash
curl -X DELETE http://localhost:8000/memories/{memory_id}
```

### 🧪 自动化测试

运行完整的API功能测试：

```bash
./test-api.sh
```

测试脚本会验证：
- ✅ 服务健康状态
- ✅ 中文记忆添加
- ✅ 中文语义搜索
- ✅ 记忆CRUD操作
- ✅ 向量化和检索功能

## 🐳 Docker命令参考

### 服务管理

```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f mem0-api

# 停止服务
docker-compose -f docker-compose.dev.yml down

# 重启服务
docker-compose -f docker-compose.dev.yml restart mem0-api

# 进入容器
docker-compose -f docker-compose.dev.yml exec mem0-api bash
```

### 数据管理

```bash
# 备份数据
docker-compose -f docker-compose.dev.yml down
docker run --rm -v mem0_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz /data

# 恢复数据
docker-compose -f docker-compose.dev.yml down
docker run --rm -v mem0_qdrant_data:/data -v $(pwd):/backup alpine tar xzf /backup/qdrant_backup.tar.gz -C /
docker-compose -f docker-compose.dev.yml up -d
```

### 清理环境

```bash
# 停止并删除所有容器和网络
docker-compose -f docker-compose.dev.yml down

# 清理未使用的数据卷
docker-compose -f docker-compose.dev.yml down -v

# 清理镜像
docker rmi mem0-mem0-api-dev
```

## 📊 监控和调试

### 查看日志

```bash
# 实时查看API日志
docker-compose -f docker-compose.dev.yml logs -f mem0-api

# 查看Qdrant日志
docker-compose -f docker-compose.dev.yml logs -f qdrant

# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看容器详细信息
docker-compose -f docker-compose.dev.yml top
```

### 调试技巧

1. **进入API容器**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec mem0-api bash
   ```

2. **手动运行Python代码**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec mem0-api python
   ```

3. **查看模型下载进度**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec mem0-api ls -la /root/.cache/huggingface
   ```

4. **测试中文嵌入**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec mem0-api python -c "
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
   result = model.encode('测试中文句子')
   print(f'嵌入维度: {len(result)}')
   "
   ```

## 🚨 常见问题

### 模型下载问题

**问题**: 首次启动时嵌入模型下载缓慢或失败

**解决方案**:
```bash
# 手动下载模型
docker-compose -f docker-compose.dev.yml exec mem0-api python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
print('模型下载完成')
"
```

### 内存不足

**问题**: 容器内存不足，模型加载失败

**解决方案**:
1. 增加Docker内存限制到8GB+
2. 使用轻量模型：
   ```bash
   export MEM0_EMBEDDER_MODEL=moka-ai/m3e-base
   ```

### API密钥配置

**问题**: API密钥未正确设置

**解决方案**:
1. 检查 `.env` 文件是否存在并正确配置
2. 确认环境变量已加载：
   ```bash
   docker-compose -f docker-compose.dev.yml exec mem0-api env | grep API_KEY
   ```

### 端口冲突

**问题**: 端口8000或6333已被占用

**解决方案**:
修改 `docker-compose.dev.yml` 中的端口映射：
```yaml
ports:
  - "8001:8000"  # API服务改为8001
  - "6334:6333"  # Qdrant改为6334
```

### 向量搜索不准确

**问题**: 中文搜索结果不相关

**解决方案**:
1. 确认使用了中文优化模型
2. 检查嵌入维度配置是否正确
3. 增加更多样本数据进行测试

## 🎯 开发最佳实践

### 1. 代码热重载

开发环境支持代码热重载：
- 修改 `mem0/` 目录下的代码会自动重启API服务
- 无需重新构建Docker镜像

### 2. 数据持久化

- 使用Docker volumes保证数据持久性
- 定期备份重要数据
- 开发环境数据存储在 `./data/` 目录

### 3. 测试驱动开发

- 使用 `./test-api.sh` 验证功能
- 编写自定义测试用例
- 使用Pytest进行单元测试

### 4. 配置管理

- 使用 `.env` 文件管理配置
- 区分开发和生产环境配置
- 敏感信息不要提交到Git

## 🚀 部署到生产环境

开发完成后，可以使用以下方式部署：

1. **Docker部署**: 使用主Dockerfile构建生产镜像
2. **Kubernetes**: 参考K8s配置文件
3. **云服务器**: 参考 `CHINESE_DEPLOYMENT_GUIDE.md`

---

## 📞 获取帮助

- **API文档**: http://localhost:8000/docs
- **GitHub Issues**: 项目GitHub页面
- **日志分析**: 查看Docker容器日志
- **配置参考**: 查看 `.env.example`

祝你开发愉快！🎉