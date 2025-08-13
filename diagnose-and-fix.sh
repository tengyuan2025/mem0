#!/bin/bash
# Docker网络问题诊断和修复脚本

echo "🔍 Mem0 Docker网络问题诊断和修复"
echo "=================================="

# 检查Docker是否运行
echo "1️⃣ 检查Docker状态..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请启动Docker Desktop"
    exit 1
fi
echo "✅ Docker正在运行"

# 检查网络连通性
echo ""
echo "2️⃣ 检查网络连通性..."
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ 网络连接正常"
else
    echo "⚠️ 网络连接异常，可能影响Docker镜像拉取"
fi

# 检查DNS
echo ""
echo "3️⃣ 检查DNS解析..."
if nslookup registry-1.docker.io > /dev/null 2>&1; then
    echo "✅ DNS解析正常"
else
    echo "⚠️ DNS解析异常"
fi

# 清理Docker缓存
echo ""
echo "4️⃣ 清理Docker缓存..."
docker system prune -f
echo "✅ Docker缓存已清理"

# 尝试手动拉取镜像
echo ""
echo "5️⃣ 尝试拉取基础镜像..."

# 设置较长的超时时间
export DOCKER_CLIENT_TIMEOUT=120
export COMPOSE_HTTP_TIMEOUT=120

# 尝试不同的镜像源
IMAGES=(
    "python:3.11-slim"
    "python:3.11"
    "python:3.10-slim"
)

SUCCESS=false
for image in "${IMAGES[@]}"; do
    echo "📡 尝试拉取: $image"
    if timeout 180 docker pull "$image"; then
        # 如果成功拉取了其他版本，重新标记为需要的版本
        if [ "$image" != "python:3.11-slim" ]; then
            docker tag "$image" "python:3.11-slim"
            echo "🏷️ 已标记为 python:3.11-slim"
        fi
        echo "✅ 成功拉取镜像"
        SUCCESS=true
        break
    else
        echo "❌ 拉取失败: $image"
    fi
done

if [ "$SUCCESS" = false ]; then
    echo "❌ 所有镜像拉取失败"
    echo ""
    echo "🛠️ 建议的解决方案："
    echo "1. 配置Docker镜像加速器："
    echo "   ./fix-docker-network.sh"
    echo ""
    echo "2. 使用本地Python环境："
    echo "   ./start-local.sh"
    echo ""
    echo "3. 使用备用Dockerfile："
    echo "   mv Dockerfile.dev.fallback Dockerfile.dev"
    echo "   ./start-dev.sh"
    echo ""
    echo "4. 只启动数据库服务："
    echo "   docker-compose -f docker-compose.simple.yml up -d"
    exit 1
fi

# 验证其他必需镜像
echo ""
echo "6️⃣ 验证其他服务镜像..."

OTHER_IMAGES=(
    "qdrant/qdrant:v1.8.1"
    "redis:7-alpine"
)

for image in "${OTHER_IMAGES[@]}"; do
    echo "📡 检查镜像: $image"
    if ! docker image inspect "$image" > /dev/null 2>&1; then
        echo "⬇️ 拉取镜像: $image"
        if ! timeout 120 docker pull "$image"; then
            echo "⚠️ 拉取失败，但不影响主要功能: $image"
        fi
    else
        echo "✅ 镜像已存在: $image"
    fi
done

echo ""
echo "7️⃣ 测试Docker构建..."
cat > Dockerfile.test << 'EOF'
FROM python:3.11-slim
RUN echo "Docker build test successful"
EOF

if docker build -f Dockerfile.test -t test-build . > /dev/null 2>&1; then
    echo "✅ Docker构建测试成功"
    docker rmi test-build > /dev/null 2>&1
    rm Dockerfile.test
else
    echo "❌ Docker构建测试失败"
    rm -f Dockerfile.test
fi

echo ""
echo "🎉 诊断完成！"
echo ""
echo "💡 推荐的启动方式："
echo ""
echo "方式1 - Docker完整环境 (推荐):"
echo "  ./start-dev.sh"
echo ""
echo "方式2 - 本地Python + Docker数据库:"
echo "  ./start-local.sh"
echo ""
echo "方式3 - 仅数据库服务:"
echo "  docker-compose -f docker-compose.simple.yml up -d"
echo "  # 然后手动运行: python -m uvicorn mem0.api.main:app --reload"
echo ""
echo "🔧 如果仍有问题，请运行："
echo "  ./fix-docker-network.sh"