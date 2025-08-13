#!/bin/bash
# Docker资源存储位置查看脚本

echo "🔍 Docker资源存储位置详解"
echo "============================"

# 检测操作系统
OS_TYPE=$(uname -s)

echo "1️⃣ Docker镜像存储位置："
echo "----------------------------"

if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "🍎 macOS 系统："
    echo "Docker镜像位置: ~/Library/Containers/com.docker.docker/Data/vms/0/data/docker/image/"
    echo "Docker容器位置: ~/Library/Containers/com.docker.docker/Data/vms/0/data/docker/containers/"
    echo "Docker数据根目录: ~/Library/Containers/com.docker.docker/Data/vms/0/data/"
    
    # 检查Docker Desktop数据使用情况
    if command -v docker &> /dev/null; then
        echo ""
        echo "📊 Docker空间使用情况:"
        docker system df
    fi
    
elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "🐧 Linux 系统："
    echo "Docker根目录: /var/lib/docker/"
    echo "Docker镜像: /var/lib/docker/image/"
    echo "Docker容器: /var/lib/docker/containers/"
    echo "Docker数据卷: /var/lib/docker/volumes/"
    
    if command -v docker &> /dev/null; then
        echo ""
        echo "📊 Docker空间使用情况:"
        docker system df 2>/dev/null || echo "需要sudo权限查看"
    fi
else
    echo "❓ 未知系统类型: $OS_TYPE"
fi

echo ""
echo "2️⃣ Mem0项目相关存储："
echo "----------------------------"

# 查看Docker镜像
echo "🖼️ 已下载的镜像:"
docker images | grep -E "(python|qdrant|redis|mem0)" || echo "暂无相关镜像"

echo ""
echo "📦 项目相关数据卷:"
docker volume ls | grep -E "(mem0|qdrant|redis|huggingface)" || echo "暂无相关数据卷"

echo ""
echo "3️⃣ AI模型存储位置："
echo "----------------------------"

# 检查模型缓存数据卷
if docker volume inspect huggingface_cache >/dev/null 2>&1; then
    echo "🤗 HuggingFace模型缓存卷已创建"
    echo "数据卷路径: $(docker volume inspect huggingface_cache --format '{{.Mountpoint}}' 2>/dev/null || echo '查看需要sudo权限')"
else
    echo "🤗 HuggingFace模型缓存卷未创建 (首次运行时会创建)"
fi

if docker volume inspect transformers_cache >/dev/null 2>&1; then
    echo "🔄 Transformers模型缓存卷已创建"
    echo "数据卷路径: $(docker volume inspect transformers_cache --format '{{.Mountpoint}}' 2>/dev/null || echo '查看需要sudo权限')"
else
    echo "🔄 Transformers模型缓存卷未创建 (首次运行时会创建)"
fi

echo ""
echo "4️⃣ 数据存储大小："
echo "----------------------------"

if command -v docker &> /dev/null; then
    echo "📊 Docker系统占用空间："
    docker system df
    
    echo ""
    echo "📁 项目数据卷大小："
    for volume in mem0_data qdrant_data huggingface_cache transformers_cache; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            # 尝试获取数据卷大小 (Linux可用)
            if [[ "$OS_TYPE" == "Linux" ]]; then
                size=$(sudo du -sh $(docker volume inspect "$volume" --format '{{.Mountpoint}}') 2>/dev/null | cut -f1 || echo "未知")
                echo "  📦 $volume: $size"
            else
                echo "  📦 $volume: 已创建 (macOS上查看大小需特殊方法)"
            fi
        else
            echo "  📦 $volume: 未创建"
        fi
    done
fi

echo ""
echo "5️⃣ 清理命令 (谨慎使用)："
echo "----------------------------"
echo "🗑️ 清理未使用的镜像: docker image prune"
echo "🗑️ 清理未使用的数据卷: docker volume prune"
echo "🗑️ 清理整个Docker系统: docker system prune -a"
echo "🗑️ 查看可清理空间: docker system df"

echo ""
echo "⚠️ 注意事项："
echo "- 模型文件只在首次API调用时下载"
echo "- BGE-Large-ZH模型约1.3GB，下载一次后永久缓存"
echo "- Docker镜像在本地永久保存，除非手动删除"
echo "- 数据卷中的数据在容器重启后保持不变"