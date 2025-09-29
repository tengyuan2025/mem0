#!/bin/bash

# Mem0 部署状态检查脚本
# 使用方法: ./scripts/check-deployment.sh [服务器IP] [SSH用户]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 参数检查
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <服务器IP> [SSH用户名]"
    echo "示例: $0 192.168.1.100 root"
    exit 1
fi

SSH_HOST="$1"
SSH_USER="${2:-root}"

log "🔍 检查服务器 $SSH_HOST 上的 Mem0 部署状态..."

# 检查SSH连接
echo "📡 测试SSH连接..."
if ssh -o ConnectTimeout=10 "$SSH_USER@$SSH_HOST" "echo 'SSH连接正常'" 2>/dev/null; then
    log "✅ SSH连接正常"
else
    error "❌ SSH连接失败"
    echo "请检查："
    echo "1. 服务器IP是否正确: $SSH_HOST"
    echo "2. SSH用户是否正确: $SSH_USER"
    echo "3. 服务器是否在线"
    echo "4. SSH端口是否开放"
    exit 1
fi

# 检查Docker状态
echo ""
echo "🐳 检查Docker状态..."
docker_status=$(ssh "$SSH_USER@$SSH_HOST" "docker --version 2>/dev/null && echo 'INSTALLED' || echo 'NOT_INSTALLED'")
if [[ "$docker_status" == *"INSTALLED"* ]]; then
    log "✅ Docker已安装"
    docker_version=$(ssh "$SSH_USER@$SSH_HOST" "docker --version")
    echo "   版本: $docker_version"
    
    # 检查Docker服务状态
    docker_running=$(ssh "$SSH_USER@$SSH_HOST" "systemctl is-active docker 2>/dev/null || echo 'inactive'")
    if [ "$docker_running" = "active" ]; then
        log "✅ Docker服务运行正常"
    else
        warn "⚠️ Docker服务未运行"
    fi
else
    error "❌ Docker未安装"
fi

# 检查Mem0容器状态
echo ""
echo "📦 检查Mem0容器状态..."
container_info=$(ssh "$SSH_USER@$SSH_HOST" "docker ps -a --filter name=mem0-api --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo 'NO_CONTAINER'")

if [[ "$container_info" == *"mem0-api"* ]]; then
    echo "$container_info"
    
    # 检查容器是否运行
    if [[ "$container_info" == *"Up"* ]]; then
        log "✅ Mem0容器运行正常"
        
        # 获取端口信息
        if [[ "$container_info" == *"8000"* ]]; then
            log "✅ 端口8000已映射"
        else
            warn "⚠️ 端口8000未正确映射"
        fi
    else
        warn "⚠️ Mem0容器已停止"
        
        # 查看容器日志
        echo "🔍 最近的容器日志："
        ssh "$SSH_USER@$SSH_HOST" "docker logs --tail 10 mem0-api 2>/dev/null || echo '无法获取日志'"
    fi
else
    error "❌ 未找到Mem0容器"
fi

# 检查应用目录
echo ""
echo "📁 检查应用目录..."
app_dir_info=$(ssh "$SSH_USER@$SSH_HOST" "ls -la /opt/mem0/ 2>/dev/null || echo 'NOT_FOUND'")
if [[ "$app_dir_info" != "NOT_FOUND" ]]; then
    log "✅ 应用目录存在: /opt/mem0/"
    
    # 检查关键文件
    key_files=(".env" "app.py" "Dockerfile.simple")
    for file in "${key_files[@]}"; do
        file_exists=$(ssh "$SSH_USER@$SSH_HOST" "[ -f /opt/mem0/$file ] && echo 'EXISTS' || echo 'NOT_FOUND'")
        if [ "$file_exists" = "EXISTS" ]; then
            log "✅ $file 文件存在"
        else
            warn "⚠️ $file 文件不存在"
        fi
    done
else
    error "❌ 应用目录不存在: /opt/mem0/"
fi

# API健康检查
echo ""
echo "🔍 API健康检查..."
health_check=$(ssh "$SSH_USER@$SSH_HOST" "curl -f http://localhost:8000/health 2>/dev/null && echo 'HEALTHY' || echo 'UNHEALTHY'")
if [ "$health_check" = "HEALTHY" ]; then
    log "✅ API健康检查通过"
    
    # 获取API信息
    api_info=$(ssh "$SSH_USER@$SSH_HOST" "curl -s http://localhost:8000/health 2>/dev/null || echo '{}'")
    echo "   API响应: $api_info"
else
    error "❌ API健康检查失败"
    echo "   请检查容器日志或服务配置"
fi

# 检查系统资源
echo ""
echo "📊 系统资源使用情况..."
memory_info=$(ssh "$SSH_USER@$SSH_HOST" "free -h | grep Mem | awk '{print \"使用: \" \$3 \"/\" \$2 \" (\" \$3/\$2*100 \"%)\"}'")
disk_info=$(ssh "$SSH_USER@$SSH_HOST" "df -h /opt/mem0 2>/dev/null | tail -1 | awk '{print \"使用: \" \$3 \"/\" \$2 \" (\" \$5 \")\"}' || echo '无法获取磁盘信息'")

echo "💾 内存: $memory_info"
echo "💿 磁盘: $disk_info"

# 检查网络端口
echo ""
echo "🌐 网络端口检查..."
port_info=$(ssh "$SSH_USER@$SSH_HOST" "netstat -tulpn | grep :8000 || echo 'PORT_NOT_LISTENING'")
if [[ "$port_info" != "PORT_NOT_LISTENING" ]]; then
    log "✅ 端口8000正在监听"
    echo "   $port_info"
else
    warn "⚠️ 端口8000未在监听"
fi

# 总结
echo ""
echo "📋 部署状态总结："
echo "=================================="

# 基础环境检查
if [[ "$docker_status" == *"INSTALLED"* ]] && [ "$docker_running" = "active" ]; then
    log "✅ Docker环境: 正常"
else
    error "❌ Docker环境: 异常"
fi

# 应用状态检查
if [[ "$container_info" == *"Up"* ]] && [ "$health_check" = "HEALTHY" ]; then
    log "✅ Mem0应用: 运行正常"
    echo ""
    echo "🎉 Mem0服务部署成功！"
    echo "📱 API文档: http://$SSH_HOST:8000/docs"
    echo "🔍 健康检查: http://$SSH_HOST:8000/health"
elif [[ "$container_info" == *"mem0-api"* ]]; then
    warn "⚠️ Mem0应用: 容器存在但服务异常"
    echo ""
    echo "🔧 建议操作："
    echo "1. 重启容器: ssh $SSH_USER@$SSH_HOST 'cd /opt/mem0 && docker restart mem0-api'"
    echo "2. 查看日志: ssh $SSH_USER@$SSH_HOST 'docker logs mem0-api'"
    echo "3. 重新部署: 推送代码到GitHub触发自动部署"
else
    error "❌ Mem0应用: 未部署或部署失败"
    echo ""
    echo "🔧 建议操作："
    echo "1. 检查GitHub Actions部署日志"
    echo "2. 手动部署: ssh $SSH_USER@$SSH_HOST 'cd /opt && rm -rf mem0 && git clone <your-repo>'"
    echo "3. 运行部署脚本: ./scripts/deployment/setup-server.sh"
fi

echo ""
log "🔍 检查完成！"