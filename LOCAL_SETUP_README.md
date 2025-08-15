# Mem0 本地环境设置指南

## 🚀 快速开始

### 1. 启动本地环境

```bash
./start-local.sh
```

### 2. 停止本地环境

```bash
./stop-local.sh
```

## 📋 环境要求

### 必需软件

- **Python 3.9+**
- **Homebrew** (macOS) 或 **curl** (Linux)

### 可选软件

- **Git** (用于代码管理)

## 🔧 安装流程

### 1. 自动安装 (推荐)

脚本会自动检测并安装：

- Python 虚拟环境
- 项目依赖包
- 本地 Qdrant 数据库

### 2. 手动安装

如果自动安装失败，可以手动安装：

#### macOS

```bash
# 安装 Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Qdrant
brew install qdrant
```

#### Linux

```bash
# 下载并安装 Qdrant
QDRANT_VERSION="1.8.1"
curl -L https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar -xz
sudo mv qdrant /usr/local/bin/
```

## ⚙️ 配置说明

### 1. API 密钥配置

在 `.env` 文件中配置：

```bash
# 必需配置
DOUBAO_API_KEY=your_doubao_api_key_here
ARK_API_KEY=your_ark_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 可选配置
DOUBAO_API_BASE=https://ark.cn-beijing.volces.com/api/v3
MEM0_DIR=./data
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2. 获取 API 密钥

- **豆包 API**: https://www.doubao.com/
- **方舟 API**: https://www.volcengine.com/product/ark
- **OpenAI API**: https://platform.openai.com/

## 🌐 服务地址

启动成功后，可以访问：

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Qdrant 管理**: http://localhost:6333/dashboard
- **Qdrant API**: http://localhost:6333

## 📁 目录结构

```
mem0/
├── data/           # 数据存储目录
├── logs/           # 日志文件目录
├── qdrant_data/    # Qdrant 数据目录
├── qdrant.log      # Qdrant 日志文件
├── qdrant.pid      # Qdrant 进程 ID 文件
├── venv/           # Python 虚拟环境
├── start-local.sh  # 启动脚本
└── stop-local.sh   # 停止脚本
```

## 🐛 故障排除

### 1. Qdrant 启动失败

```bash
# 检查端口占用
lsof -i :6333

# 查看 Qdrant 日志
tail -f qdrant.log

# 强制停止所有 Qdrant 进程
pkill -9 -f qdrant
```

### 2. Python 依赖安装失败

```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-chinese.txt
```

### 3. 端口冲突

```bash
# 修改端口 (在 .env 文件中)
QDRANT_PORT=6334  # 改为其他端口
```

## 🔄 更新和维护

### 1. 更新依赖

```bash
source venv/bin/activate
pip install --upgrade -r requirements-chinese.txt
```

### 2. 清理数据

```bash
# 停止服务
./stop-local.sh

# 清理数据 (谨慎操作)
rm -rf qdrant_data data logs
```

### 3. 重启服务

```bash
./stop-local.sh
./start-local.sh
```

## 💡 使用技巧

### 1. 开发模式

```bash
# 启动时自动重载
python3 -m uvicorn mem0.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 调试模式

```bash
# 设置调试环境变量
export DEBUG=1
export LOG_LEVEL=DEBUG
```

### 3. 性能优化

```bash
# 使用生产模式启动
python3 -m uvicorn mem0.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件
2. 检查 `.env` 配置
3. 确认网络连接
4. 查看项目文档

## 🔒 安全注意事项

- 不要将 `.env` 文件提交到版本控制
- 定期更新 API 密钥
- 在生产环境中使用 HTTPS
- 限制数据库访问权限
