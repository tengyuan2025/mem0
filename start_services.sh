#!/bin/bash

echo "🚀 启动 DeepSeek + Qdrant 完整服务"
echo "=================================="

# 检查 Docker 是否运行
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 停止旧的 Qdrant 容器（如果存在）
echo "🔄 清理旧的 Qdrant 容器..."
docker stop qdrant 2>/dev/null || true
docker rm qdrant 2>/dev/null || true

# 启动 Qdrant 容器
echo "🗄️ 启动 Qdrant 向量数据库..."
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

if [ $? -ne 0 ]; then
    echo "❌ Qdrant 启动失败"
    exit 1
fi

# 等待 Qdrant 完全启动
echo "⏳ 等待 Qdrant 启动（最多60秒）..."
for i in {1..60}; do
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        echo "✅ Qdrant 启动成功！"
        break
    fi
    
    if [ $i -eq 60 ]; then
        echo "⚠️  Qdrant 启动超时，但将继续启动 Web 服务"
        break
    fi
    
    echo -n "."
    sleep 1
done

echo ""
echo "📊 Qdrant 状态:"
echo "   - 容器状态: $(docker ps --format 'table {{.Names}}\t{{.Status}}' | grep qdrant | cut -f2 || echo '未运行')"
echo "   - HTTP 端口: 6333"
echo "   - gRPC 端口: 6334"
echo "   - Web 界面: http://localhost:6333/dashboard"

echo ""
echo "🌐 启动 DeepSeek Web 服务..."
echo "   - Web 界面: http://localhost:9000"
echo "   - API 文档: http://localhost:9000/docs"
echo ""

# 启动 Web 服务
python deepseek_web_service.py