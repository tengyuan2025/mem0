#!/bin/bash
# Mem0 本地开发环境启动脚本

set -e

echo "🚀 启动 Mem0 本地开发环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "⚠️ .env文件不存在，正在创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件并填入你的API密钥："
    echo "   - DOUBAO_API_KEY (推荐用于中文)"
    echo "   - OPENAI_API_KEY (备选方案)"
    echo ""
    echo "然后重新运行此脚本"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data logs

# 构建开发环境镜像
echo "🔨 构建开发环境Docker镜像..."
docker-compose -f docker-compose.dev.yml build

# 启动服务
echo "🚀 启动服务栈..."
docker-compose -f docker-compose.dev.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.dev.yml ps

echo ""
echo "✅ Mem0 开发环境启动完成！"
echo ""
echo "🌐 服务地址："
echo "  - API服务: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - Qdrant管理: http://localhost:6333/dashboard"
echo "  - Redis (可选): localhost:6379"
echo ""
echo "🧪 测试API："
echo "  curl http://localhost:8000/health"
echo ""
echo "📝 查看日志："
echo "  docker-compose -f docker-compose.dev.yml logs -f mem0-api"
echo ""
echo "⏹️ 停止服务："
echo "  docker-compose -f docker-compose.dev.yml down"

# 检查API健康状态
echo "🔍 检查API健康状态..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API服务就绪！"
        break
    elif [ $i -eq 30 ]; then
        echo "❌ API服务启动超时，请检查日志"
        docker-compose -f docker-compose.dev.yml logs mem0-api
        exit 1
    else
        echo "⏳ 等待API服务启动... ($i/30)"
        sleep 2
    fi
done

echo ""
echo "🎉 一切就绪！开始使用Mem0 API吧！"