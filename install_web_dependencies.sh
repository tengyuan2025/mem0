#!/bin/bash

echo "🔧 安装 DeepSeek + Qdrant Web 服务依赖..."

# 基础依赖
echo "📦 安装基础依赖..."
pip install 'mem0ai[vector_stores]'
pip install sentence-transformers
pip install qdrant-client

# Web 服务依赖
echo "🌐 安装 Web 服务依赖..."
pip install fastapi
pip install uvicorn[standard]
pip install jinja2
pip install python-multipart

# 可选依赖
echo "📊 安装可选依赖..."
pip install requests  # API 测试需要

# 检查安装结果
echo ""
echo "✅ 检查安装结果:"

check_package() {
    python -c "import $1; print('✅ $1 已安装')" 2>/dev/null || echo "❌ $1 安装失败"
}

check_package "mem0"
check_package "sentence_transformers"
check_package "qdrant_client"
check_package "fastapi"
check_package "uvicorn"
check_package "requests"

echo ""
echo "🎉 依赖安装完成！"
echo "📝 现在可以运行: python deepseek_web_service.py"