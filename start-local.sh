#!/bin/bash
# 本地安装和运行脚本 (不使用Docker)

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
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        # 创建基本的 .env 文件
        cat > .env << 'EOF'
# Mem0 本地开发环境配置

# ===== 必需配置 =====
# 豆包 API 密钥 (推荐用于中文，获取地址: https://www.doubao.com/)
DOUBAO_API_KEY=your_doubao_api_key_here

# 方舟 API 密钥 (火山引擎，获取地址: https://www.volcengine.com/product/ark)
ARK_API_KEY=your_ark_api_key_here

# OpenAI API 密钥 (备选方案，获取地址: https://platform.openai.com/)
OPENAI_API_KEY=your_openai_api_key_here

# ===== 可选配置 =====
# 豆包 API 基础地址
DOUBAO_API_BASE=https://ark.cn-beijing.volces.com/api/v3

# 数据存储目录
MEM0_DIR=./data

# Qdrant 向量数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 日志级别
LOG_LEVEL=DEBUG

# 调试模式
DEBUG=1
EOF
    fi
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
mkdir -p data logs qdrant_data

# 检查并安装本地Qdrant
echo "🔍 检查本地Qdrant..."
if ! command -v qdrant &> /dev/null; then
    echo "📦 Qdrant未安装，正在安装..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "🍺 使用Homebrew安装Qdrant..."
            brew install qdrant
        else
            echo "❌ 未找到Homebrew，请先安装Homebrew或手动安装Qdrant"
            echo "手动安装地址: https://qdrant.tech/documentation/guides/installation/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "🐧 在Linux上安装Qdrant..."
        if command -v curl &> /dev/null; then
            # 下载并安装Qdrant
            QDRANT_VERSION="1.8.1"
            curl -L https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar -xz
            sudo mv qdrant /usr/local/bin/
            echo "✅ Qdrant安装完成"
        else
            echo "❌ 未找到curl，请手动安装Qdrant"
            exit 1
        fi
    else
        echo "❌ 不支持的操作系统: $OSTYPE"
        echo "请手动安装Qdrant: https://qdrant.tech/documentation/guides/installation/"
        exit 1
    fi
else
    echo "✅ Qdrant已安装"
fi

# 启动本地Qdrant
echo "🚀 启动本地Qdrant数据库..."
if pgrep -f "qdrant" > /dev/null; then
    echo "⚠️ Qdrant已在运行，跳过启动"
else
    # 启动Qdrant后台进程
    qdrant --storage-path ./qdrant_data --http-port 6333 --grpc-port 6334 > qdrant.log 2>&1 &
    QDRANT_PID=$!
    echo "📝 Qdrant进程ID: $QDRANT_PID"
    echo $QDRANT_PID > qdrant.pid
    
    # 等待Qdrant启动
    echo "⏳ 等待Qdrant启动..."
    for i in {1..30}; do
        if curl -s http://localhost:6333/health > /dev/null 2>&1; then
            echo "✅ Qdrant启动成功！"
            break
        elif [ $i -eq 30 ]; then
            echo "❌ Qdrant启动超时"
            kill $QDRANT_PID 2>/dev/null || true
            exit 1
        else
            echo "⏳ 等待Qdrant启动... ($i/30)"
            sleep 2
        fi
    done
fi

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
echo "  - Qdrant API: http://localhost:6333"
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