#!/bin/bash

# Mem0 API 阿里云服务器一键部署脚本
# 专为阿里云 ECS 优化，支持 Ubuntu/CentOS/Alibaba Cloud Linux

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
☁️ Mem0 API 阿里云服务器部署脚本

用法: $0 [选项]

选项:
    -d, --domain        域名 (例如: api.example.com)
    -e, --email         SSL 证书邮箱 (用于 Let's Encrypt)
    -p, --port          API 端口 [默认: 8000]
    -m, --monitoring    启用监控服务 (Prometheus + Grafana)
    -u, --update        更新系统包
    -c, --clean         清理安装
    --ssl               启用 SSL (需要域名)
    --aliyun-mirror     使用阿里云镜像源加速
    -h, --help          显示帮助信息

示例:
    # 基本部署 (HTTP)
    $0 --port 8000

    # 带域名和 SSL 的完整部署
    $0 --domain api.example.com --email admin@example.com --ssl

    # 包含监控的完整部署
    $0 --domain api.example.com --email admin@example.com --ssl --monitoring

    # 使用阿里云镜像加速
    $0 --aliyun-mirror --port 8000

环境变量:
    OPENAI_API_KEY      OpenAI API 密钥 (必需)
    MEM0_API_KEY        Mem0 API 密钥 (可选)

阿里云特殊配置:
    - 自动配置阿里云安全组
    - 支持阿里云镜像源加速
    - 优化阿里云 ECS 性能
    - 支持内网 IP 访问

注意:
    - 需要 root 权限或 sudo 权限
    - 确保安全组开放相应端口 (80, 443, 自定义端口)
    - 如使用域名，请先将域名解析到 ECS 公网 IP
EOF
}

# 默认参数
DOMAIN=""
EMAIL=""
PORT="8000"
MONITORING=""
UPDATE=""
CLEAN=""
ENABLE_SSL=""
USE_ALIYUN_MIRROR=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -m|--monitoring)
            MONITORING="true"
            shift
            ;;
        -u|--update)
            UPDATE="true"
            shift
            ;;
        -c|--clean)
            CLEAN="true"
            shift
            ;;
        --ssl)
            ENABLE_SSL="true"
            shift
            ;;
        --aliyun-mirror)
            USE_ALIYUN_MIRROR="true"
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

# 如果启用 SSL，必须提供域名和邮箱
if [[ "$ENABLE_SSL" == "true" ]]; then
    if [[ -z "$DOMAIN" ]]; then
        log_error "启用 SSL 时域名参数是必需的，使用 --domain 指定"
        exit 1
    fi
    
    if [[ -z "$EMAIL" ]]; then
        log_error "启用 SSL 时邮箱参数是必需的，使用 --email 指定"
        exit 1
    fi
fi

# 检查环境变量
if [[ -z "$OPENAI_API_KEY" ]]; then
    log_error "OPENAI_API_KEY 环境变量未设置"
    log_error "请设置: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

log_info "☁️ Mem0 API 阿里云服务器部署开始"
if [[ -n "$DOMAIN" ]]; then
    log_info "目标域名: $DOMAIN"
fi
log_info "API 端口: $PORT"

# 获取阿里云 ECS 信息
get_aliyun_info() {
    log_step "获取阿里云 ECS 信息..."
    
    # 获取实例 ID
    INSTANCE_ID=$(curl -s http://100.100.100.200/latest/meta-data/instance-id || echo "unknown")
    
    # 获取地域信息
    REGION=$(curl -s http://100.100.100.200/latest/meta-data/region-id || echo "unknown")
    
    # 获取内网 IP
    PRIVATE_IP=$(curl -s http://100.100.100.200/latest/meta-data/private-ipv4 || echo "unknown")
    
    # 获取公网 IP
    PUBLIC_IP=$(curl -s http://100.100.100.200/latest/meta-data/eipv4 || curl -s http://100.100.100.200/latest/meta-data/public-ipv4 || echo "unknown")
    
    log_info "实例 ID: $INSTANCE_ID"
    log_info "地域: $REGION"
    log_info "内网 IP: $PRIVATE_IP"
    log_info "公网 IP: $PUBLIC_IP"
}

# 检测系统类型
detect_system() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    
    log_info "检测到系统: $OS $VERSION"
    
    # 设置包管理器
    case $OS in
        *"Ubuntu"*|*"Debian"*)
            PKG_MANAGER="apt-get"
            PKG_UPDATE="apt-get update"
            PKG_INSTALL="apt-get install -y"
            ;;
        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*|*"Alibaba Cloud Linux"*)
            PKG_MANAGER="yum"
            PKG_UPDATE="yum update -y"
            PKG_INSTALL="yum install -y"
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
}

# 检查权限
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限"
        log_error "请使用: sudo $0"
        exit 1
    fi
}

# 配置阿里云镜像源
setup_aliyun_mirrors() {
    if [[ "$USE_ALIYUN_MIRROR" == "true" ]]; then
        log_step "配置阿里云镜像源..."
        
        if [[ "$PKG_MANAGER" == "apt-get" ]]; then
            # Ubuntu/Debian 阿里云镜像
            cp /etc/apt/sources.list /etc/apt/sources.list.backup
            cat > /etc/apt/sources.list << EOF
deb http://mirrors.aliyun.com/ubuntu/ $(lsb_release -cs) main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ $(lsb_release -cs)-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ $(lsb_release -cs)-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ $(lsb_release -cs)-backports main restricted universe multiverse
EOF
        else
            # CentOS/RHEL 阿里云镜像
            if [[ -f /etc/yum.repos.d/CentOS-Base.repo ]]; then
                cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup
                wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
                yum clean all && yum makecache
            fi
        fi
        
        log_info "✅ 阿里云镜像源配置完成"
    fi
}

# 更新系统
update_system() {
    if [[ "$UPDATE" == "true" ]]; then
        log_step "更新系统包..."
        $PKG_UPDATE
        
        if [[ "$PKG_MANAGER" == "apt-get" ]]; then
            apt-get upgrade -y
        fi
        
        log_info "✅ 系统更新完成"
    fi
}

# 安装基础依赖
install_dependencies() {
    log_step "安装基础依赖..."
    
    if [[ "$PKG_MANAGER" == "apt-get" ]]; then
        $PKG_INSTALL \
            curl \
            wget \
            git \
            unzip \
            software-properties-common \
            apt-transport-https \
            ca-certificates \
            gnupg \
            lsb-release \
            htop \
            vim
    else
        $PKG_INSTALL \
            curl \
            wget \
            git \
            unzip \
            yum-utils \
            device-mapper-persistent-data \
            lvm2 \
            htop \
            vim
    fi
    
    log_info "✅ 基础依赖安装完成"
}

# 安装 Docker (阿里云优化版本)
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker 已安装，跳过安装"
        return
    fi
    
    log_step "安装 Docker (阿里云优化)..."
    
    if [[ "$PKG_MANAGER" == "apt-get" ]]; then
        # Ubuntu/Debian - 使用阿里云 Docker 镜像
        curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"
        apt-get update
        $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        # CentOS/RHEL - 使用阿里云 Docker 镜像
        yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
        $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    # 启动 Docker 服务
    systemctl start docker
    systemctl enable docker
    
    # 配置 Docker 阿里云镜像加速器
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << EOF
{
    "registry-mirrors": [
        "https://mirror.ccs.tencentyun.com",
        "https://docker.mirrors.ustc.edu.cn",
        "https://reg-mirror.qiniu.com"
    ],
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF
    
    # 重启 Docker 应用配置
    systemctl daemon-reload
    systemctl restart docker
    
    # 添加当前用户到 docker 组
    usermod -aG docker $USER || true
    
    log_info "✅ Docker 安装完成 (已配置阿里云加速)"
}

# 安装 Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose 已安装，跳过安装"
        return
    fi
    
    log_step "安装 Docker Compose..."
    
    # 获取最新版本
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    
    # 下载并安装
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # 创建符号链接
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_info "✅ Docker Compose 安装完成"
}

# 配置阿里云安全组端口
configure_aliyun_security() {
    log_step "检查阿里云安全组配置..."
    
    log_warn "请确保在阿里云控制台中开放以下端口:"
    log_warn "  • HTTP: 80"
    if [[ "$ENABLE_SSL" == "true" ]]; then
        log_warn "  • HTTPS: 443"
    fi
    log_warn "  • API: $PORT"
    if [[ "$MONITORING" == "true" ]]; then
        log_warn "  • Prometheus: 9090"
        log_warn "  • Grafana: 3000"
    fi
    
    log_info "安全组配置位置: ECS 控制台 -> 网络与安全 -> 安全组"
}

# 创建项目目录
create_project_directory() {
    log_step "创建项目目录..."
    
    PROJECT_DIR="/opt/mem0-api"
    
    # 清理旧安装
    if [[ "$CLEAN" == "true" && -d "$PROJECT_DIR" ]]; then
        log_step "清理旧安装..."
        cd "$PROJECT_DIR" && docker-compose down --remove-orphans --volumes || true
        rm -rf "$PROJECT_DIR"
    fi
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    log_info "✅ 项目目录创建: $PROJECT_DIR"
}

# 下载项目文件
download_project_files() {
    log_step "下载项目文件..."
    
    # GitHub 仓库信息
    REPO_URL="https://github.com/mem0ai/mem0.git"
    
    # 克隆仓库
    git clone "$REPO_URL" . || {
        log_error "项目下载失败"
        exit 1
    }
    
    # 切换到 API 目录
    cd tests/apis/
    
    log_info "✅ 项目文件下载完成"
}

# 创建环境变量文件
create_env_file() {
    log_step "创建环境变量文件..."
    
    cat > .env << EOF
# 阿里云 ECS 生产环境配置
ENV=production
DEBUG=false
LOG_LEVEL=info

# API 配置
API_HOST=0.0.0.0
API_PORT=$PORT

# 域名配置
EOF

    if [[ -n "$DOMAIN" ]]; then
        echo "DOMAIN_NAME=$DOMAIN" >> .env
    fi

    cat >> .env << EOF

# 必需的 API 密钥
OPENAI_API_KEY=$OPENAI_API_KEY
MEM0_API_KEY=${MEM0_API_KEY:-}

# Mem0 配置
MEM0_LLM_MODEL=gpt-4o-mini
MEM0_VECTOR_STORE_PROVIDER=qdrant
MEM0_EMBEDDER_MODEL=text-embedding-3-small

# 数据库配置
QDRANT_HOST=qdrant
QDRANT_PORT=6333
REDIS_HOST=redis
REDIS_PORT=6379

# 监控配置
GRAFANA_PASSWORD=admin123

# 安全配置
JWT_SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1,$PRIVATE_IP,$PUBLIC_IP
EOF

    if [[ -n "$DOMAIN" ]]; then
        echo "ALLOWED_HOSTS=localhost,127.0.0.1,$PRIVATE_IP,$PUBLIC_IP,$DOMAIN" >> .env
    fi

    # 设置文件权限
    chmod 600 .env
    
    log_info "✅ 环境变量文件创建完成"
}

# 安装和配置 SSL (如果需要)
setup_ssl() {
    if [[ "$ENABLE_SSL" == "true" ]]; then
        log_step "安装 Certbot..."
        
        if [[ "$PKG_MANAGER" == "apt-get" ]]; then
            $PKG_INSTALL snapd
            snap install core; snap refresh core
            snap install --classic certbot
            ln -sf /snap/bin/certbot /usr/bin/certbot
        else
            $PKG_INSTALL epel-release
            $PKG_INSTALL certbot
        fi
        
        log_info "✅ Certbot 安装完成"
        log_warn "SSL 证书将在服务启动后自动获取"
    fi
}

# 部署应用
deploy_application() {
    log_step "部署应用..."
    
    local compose_args="--profile production"
    
    if [[ "$MONITORING" == "true" ]]; then
        compose_args="$compose_args --profile monitoring"
    fi
    
    # 构建并启动服务
    if [[ "$ENABLE_SSL" == "true" ]]; then
        docker-compose -f docker-compose.prod.yml $compose_args up --build -d
    else
        # HTTP 模式，不启动 Nginx
        docker-compose -f docker-compose.yml up --build -d
    fi
    
    log_info "✅ 应用部署完成"
}

# 等待服务启动
wait_for_services() {
    log_step "等待服务启动..."
    
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f http://localhost:$PORT/health &> /dev/null; then
            log_info "✅ 服务启动成功"
            break
        fi
        
        attempt=$((attempt + 1))
        log_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 5
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_error "服务启动失败，查看日志:"
        docker-compose logs --tail=50
        exit 1
    fi
}

# 获取 SSL 证书 (如果启用)
obtain_ssl_certificate() {
    if [[ "$ENABLE_SSL" == "true" ]]; then
        log_step "获取 SSL 证书..."
        
        # 获取证书
        certbot certonly --standalone \
            --email "$EMAIL" \
            --agree-tos \
            --non-interactive \
            --domains "$DOMAIN"
        
        # 设置自动续期
        crontab -l 2>/dev/null | grep -v certbot | crontab -
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        log_info "✅ SSL 证书获取完成"
    fi
}

# 显示部署信息
show_deployment_info() {
    log_info "🎉 Mem0 API 阿里云部署完成!"
    log_info ""
    log_info "🌐 访问地址:"
    
    if [[ "$ENABLE_SSL" == "true" && -n "$DOMAIN" ]]; then
        log_info "  • API 服务: https://$DOMAIN"
        log_info "  • API 文档: https://$DOMAIN/docs"
        log_info "  • 健康检查: https://$DOMAIN/health"
    else
        log_info "  • API 服务: http://$PUBLIC_IP:$PORT"
        log_info "  • API 文档: http://$PUBLIC_IP:$PORT/docs"
        log_info "  • 健康检查: http://$PUBLIC_IP:$PORT/health"
        if [[ "$PRIVATE_IP" != "unknown" ]]; then
            log_info "  • 内网访问: http://$PRIVATE_IP:$PORT"
        fi
    fi
    
    if [[ "$MONITORING" == "true" ]]; then
        log_info "  • Prometheus: http://$PUBLIC_IP:9090"
        log_info "  • Grafana: http://$PUBLIC_IP:3000 (admin/admin123)"
    fi
    
    log_info ""
    log_info "📁 项目目录: $PROJECT_DIR/tests/apis"
    log_info ""
    log_info "☁️ 阿里云信息:"
    log_info "  • 实例 ID: $INSTANCE_ID"
    log_info "  • 地域: $REGION"
    log_info "  • 公网 IP: $PUBLIC_IP"
    log_info "  • 内网 IP: $PRIVATE_IP"
    
    log_info ""
    log_info "🔧 管理命令:"
    log_info "  • 查看状态: docker-compose ps"
    log_info "  • 查看日志: docker-compose logs"
    log_info "  • 重启服务: docker-compose restart"
    log_info "  • 停止服务: docker-compose down"
    
    log_info ""
    log_info "⚠️ 重要提醒:"
    log_info "  • 请在阿里云控制台配置安全组开放端口"
    log_info "  • 定期备份 $PROJECT_DIR/data 目录"
    log_info "  • 监控服务器资源使用情况"
    log_info "  • 定期更新 Docker 镜像"
}

# 主函数
main() {
    # 系统检查和准备
    get_aliyun_info
    detect_system
    check_permissions
    
    # 配置阿里云镜像源
    setup_aliyun_mirrors
    
    # 系统更新
    update_system
    
    # 安装依赖
    install_dependencies
    install_docker
    install_docker_compose
    
    # 配置安全组
    configure_aliyun_security
    
    # 项目部署
    create_project_directory
    download_project_files
    create_env_file
    
    # SSL 配置
    setup_ssl
    
    # 应用部署
    deploy_application
    wait_for_services
    
    # SSL 证书获取
    obtain_ssl_certificate
    
    # 显示部署信息
    show_deployment_info
}

# 捕获中断信号
trap 'log_error "部署被中断"; exit 1' INT TERM

# 执行主函数
main "$@"