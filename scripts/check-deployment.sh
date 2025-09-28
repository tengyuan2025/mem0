#!/bin/bash

# Mem0 部署状态检查脚本
# 用法: ./check-deployment.sh [服务器IP]

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SERVER_IP=${1:-"你的服务器IP"}
SSH_USER="deploy"
API_PORT="8000"

# 日志函数
log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Mem0 部署状态检查${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo

# 1. 检查服务器连接
check_server_connection() {
    info "检查服务器连接..."
    
    if ping -c 1 -W 2 $SERVER_IP > /dev/null 2>&1; then
        log "服务器 $SERVER_IP 可达"
    else
        error "无法连接到服务器 $SERVER_IP"
        return 1
    fi
    
    # 测试SSH连接
    if ssh -o ConnectTimeout=5 $SSH_USER@$SERVER_IP "echo 'SSH OK'" > /dev/null 2>&1; then
        log "SSH连接正常"
    else
        warn "SSH连接失败，尝试使用root用户"
        SSH_USER="root"
        if ssh -o ConnectTimeout=5 $SSH_USER@$SERVER_IP "echo 'SSH OK'" > /dev/null 2>&1; then
            log "使用root用户SSH连接成功"
        else
            error "SSH连接失败"
            return 1
        fi
    fi
}

# 2. 检查Docker服务
check_docker() {
    info "检查Docker服务..."
    
    # 检查Docker是否安装
    if ssh $SSH_USER@$SERVER_IP "which docker" > /dev/null 2>&1; then
        log "Docker已安装"
    else
        error "Docker未安装"
        return 1
    fi
    
    # 检查Docker服务状态
    if ssh $SSH_USER@$SERVER_IP "sudo systemctl is-active docker" | grep -q "active"; then
        log "Docker服务运行中"
    else
        error "Docker服务未运行"
        return 1
    fi
}

# 3. 检查Mem0容器
check_containers() {
    info "检查Mem0容器..."
    
    # 获取运行中的容器
    containers=$(ssh $SSH_USER@$SERVER_IP "sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'mem0|nginx|postgres|redis|chroma'" 2>/dev/null)
    
    if [ -z "$containers" ]; then
        warn "没有找到Mem0相关容器"
        
        # 检查停止的容器
        stopped=$(ssh $SSH_USER@$SERVER_IP "sudo docker ps -a --filter 'status=exited' --format '{{.Names}}' | grep -E 'mem0'" 2>/dev/null)
        if [ ! -z "$stopped" ]; then
            error "发现停止的容器: $stopped"
        fi
        return 1
    else
        log "找到运行中的容器:"
        echo "$containers" | while read line; do
            echo "    $line"
        done
    fi
    
    # 专门检查mem0-api容器
    if ssh $SSH_USER@$SERVER_IP "sudo docker ps | grep -q 'mem0-api'"; then
        log "Mem0 API容器运行中"
    else
        # 尝试简单的Python应用
        if ssh $SSH_USER@$SERVER_IP "ps aux | grep -v grep | grep -E 'uvicorn|python.*app'" > /dev/null 2>&1; then
            log "发现Python应用进程"
        else
            warn "Mem0 API容器未运行"
        fi
    fi
}

# 4. 检查API服务
check_api_service() {
    info "检查API服务..."
    
    # 检查端口监听
    if ssh $SSH_USER@$SERVER_IP "sudo netstat -tlnp | grep -q :$API_PORT" 2>/dev/null || \
       ssh $SSH_USER@$SERVER_IP "sudo ss -tlnp | grep -q :$API_PORT" 2>/dev/null; then
        log "端口 $API_PORT 正在监听"
    else
        warn "端口 $API_PORT 未监听"
    fi
    
    # 测试健康检查端点
    echo -n "  测试健康检查端点... "
    
    # 从服务器内部测试
    if ssh $SSH_USER@$SERVER_IP "curl -s -f http://localhost:$API_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}成功${NC}"
        log "API健康检查通过"
    else
        echo -e "${RED}失败${NC}"
        
        # 尝试根路径
        if ssh $SSH_USER@$SERVER_IP "curl -s -f http://localhost:$API_PORT/" > /dev/null 2>&1; then
            warn "根路径可访问，但健康检查端点不可用"
        else
            error "API服务不可访问"
        fi
    fi
    
    # 从外部测试（如果端口开放）
    echo -n "  从外部测试API... "
    if curl -s -f -m 5 "http://$SERVER_IP:$API_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}成功${NC}"
        log "外部可访问API"
    else
        echo -e "${YELLOW}失败${NC}"
        warn "外部无法访问API（可能是防火墙限制）"
    fi
}

# 5. 检查日志
check_logs() {
    info "检查最近日志..."
    
    # 检查Docker日志
    if ssh $SSH_USER@$SERVER_IP "sudo docker logs --tail 10 mem0-api 2>&1 | grep -q 'ERROR'" 2>/dev/null; then
        warn "发现错误日志"
    else
        log "未发现明显错误"
    fi
    
    # 显示最后几行日志
    echo "  最近的应用日志:"
    ssh $SSH_USER@$SERVER_IP "sudo docker logs --tail 5 mem0-api 2>&1" 2>/dev/null || \
    ssh $SSH_USER@$SERVER_IP "sudo tail -5 /opt/mem0/logs/app.log 2>/dev/null" || \
    echo "    （无法获取日志）"
}

# 6. 系统资源检查
check_resources() {
    info "检查系统资源..."
    
    # 内存使用
    mem_usage=$(ssh $SSH_USER@$SERVER_IP "free -m | grep Mem | awk '{print int(\$3/\$2*100)}'" 2>/dev/null)
    if [ ! -z "$mem_usage" ]; then
        if [ "$mem_usage" -lt 80 ]; then
            log "内存使用率: ${mem_usage}%"
        else
            warn "内存使用率较高: ${mem_usage}%"
        fi
    fi
    
    # 磁盘使用
    disk_usage=$(ssh $SSH_USER@$SERVER_IP "df -h / | tail -1 | awk '{print \$5}' | sed 's/%//'" 2>/dev/null)
    if [ ! -z "$disk_usage" ]; then
        if [ "$disk_usage" -lt 80 ]; then
            log "磁盘使用率: ${disk_usage}%"
        else
            warn "磁盘使用率较高: ${disk_usage}%"
        fi
    fi
}

# 主函数
main() {
    local failed=0
    
    # 运行所有检查
    check_server_connection || ((failed++))
    check_docker || ((failed++))
    check_containers || ((failed++))
    check_api_service || ((failed++))
    check_logs
    check_resources
    
    echo
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✅ 部署状态: 正常${NC}"
        echo
        info "API地址: http://$SERVER_IP:$API_PORT"
        info "文档地址: http://$SERVER_IP:$API_PORT/docs"
    else
        echo -e "${YELLOW}⚠️ 部署状态: 存在问题${NC}"
        echo
        echo "建议操作:"
        echo "1. SSH登录服务器: ssh $SSH_USER@$SERVER_IP"
        echo "2. 查看容器: docker ps -a"
        echo "3. 查看日志: docker logs mem0-api"
        echo "4. 重启服务: cd /opt/mem0 && docker-compose restart"
    fi
    
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
}

# 运行主函数
main