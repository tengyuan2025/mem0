#!/bin/bash

# Mem0 API Docker 一键部署脚本
# 支持本地开发和生产环境部署

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
🐳 Mem0 API Docker 部署脚本

用法: $0 [选项]

选项:
    -e, --env           环境类型 (dev|prod) [默认: dev]
    -p, --port          API 端口 [默认: 8000]
    -d, --detach        后台运行
    -b, --build         强制重新构建镜像
    -c, --clean         清理现有容器和镜像
    -m, --monitoring    启用监控服务 (仅生产环境)
    -s, --stop          停止所有服务
    -l, --logs          查看日志
    -h, --help          显示帮助信息

示例:
    # 开发环境部署
    $0 --env dev

    # 生产环境部署（含监控）
    $0 --env prod --monitoring --detach

    # 强制重新构建并部署
    $0 --build --env dev

    # 停止所有服务
    $0 --stop

    # 查看日志
    $0 --logs
EOF
}

# 默认参数
ENV="dev"
PORT="8000"
DETACH=""
BUILD=""
CLEAN=""
MONITORING=""
STOP=""
LOGS=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--detach)
            DETACH="--detach"
            shift
            ;;
        -b|--build)
            BUILD="--build"
            shift
            ;;
        -c|--clean)
            CLEAN="true"
            shift
            ;;
        -m|--monitoring)
            MONITORING="--profile monitoring"
            shift
            ;;
        -s|--stop)
            STOP="true"
            shift
            ;;
        -l|--logs)
            LOGS="true"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证环境参数
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    log_error "环境参数必须是 'dev' 或 'prod'"
    exit 1
fi

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "🐳 Mem0 API Docker 部署脚本启动"
log_info "部署环境: $ENV"

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    
    log_info "✅ Docker 检查通过"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_info "✅ Docker Compose 检查通过"
}

# 检查环境变量文件
check_env_file() {
    if [[ ! -f ".env" ]]; then
        log_warn ".env 文件不存在，从模板创建..."
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warn "请编辑 .env 文件并设置必要的环境变量"
            log_warn "特别是 OPENAI_API_KEY"
        else
            log_error ".env.example 模板文件不存在"
            exit 1
        fi
    fi
    
    # 检查必需的环境变量
    source .env
    if [[ -z "$OPENAI_API_KEY" ]]; then
        log_error "OPENAI_API_KEY 未设置，请在 .env 文件中设置"
        exit 1
    fi
    
    log_info "✅ 环境变量检查通过"
}

# 创建必要的目录
create_directories() {
    log_step "创建数据目录..."
    mkdir -p data logs config ssl
    
    # 设置权限
    chmod 755 data logs config
    
    log_info "✅ 目录创建完成"
}

# 清理现有容器和镜像
clean_containers() {
    log_step "清理现有容器和镜像..."
    
    # 停止并删除容器
    docker-compose -f docker-compose.yml down --remove-orphans --volumes || true
    
    if [[ "$ENV" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml down --remove-orphans --volumes || true
    fi
    
    # 删除相关镜像
    docker images --format "{{.Repository}}:{{.Tag}}" | grep mem0 | xargs -r docker rmi -f || true
    
    # 清理未使用的镜像和网络
    docker system prune -f
    
    log_info "✅ 清理完成"
}

# 停止所有服务
stop_services() {
    log_step "停止所有服务..."
    
    docker-compose -f docker-compose.yml down || true
    
    if [[ "$ENV" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml down || true
    fi
    
    log_info "✅ 服务已停止"
}

# 查看日志
show_logs() {
    log_step "显示服务日志..."
    
    if [[ "$ENV" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml logs -f --tail=100
    else
        docker-compose -f docker-compose.yml logs -f --tail=100
    fi
}

# 部署服务
deploy_services() {
    local compose_file="docker-compose.yml"
    local compose_args=""
    
    if [[ "$ENV" == "prod" ]]; then
        compose_file="docker-compose.prod.yml"
        compose_args="--profile production"
        
        if [[ -n "$MONITORING" ]]; then
            compose_args="$compose_args --profile monitoring"
        fi
    fi
    
    log_step "使用配置文件: $compose_file"
    
    # 构建和启动服务
    local docker_cmd="docker-compose -f $compose_file $compose_args up $BUILD $DETACH"
    
    log_step "执行命令: $docker_cmd"
    
    eval "$docker_cmd"
    
    if [[ -z "$DETACH" ]]; then
        log_info "✅ 服务启动完成"
    else
        log_info "✅ 服务在后台启动"
        log_info "使用 'docker-compose -f $compose_file logs -f' 查看日志"
    fi
}

# 等待服务健康检查
wait_for_health() {
    if [[ -n "$DETACH" ]]; then
        log_step "等待服务健康检查..."
        
        local max_attempts=30
        local attempt=0
        
        while [[ $attempt -lt $max_attempts ]]; do
            if curl -f http://localhost:$PORT/health &> /dev/null; then
                log_info "✅ API 服务健康检查通过"
                break
            fi
            
            attempt=$((attempt + 1))
            log_info "等待服务启动... ($attempt/$max_attempts)"
            sleep 5
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "服务健康检查失败，请检查日志"
            docker-compose logs
            exit 1
        fi
    fi
}

# 显示部署信息
show_deployment_info() {
    log_info "🎉 Mem0 API 部署完成!"
    log_info ""
    log_info "📊 服务信息:"
    log_info "  • API 服务: http://localhost:$PORT"
    log_info "  • API 文档: http://localhost:$PORT/docs"
    log_info "  • 健康检查: http://localhost:$PORT/health"
    
    if [[ "$ENV" == "prod" ]]; then
        log_info "  • Qdrant 控制台: http://localhost:6333/dashboard"
        
        if [[ -n "$MONITORING" ]]; then
            log_info "  • Prometheus: http://localhost:9090"
            log_info "  • Grafana: http://localhost:3000 (admin/admin123)"
        fi
    fi
    
    log_info ""
    log_info "🔧 管理命令:"
    log_info "  • 查看日志: $0 --logs"
    log_info "  • 停止服务: $0 --stop"
    log_info "  • 重新部署: $0 --env $ENV --build"
    log_info "  • 清理重置: $0 --clean"
    
    if [[ "$ENV" == "dev" ]]; then
        log_info ""
        log_info "🧪 测试命令:"
        log_info "  • 运行测试: python example_client.py"
        log_info "  • API 测试: curl http://localhost:$PORT/health"
    fi
}

# 主函数
main() {
    # 处理特殊操作
    if [[ "$STOP" == "true" ]]; then
        check_docker
        check_docker_compose
        stop_services
        exit 0
    fi
    
    if [[ "$LOGS" == "true" ]]; then
        check_docker
        check_docker_compose
        show_logs
        exit 0
    fi
    
    # 系统检查
    check_docker
    check_docker_compose
    check_env_file
    
    # 创建目录
    create_directories
    
    # 清理（如果需要）
    if [[ "$CLEAN" == "true" ]]; then
        clean_containers
    fi
    
    # 部署服务
    deploy_services
    
    # 等待健康检查
    wait_for_health
    
    # 显示部署信息
    show_deployment_info
}

# 捕获中断信号
trap 'log_error "部署被中断"; exit 1' INT TERM

# 执行主函数
main "$@"