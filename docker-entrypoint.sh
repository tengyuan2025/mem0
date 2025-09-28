#!/bin/bash
set -e

# 生产环境Docker入口脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# 等待服务函数
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    log "等待 $service_name 服务启动 ($host:$port)"
    
    while [ $attempt -le $max_attempts ]; do
        if timeout 1 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
            log "$service_name 服务已就绪"
            return 0
        fi
        
        log "等待 $service_name 服务... (尝试 $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "$service_name 服务启动超时"
    return 1
}

# 检查环境变量
check_environment() {
    log "检查环境变量..."
    
    # 必需的环境变量
    local required_vars=(
        "API_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "缺少必需的环境变量: $var"
            exit 1
        fi
    done
    
    # 可选环境变量的默认值
    export MEM0_EMBEDDER_PROVIDER=${MEM0_EMBEDDER_PROVIDER:-"sentence_transformers"}
    export MEM0_EMBEDDER_MODEL=${MEM0_EMBEDDER_MODEL:-"shibing624/text2vec-base-chinese"}
    export MEM0_VECTOR_STORE_PROVIDER=${MEM0_VECTOR_STORE_PROVIDER:-"chroma"}
    export APP_HOST=${APP_HOST:-"0.0.0.0"}
    export APP_PORT=${APP_PORT:-"8000"}
    export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
    
    log "环境变量检查完成"
}

# 等待依赖服务
wait_for_dependencies() {
    log "等待依赖服务启动..."
    
    # 等待PostgreSQL (如果配置了)
    if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
        local pg_host=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        local pg_port=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        wait_for_service "$pg_host" "$pg_port" "PostgreSQL"
    fi
    
    # 等待Redis (如果配置了)
    if [ -n "$REDIS_HOST" ]; then
        local redis_port=${REDIS_PORT:-6379}
        wait_for_service "$REDIS_HOST" "$redis_port" "Redis"
    fi
    
    # 等待ChromaDB (如果配置了)
    if [ -n "$CHROMA_HOST" ]; then
        local chroma_port=${CHROMA_PORT:-8000}
        wait_for_service "$CHROMA_HOST" "$chroma_port" "ChromaDB"
    fi
}

# 初始化数据目录
init_data_directories() {
    log "初始化数据目录..."
    
    # 创建必要的数据目录
    mkdir -p /app/data/chroma
    mkdir -p /app/data/huggingface
    mkdir -p /app/data/transformers
    mkdir -p /app/logs
    
    # 设置环境变量
    export HF_HOME=/app/data/huggingface
    export TRANSFORMERS_CACHE=/app/data/transformers
    export CHROMA_PERSIST_DIRECTORY=${CHROMA_PERSIST_DIRECTORY:-"/app/data/chroma"}
    
    log "数据目录初始化完成"
}

# 运行健康检查
run_health_check() {
    log "运行启动健康检查..."
    
    if python check_health.py --no-api --config /dev/null; then
        log "健康检查通过"
    else
        warn "健康检查发现问题，但继续启动服务"
    fi
}

# 启动前预热
warmup_services() {
    log "预热服务..."
    
    # 预加载嵌入模型
    python -c "
import os
from sentence_transformers import SentenceTransformer
try:
    model_name = os.getenv('MEM0_EMBEDDER_MODEL', 'shibing624/text2vec-base-chinese')
    print(f'预加载嵌入模型: {model_name}')
    model = SentenceTransformer(model_name)
    print('模型预加载完成')
except Exception as e:
    print(f'模型预加载失败: {e}')
" || warn "模型预加载失败"
    
    log "服务预热完成"
}

# 主函数
main() {
    log "=== Mem0 生产环境启动 ==="
    
    # 检查环境
    check_environment
    
    # 初始化目录
    init_data_directories
    
    # 等待依赖服务
    wait_for_dependencies
    
    # 运行健康检查
    run_health_check
    
    # 预热服务
    warmup_services
    
    log "准备启动应用服务..."
    log "命令: $@"
    
    # 执行传入的命令
    exec "$@"
}

# 信号处理
cleanup() {
    log "接收到终止信号，正在优雅关闭..."
    # 这里可以添加清理逻辑
    exit 0
}

trap cleanup SIGTERM SIGINT

# 运行主函数
main "$@"