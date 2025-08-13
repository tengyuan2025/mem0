#!/bin/bash

echo "🚀 启动 Mem0 本地开发环境 (中国网络优化版本)..."

# 检查 Docker 是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 没有运行，请先启动 Docker Desktop"
    exit 1
fi

echo "📁 创建数据目录..."
mkdir -p data logs cache/huggingface cache/transformers

echo "🔨 使用优化版本构建Docker镜像 (使用中国镜像源)..."
docker-compose -f docker-compose.dev.yml build --build-arg DOCKERFILE=Dockerfile.dev.fast mem0-api

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Docker镜像构建失败"
    echo ""
    echo "🔄 建议尝试以下解决方案："
    echo "1. 检查网络连接"
    echo "2. 重启Docker Desktop"
    echo "3. 清理Docker缓存: docker system prune -a"
    echo "4. 使用本地Python开发: ./start-local.sh"
    exit 1
fi

echo "🚀 启动所有服务..."
docker-compose -f docker-compose.dev.yml up -d

echo "⏳ 等待服务启动..."
sleep 10

echo ""
echo "✅ Mem0开发环境启动成功！"
echo ""
echo "🌐 服务地址："
echo "  • Mem0 API: http://localhost:8000"
echo "  • API文档: http://localhost:8000/docs"
echo "  • Qdrant管理界面: http://localhost:6333/dashboard"
echo "  • Redis管理: redis://localhost:6379"
echo ""
echo "📋 常用命令："
echo "  • 查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "  • 停止服务: docker-compose -f docker-compose.dev.yml down"
echo "  • 重启服务: docker-compose -f docker-compose.dev.yml restart"
echo ""
echo "🧪 测试API："
echo "  curl -X POST http://localhost:8000/v1/memories/ \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"messages\": [{\"role\": \"user\", \"content\": \"我喜欢中文AI\"}], \"user_id\": \"test\"}'"