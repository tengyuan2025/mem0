#!/bin/bash
# Docker网络问题修复脚本

echo "🔧 修复Docker网络连接问题..."

# 检查系统类型
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 检测到macOS系统"
    
    # macOS Docker Desktop配置
    echo "🏃 为macOS Docker Desktop配置镜像加速器..."
    
    echo "请按以下步骤配置Docker Desktop:"
    echo "1. 打开Docker Desktop"
    echo "2. 点击设置 (Settings)"
    echo "3. 选择 Docker Engine"
    echo "4. 在配置中添加以下内容:"
    
    cat << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ],
  "dns": ["8.8.8.8", "114.114.114.114"]
}
EOF
    
    echo ""
    echo "5. 点击 Apply & Restart"
    echo ""
    echo "或者你也可以使用以下命令自动配置 (需要重启Docker):"
    echo 'echo '"'"'{"registry-mirrors":["https://docker.mirrors.ustc.edu.cn"],"dns":["8.8.8.8"]}'"'"' > ~/.docker/daemon.json'
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 检测到Linux系统"
    
    # 为Linux配置Docker镜像加速器
    echo "配置Docker镜像加速器..."
    sudo mkdir -p /etc/docker
    
    sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ],
  "dns": ["8.8.8.8", "114.114.114.114"]
}
EOF
    
    echo "重启Docker服务..."
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    echo "✅ Docker配置已更新"
else
    echo "❓ 未知系统类型: $OSTYPE"
fi

echo ""
echo "🔄 尝试手动拉取基础镜像..."

# 尝试从不同镜像源拉取
MIRRORS=(
    "docker.mirrors.ustc.edu.cn"
    "hub-mirror.c.163.com"
    "registry.docker-cn.com"
    ""  # 官方源
)

for mirror in "${MIRRORS[@]}"; do
    if [ -z "$mirror" ]; then
        echo "📡 尝试官方Docker Hub..."
        IMAGE="python:3.11-slim"
    else
        echo "📡 尝试镜像源: $mirror"
        IMAGE="$mirror/library/python:3.11-slim"
    fi
    
    if timeout 60 docker pull "$IMAGE"; then
        echo "✅ 成功拉取镜像: $IMAGE"
        
        # 如果不是官方源，需要重新标记
        if [ ! -z "$mirror" ]; then
            docker tag "$IMAGE" "python:3.11-slim"
            echo "🏷️ 已重新标记为: python:3.11-slim"
        fi
        break
    else
        echo "❌ 从 $mirror 拉取失败"
    fi
done

echo ""
echo "🧪 测试Docker网络连接..."
if docker run --rm python:3.11-slim python --version > /dev/null 2>&1; then
    echo "✅ Docker网络连接正常"
else
    echo "❌ Docker网络仍有问题"
fi

echo ""
echo "📝 如果问题仍然存在，请尝试以下方法:"
echo "1. 检查网络连接"
echo "2. 重启Docker服务"
echo "3. 清理Docker缓存: docker system prune"
echo "4. 使用VPN或更换网络环境"