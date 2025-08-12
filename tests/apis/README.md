# Mem0 Memory API 文档

这个目录包含了 Mem0 Memory API 的完整实现和测试套件。

## 概述

Mem0 Memory API 是一个基于 FastAPI 构建的 RESTful API，用于管理 AI 记忆操作。它提供了完整的 CRUD 操作来处理个性化 AI 记忆。

## API 功能

### 核心功能
- **创建记忆**: 从消息中提取并存储记忆
- **检索记忆**: 通过 ID 获取特定记忆
- **搜索记忆**: 基于语义相似性搜索记忆
- **更新记忆**: 修改现有记忆内容
- **删除记忆**: 删除单个或批量记忆
- **记忆历史**: 查看记忆变更历史
- **重置系统**: 清空所有记忆（管理员功能）

### 特性
- **异步处理**: 所有操作都支持异步处理
- **会话隔离**: 通过 `user_id`、`agent_id`、`run_id` 实现多租户隔离
- **语义搜索**: 基于向量相似性的智能搜索
- **自动推理**: 使用 LLM 进行事实提取和记忆管理
- **历史追踪**: 完整的记忆变更历史记录
- **错误处理**: 完善的错误处理和验证机制

## API 端点

### 基础端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 根端点，返回 API 状态 |
| GET | `/health` | 健康检查端点 |

### 记忆操作端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/memories` | 创建新记忆 |
| GET | `/memories/{memory_id}` | 获取特定记忆 |
| POST | `/memories/search` | 搜索记忆 |
| POST | `/memories/all` | 获取所有记忆 |
| PUT | `/memories/{memory_id}` | 更新记忆 |
| DELETE | `/memories/{memory_id}` | 删除特定记忆 |
| DELETE | `/memories` | 批量删除记忆 |
| GET | `/memories/{memory_id}/history` | 获取记忆历史 |

### 管理员端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/memories/reset` | 重置所有记忆 |

## 请求/响应模型

### 创建记忆请求
```json
{
  "messages": "I love Italian food",
  "user_id": "user-123",
  "agent_id": "agent-456",
  "run_id": "run-789",
  "metadata": {"source": "chat"},
  "infer": true,
  "memory_type": null,
  "prompt": null
}
```

### 搜索记忆请求
```json
{
  "query": "food preferences",
  "user_id": "user-123",
  "limit": 10,
  "filters": {"category": "food"},
  "threshold": 0.7
}
```

### 记忆响应
```json
{
  "id": "memory-123",
  "memory": "User loves Italian food",
  "hash": "abc123",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null,
  "user_id": "user-123",
  "agent_id": null,
  "run_id": null,
  "actor_id": null,
  "role": "user",
  "metadata": {"source": "chat"},
  "score": 0.95
}
```

## 启动 API 服务器

### 🐳 Docker 一键部署（推荐）

> **注意**: Docker 部署文件已移至项目根目录，请先切换到根目录进行部署。

#### 环境准备
```bash
# 1. 切换到项目根目录
cd ../../

# 2. 复制环境变量模板
cp .env.example .env

# 3. 编辑 .env 文件，设置必要的 API 密钥
# 至少需要设置 OPENAI_API_KEY
nano .env
```

#### 开发环境部署
```bash
# 启动开发环境（包含 API + Qdrant + Redis）
./deploy.sh --env dev

# 后台运行
./deploy.sh --env dev --detach

# 查看日志
./deploy.sh --logs
```

#### 生产环境部署
```bash
# 生产环境部署（优化配置）
./deploy.sh --env prod --detach

# 包含监控服务的完整部署
./deploy.sh --env prod --monitoring --detach

# 强制重新构建并部署
./deploy.sh --env prod --build --detach
```

#### 云服务器一键部署
```bash
# 通用云服务器部署（需要 root 权限）
sudo OPENAI_API_KEY='your-key' ./deploy_cloud.sh \
  --domain api.example.com \
  --email admin@example.com \
  --monitoring

# 阿里云 ECS 优化部署
sudo OPENAI_API_KEY='your-key' ./deploy_aliyun.sh \
  --domain api.example.com \
  --email admin@example.com \
  --ssl \
  --monitoring \
  --aliyun-mirror
```

#### 部署指南
- 📚 [Docker 快速开始指南](../../DOCKER_QUICKSTART.md)
- ☁️ [阿里云部署指南](../../ALIYUN_DEPLOY.md)

#### Docker 管理命令
```bash
# 查看服务状态 (在根目录下执行)
docker-compose ps

# 停止所有服务
./deploy.sh --stop

# 清理并重新部署
./deploy.sh --clean --env dev

# 查看特定服务日志
docker-compose logs mem0-api
```

### 📦 传统本地开发方式

#### 手动安装依赖
```bash
# 安装 FastAPI 相关依赖
pip install fastapi uvicorn python-multipart

# 安装 mem0 核心依赖
pip install mem0ai
```

#### 运行服务器
```bash
# 切换到项目根目录
cd ../../

# 直接运行 API 服务器
python -m mem0.api.main

# 或使用 uvicorn 开发模式
uvicorn mem0.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问 API 文档
启动服务器后，可以通过以下 URL 访问自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 配置

API 使用 Mem0 的标准配置系统。可以通过以下方式配置：

### 环境变量
```bash
export MEM0_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"
```

### 配置文件
创建配置文件并通过 `MemoryConfig` 传递给 Memory 实例。

## 测试

### 运行测试
```bash
# 运行所有 API 测试
pytest tests/apis/

# 运行特定测试文件
pytest tests/apis/test_memory_api.py

# 运行集成测试（需要配置 API 密钥）
pytest tests/apis/test_integration.py -m integration

# 运行测试并显示覆盖率
pytest tests/apis/ --cov=mem0.api
```

### 测试结构
- `conftest.py`: 测试配置和夹具
- `test_memory_api.py`: 单元测试（使用 Mock）
- `test_integration.py`: 集成测试（使用真实实例）

## 使用示例

### Python 客户端示例

```python
import requests

# 创建记忆
response = requests.post("http://localhost:8000/memories", json={
    "messages": "I prefer tea over coffee",
    "user_id": "user-123"
})
print(response.json())

# 搜索记忆
response = requests.post("http://localhost:8000/memories/search", json={
    "query": "beverage preference",
    "user_id": "user-123",
    "limit": 5
})
print(response.json())
```

### curl 示例

```bash
# 创建记忆
curl -X POST "http://localhost:8000/memories" \
  -H "Content-Type: application/json" \
  -d '{"messages": "I love pizza", "user_id": "user-123"}'

# 搜索记忆
curl -X POST "http://localhost:8000/memories/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "food preferences", "user_id": "user-123"}'
```

## 错误处理

API 返回标准的 HTTP 状态码：

- **200**: 成功
- **400**: 客户端错误（验证失败等）
- **404**: 资源未找到
- **422**: 请求验证错误
- **500**: 服务器内部错误

错误响应格式：
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## 安全考虑

- API 不包含内置身份验证机制，建议在生产环境中添加适当的身份验证
- 使用 HTTPS 保护数据传输
- 限制 CORS 来源以提高安全性
- 考虑实现速率限制

## 性能优化

- 所有操作都使用异步处理
- 支持批量操作以减少 API 调用次数
- 向量搜索已优化性能
- 建议为生产环境配置适当的向量数据库

## 监控和日志

API 包含：
- 结构化日志记录
- 错误跟踪
- 性能监控点
- 健康检查端点

## 开发指南

### 添加新端点
1. 在 `models.py` 中定义请求/响应模型
2. 在 `main.py` 中添加端点处理函数
3. 在 `test_memory_api.py` 中添加测试用例
4. 更新此文档

### 扩展功能
- 支持批量操作
- 添加身份验证中间件
- 实现缓存层
- 添加监控和指标收集

## 故障排除

常见问题：

1. **Memory 实例初始化失败**: 检查 API 密钥和配置
2. **向量搜索慢**: 检查向量数据库配置和索引
3. **内存使用高**: 考虑优化批量操作和连接池
4. **测试失败**: 确保所有依赖已安装且配置正确


## 贡献

欢迎贡献代码！请确保：
1. 添加适当的测试覆盖
2. 遵循代码风格指南
3. 更新文档
4. 运行所有测试确保无回归