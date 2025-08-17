#!/bin/bash

echo "🔍 Mem0项目端口和接口占用情况"
echo "==============================="

echo ""
echo "📊 监听端口状态："
echo "----------------"
echo "端口    服务            状态    描述"
echo "8000    Mem0 API       $(curl -s http://localhost:8000/health >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 停止')    FastAPI Web服务"
echo "8004    Mem0 API       $(curl -s http://localhost:8004/health >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 停止')    FastAPI Web服务(当前运行)"
echo "6333    Qdrant REST    $(curl -s http://localhost:6333 >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 停止')    向量数据库REST API"
echo "6334    Qdrant gRPC    $(netstat -an | grep :6334 | grep LISTEN >/dev/null && echo '✅ 监听中' || echo '❌ 停止')    向量数据库gRPC API"
echo "6379    Redis          $(redis-cli -p 6379 ping 2>/dev/null | grep PONG >/dev/null && echo '✅ 运行中' || echo '❌ 停止')    缓存数据库"

echo ""
echo "🌐 API接口列表："
echo "----------------"

if curl -s http://localhost:8004/health >/dev/null 2>&1; then
    echo "基础接口："
    echo "  GET  /                    - 根路径信息"
    echo "  GET  /health              - 健康检查"
    echo "  GET  /docs               - Swagger UI文档"
    echo "  GET  /redoc              - ReDoc文档" 
    echo "  GET  /openapi.json       - OpenAPI规范"
    echo ""
    echo "记忆管理接口："
    echo "  POST /v1/memories/        - 创建记忆"
    echo "  GET  /v1/memories/        - 获取用户记忆"
    echo "  GET  /v1/memories/all     - 获取所有记忆"
    echo "  POST /v1/memories/search  - 搜索记忆(推荐)"
    echo "  GET  /v1/memories/search  - 搜索记忆(简单)"
    echo ""
    echo "系统管理接口："
    echo "  GET    /v1/system/stats     - 系统统计信息"
    echo "  DELETE /v1/system/clear     - 清理所有数据"
    echo "  DELETE /v1/memories/user/{id} - 删除用户记忆"
    echo ""
    echo "数据库接口："
    echo "  GET  /v1/collections      - Qdrant集合信息"
    echo ""
    echo "静态资源："
    echo "  GET  /static/*            - 本地静态文件"
else
    echo "❌ API服务未运行，无法获取接口列表"
fi

echo ""
echo "🔧 进程状态："
echo "------------"
echo "Docker容器："
docker-compose -f docker-compose.simple.yml ps --format table 2>/dev/null | head -5

echo ""
echo "Python进程："
ps aux | grep -E "(simple-api|uvicorn)" | grep -v grep | head -3

echo ""
echo "📈 网络连接："
echo "------------"
echo "活跃连接数："
netstat -an | grep -E "(8000|8001|6333|6334|6379)" | grep ESTABLISHED | wc -l | awk '{print "  活跃连接: " $1 " 个"}'

echo "监听状态："
netstat -an | grep LISTEN | grep -E "(8000|6333|6334|6379)" | awk '{print "  " $4 " - 监听中"}'

echo ""
echo "🚨 注意事项："
echo "------------"
echo "• 端口8004: 主要的API服务端口，外部应用通过此端口访问"  
echo "• 端口6333: Qdrant REST API，一般只内部使用"
echo "• 端口6334: Qdrant gRPC API，一般只内部使用"
echo "• 端口6379: Redis缓存，一般只内部使用"
echo "• 如果要对外提供服务，只需要开放8004端口即可"