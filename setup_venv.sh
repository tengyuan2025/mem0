#!/bin/bash

echo "🔧 设置虚拟环境并安装依赖"
echo "=================================="

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 已在虚拟环境中: $VIRTUAL_ENV"
else
    echo "❌ 未在虚拟环境中"
    echo "🔄 创建并激活虚拟环境..."
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "📁 创建虚拟环境..."
        python3 -m venv venv || {
            echo "❌ 创建虚拟环境失败"
            exit 1
        }
    fi
    
    # 激活虚拟环境
    source venv/bin/activate || {
        echo "❌ 无法激活虚拟环境"
        exit 1
    }
    echo "✅ 虚拟环境已激活"
fi

echo ""
echo "📦 升级 pip..."
pip install --upgrade pip

echo ""
echo "📦 安装 DeepSeek + Qdrant 依赖包..."

# 基础 mem0 安装
echo "📦 安装 mem0ai..."
pip install mem0ai

# 向量存储支持
echo "📦 安装向量存储支持..."
pip install 'mem0ai[vector_stores]'

# 中文嵌入模型支持
echo "📦 安装 sentence-transformers..."
pip install sentence-transformers

# Qdrant 客户端
echo "📦 安装 qdrant-client..."
pip install qdrant-client

# 可选：FAISS 支持
echo "📦 安装 FAISS (可选)..."
pip install faiss-cpu

echo ""
echo "📦 安装 Web 服务依赖..."
pip install requests
pip install fastapi
pip install 'uvicorn[standard]'
pip install jinja2
pip install python-multipart

echo ""
echo "📦 安装其他可选依赖..."
pip install ollama

echo ""
echo "✅ 检查安装结果..."
python -c "
import sys
print(f'Python: {sys.version}')
print(f'虚拟环境: {sys.prefix}')

modules = ['requests', 'mem0', 'fastapi', 'uvicorn', 'qdrant_client', 'sentence_transformers', 'faiss']
for mod_name in modules:
    try:
        if mod_name == 'sentence_transformers':
            import sentence_transformers
            print(f'✅ {mod_name} 已安装')
        elif mod_name == 'qdrant_client':
            import qdrant_client
            print(f'✅ {mod_name} 已安装')
        elif mod_name == 'faiss':
            import faiss
            print(f'✅ {mod_name} 已安装')
        else:
            __import__(mod_name)
            print(f'✅ {mod_name} 已安装')
    except ImportError:
        print(f'❌ {mod_name} 安装失败或未安装')
"

echo ""
echo "🎉 安装完成！"
echo ""
echo "💡 下一步："
echo "   1. 启动 Qdrant: docker run -d --name qdrant -p 6333:6333 qdrant/qdrant"
echo "   2. 启动 Ollama: ollama serve"
echo "   3. 下载嵌入模型: ollama pull bge-m3"
echo "   4. 运行服务: python deepseek_web_service.py"