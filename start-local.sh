#!/bin/bash
# 本地安装和运行脚本 (不使用Docker构建)

set -e

echo "🚀 启动 Mem0 本地环境 (原生Python运行)..."

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Python版本: $PYTHON_VERSION"

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️ .env文件不存在，正在创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件并填入你的API密钥"
    echo "然后重新运行此脚本"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装依赖..."
if [ -f "requirements-chinese.txt" ]; then
    pip install -r requirements-chinese.txt
else
    echo "❌ 未找到 requirements-chinese.txt"
    exit 1
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data logs

# 启动Qdrant (使用Docker)
echo "🚀 启动Qdrant数据库..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，无法启动Qdrant"
    echo "请手动启动Docker或安装本地Qdrant"
    exit 1
fi

# 启动简化版docker-compose
docker-compose -f docker-compose.simple.yml up -d

# 等待Qdrant启动
echo "⏳ 等待Qdrant启动..."
sleep 5

# 设置环境变量
export PYTHONPATH=$(pwd)
export MEM0_DIR=$(pwd)/data
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# 加载.env文件
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "✅ 环境准备完成"
echo ""
echo "🌐 服务地址："
echo "  - Qdrant: http://localhost:6333/dashboard"
echo "  - Redis: localhost:6379"
echo ""
echo "🧪 测试中文嵌入模型..."
python3 -c "
try:
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers 可用')
    # 不实际下载模型，只测试导入
    print('💡 首次使用会自动下载BGE-Large-ZH模型')
except ImportError:
    print('❌ sentence-transformers 未安装')
    exit(1)
except Exception as e:
    print(f'⚠️ 导入警告: {e}')
"

echo ""
echo "🚀 启动API服务..."
echo "如果需要停止，按 Ctrl+C"
echo ""

# 启动API服务
python3 -m uvicorn mem0.api.main:app --host 0.0.0.0 --port 8000 --reload