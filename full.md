# Mem0 项目根目录文件和目录完整说明

此文档详细记录了 Mem0 项目根目录下每个文件和目录的用途。

## 📁 目录结构概览

Mem0 是一个智能记忆层项目，为 AI 智能体提供个性化记忆能力。项目采用模块化架构，支持多种向量数据库、大语言模型和嵌入模型。

---

## 📋 文档文件

### 项目文档
- **`README.md`** - 项目主要说明文档，包含介绍、安装、快速开始等
- **`CLAUDE.md`** - Claude Code 工作指导文档，包含开发命令、架构概览等
- **`CONTRIBUTING.md`** - 贡献指南，如何为项目贡献代码
- **`LICENSE`** - 项目开源许可证

### 部署和运维文档
- **`ALIYUN_DEPLOY.md`** - 阿里云部署指南
- **`API_USAGE.md`** - API 使用说明文档
- **`CHINESE_DEPLOYMENT_GUIDE.md`** - 中文部署指南
- **`DEPLOYMENT_ARCHITECTURE.md`** - 部署架构说明
- **`DOCKER_DEPLOYMENT.md`** - Docker 部署指南
- **`DOCKER_QUICKSTART.md`** - Docker 快速开始
- **`LOCAL_DEVELOPMENT_GUIDE.md`** - 本地开发指南
- **`LLM.md`** - 大语言模型相关文档

### 技术文档
- **`doc.md`** - 端口和接口文档，记录项目占用的端口和API接口
- **`full.md`** - 本文件，根目录完整说明

---

## 🐳 容器化和部署

### Docker 配置文件
- **`Dockerfile`** - 主要的 Docker 镜像构建文件
- **`Dockerfile.dev`** - 开发环境 Docker 文件
- **`Dockerfile.dev.fallback`** - 开发环境备用 Docker 文件
- **`Dockerfile.dev.fast`** - 快速开发环境 Docker 文件

### Docker Compose 配置
- **`docker-compose.yml`** - 主要的 Docker Compose 配置
- **`docker-compose.dev.yml`** - 开发环境 Docker Compose
- **`docker-compose.prod.yml`** - 生产环境 Docker Compose
- **`docker-compose.simple.yml`** - 简化版 Docker Compose

### 部署脚本
- **`deploy.sh`** - 通用部署脚本
- **`deploy_aliyun.sh`** - 阿里云部署脚本
- **`deploy_cloud.sh`** - 云端部署脚本

---

## 🔧 开发工具和脚本

### 构建工具
- **`Makefile`** - Make 构建配置文件
- **`pyproject.toml`** - Python 项目配置文件（Poetry/setuptools）
- **`poetry.lock`** - Poetry 依赖锁定文件
- **`requirements-chinese.txt`** - 中文环境依赖配置

### 开发脚本
- **`start-dev.sh`** - 启动开发环境脚本
- **`start-dev-fast.sh`** - 快速启动开发环境
- **`start-local.sh`** - 启动本地环境
- **`test-api.sh`** - API 测试脚本
- **`test-env.py`** - 环境测试脚本

### 运维工具
- **`check-ports.sh`** - 端口检查脚本，检查所有服务状态
- **`manage-static-resources.sh`** - 静态资源管理脚本
- **`docker-storage-info.sh`** - Docker 存储信息查看
- **`fix-docker-network.sh`** - Docker 网络修复脚本
- **`diagnose-and-fix.sh`** - 诊断和修复脚本

---

## 🚀 API 服务

### 主要服务文件
- **`simple-api.py`** - 简化版 API 服务器，FastAPI 实现
- **`example_client.py`** - 客户端示例代码
- **`docs-cdn-fallback.py`** - 文档 CDN 备用方案

### 日志文件
- **`api.log`** - API 服务运行日志

---

## 📦 核心代码模块

### 主要代码目录
- **`mem0/`** - 核心 Mem0 Python 库
  - `memory/` - 记忆管理核心模块
  - `llms/` - 大语言模型集成
  - `embeddings/` - 嵌入模型集成
  - `vector_stores/` - 向量数据库集成
  - `configs/` - 配置管理
  - `client/` - 客户端代码
  - `api/` - API 服务代码

### TypeScript/JavaScript 版本
- **`mem0-ts/`** - TypeScript 版本的 Mem0 客户端
- **`vercel-ai-sdk/`** - Vercel AI SDK 集成

---

## 🧪 测试

### 测试目录
- **`tests/`** - Python 测试套件
  - `memory/` - 记忆功能测试
  - `llms/` - LLM 测试
  - `embeddings/` - 嵌入模型测试
  - `vector_stores/` - 向量数据库测试
  - `apis/` - API 集成测试

### 评估工具
- **`evaluation/`** - 性能评估工具和脚本

---

## 📚 示例和演示

### 示例代码
- **`examples/`** - 各种使用示例
  - `graph-db-demo/` - 图数据库演示
  - `mem0-demo/` - Mem0 演示应用
  - `multimodal-demo/` - 多模态演示
  - `openai-inbuilt-tools/` - OpenAI 内置工具示例
  - `misc/` - 其他杂项示例

### Cookbook
- **`cookbooks/`** - 教程和使用指南
  - `customer-support-chatbot.ipynb` - 客户支持聊天机器人
  - `mem0-autogen.ipynb` - Mem0 与 AutoGen 集成

---

## 📖 文档和指南

### 文档网站
- **`docs/`** - 完整的文档网站源码
  - `api-reference/` - API 参考文档
  - `examples/` - 示例文档
  - `components/` - 组件文档
  - `integrations/` - 集成指南

### 产品需求文档
- **`prds/`** - 产品需求文档
  - `api.md` - API 需求
  - `base.md` - 基础需求
  - `docker.md` - Docker 需求
  - `llm.md` - LLM 需求
  - `vector.md` - 向量数据库需求

---

## 🔧 服务器和代理

### 服务器代码
- **`server/`** - 独立服务器实现
  - `main.py` - 服务器主文件
  - `Dockerfile` - 服务器 Docker 文件

### 代理服务
- **`openmemory/`** - OpenMemory 开源版本
  - `api/` - API 服务
  - `ui/` - 用户界面

---

## 🎨 静态资源

### 前端资源
- **`static/`** - 静态文件目录
  - `swagger-ui.css` - Swagger UI 样式文件
  - `swagger-ui-bundle.js` - Swagger UI JavaScript
  - `favicon-32x32.png` - 网站图标

---

## 📊 数据和缓存

### 数据目录
- **`data/`** - 数据存储目录
- **`cache/`** - 缓存目录
  - `huggingface/` - HuggingFace 模型缓存
  - `transformers/` - Transformer 模型缓存
- **`logs/`** - 日志文件目录

---

## 🔄 相关项目

### Embedchain 遗留代码
- **`embedchain/`** - Embedchain 项目代码（Mem0 的前身）
  - 包含完整的 embedchain 实现
  - 用于向后兼容和迁移

### Python 虚拟环境
- **`venv/`** - Python 虚拟环境目录（本地开发用）

---

## 🔒 特别说明

### 安全和最佳实践
1. **敏感文件**：
   - `api.log` 包含运行日志，注意不要提交敏感信息
   - `venv/` 是本地虚拟环境，不应提交到版本控制
   - `cache/` 包含模型缓存，体积较大

2. **配置文件**：
   - 各种 Docker 配置文件用于不同部署场景
   - `.yml` 文件包含服务配置，修改时需谨慎

3. **脚本文件**：
   - 所有 `.sh` 脚本都有执行权限
   - 部署脚本会修改系统配置，使用前请仔细检查

### 开发工作流
1. **本地开发**：使用 `start-dev.sh` 或 `start-local.sh`
2. **测试**：运行 `test-env.py` 检查环境，`test-api.sh` 测试 API
3. **部署**：选择对应的部署脚本（阿里云、Docker 等）
4. **监控**：使用 `check-ports.sh` 检查服务状态

---

## 📅 维护信息

- **创建时间**：2025-08-16
- **最后更新**：根据项目结构动态更新
- **维护者**：Mem0 开发团队
- **用途**：为开发者提供项目结构的完整理解

---

> 💡 **提示**：这是一个活跃开发的项目，文件结构可能会发生变化。建议定期更新此文档以保持准确性。

> 🔍 **查看更多**：如需了解具体文件的详细内容，请查看对应的文档文件或源代码。