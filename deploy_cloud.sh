#!/bin/bash

# Mem0 API 云服务器一键部署脚本
# 支持 Ubuntu/CentOS/Debian 系统

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
☁️ Mem0 API 云服务器部署脚本

用法: $0 [选项]

选项:
    -d, --domain        域名 (例如: api.example.com)
    -e, --email         Let's Encrypt 证书邮箱
    -p, --port          API 端口 [默认: 8000]
    -m, --monitoring    启用监控服务
    -u, --update        更新系统包
    -c, --clean         清理安装
    -h, --help          显示帮助信息

示例:
    # 基本部署
    $0 --domain api.example.com --email admin@example.com

    # 包含监控的完整部署
    $0 --domain api.example.com --email admin@example.com --monitoring

    # 更新系统并清理安装
    $0 --update --clean --domain api.example.com --email admin@example.com

环境变量:
    OPENAI_API_KEY      OpenAI API 密钥 (必需)
    MEM0_API_KEY        Mem0 API 密钥 (可选)
    GITHUB_TOKEN        GitHub 访问令牌 (用于私有仓库)

注意:
    - 需要 root 权限或 sudo 权限
    - 确保防火墙开放 80, 443 端口
    - 域名需要解析到服务器 IP
EOF
}

# 默认参数
DOMAIN=""
EMAIL=""
PORT="8000"
MONITORING=""
UPDATE=""
CLEAN=""

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

# 验证必需参数
if [[ -z "$DOMAIN" ]]; then
    log_error "域名参数是必需的，使用 --domain 指定"
    exit 1
fi

if [[ -z "$EMAIL" ]]; then
    log_error "邮箱参数是必需的，使用 --email 指定"
    exit 1
fi

# 检查环境变量
if [[ -z "$OPENAI_API_KEY" ]]; then
    log_error "OPENAI_API_KEY 环境变量未设置"
    log_error "请设置: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

log_info "☁️ Mem0 API 云服务器部署开始"
log_info "目标域名: $DOMAIN"
log_info "管理邮箱: $EMAIL"

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
        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*)
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
            lsb-release
    else
        $PKG_INSTALL \
            curl \
            wget \
            git \
            unzip \
            yum-utils \
            device-mapper-persistent-data \
            lvm2
    fi
    
    log_info "✅ 基础依赖安装完成"
}

# 安装 Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker 已安装，跳过安装"
        return
    fi
    
    log_step "安装 Docker..."
    
    if [[ "$PKG_MANAGER" == "apt-get" ]]; then
        # Ubuntu/Debian
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        apt-get update
        $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        # CentOS/RHEL
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    # 启动 Docker 服务
    systemctl start docker
    systemctl enable docker
    
    # 添加当前用户到 docker 组
    usermod -aG docker $USER || true
    
    log_info "✅ Docker 安装完成"
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

# 安装 Nginx
install_nginx() {
    if command -v nginx &> /dev/null; then
        log_info "Nginx 已安装，跳过安装"
        return
    fi
    
    log_step "安装 Nginx..."
    
    $PKG_INSTALL nginx
    
    # 启动 Nginx 服务
    systemctl start nginx
    systemctl enable nginx
    
    log_info "✅ Nginx 安装完成"
}

# 安装 Certbot (Let's Encrypt)
install_certbot() {
    if command -v certbot &> /dev/null; then
        log_info "Certbot 已安装，跳过安装"
        return
    fi
    
    log_step "安装 Certbot..."
    
    if [[ "$PKG_MANAGER" == "apt-get" ]]; then
        $PKG_INSTALL snapd
        snap install core; snap refresh core
        snap install --classic certbot
        ln -sf /snap/bin/certbot /usr/bin/certbot
    else
        $PKG_INSTALL epel-release
        $PKG_INSTALL certbot python3-certbot-nginx
    fi
    
    log_info "✅ Certbot 安装完成"
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙..."
    
    # 检测防火墙类型
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian UFW
        ufw --force enable
        ufw allow ssh
        ufw allow 80
        ufw allow 443
        ufw allow $PORT
        log_info "✅ UFW 防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewalld
        systemctl start firewalld
        systemctl enable firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-port=$PORT/tcp
        firewall-cmd --reload
        log_info "✅ Firewalld 防火墙配置完成"
    else
        log_warn "未检测到防火墙，请手动配置端口 80, 443, $PORT"
    fi
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
    
    if [[ -n "$GITHUB_TOKEN" ]]; then
        REPO_URL="https://$GITHUB_TOKEN@github.com/mem0ai/mem0.git"
    fi
    
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
# 生产环境配置
ENV=production
DEBUG=false
LOG_LEVEL=info

# API 配置
API_HOST=0.0.0.0
API_PORT=$PORT
DOMAIN_NAME=$DOMAIN

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
ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN
EOF

    # 设置文件权限
    chmod 600 .env
    
    log_info "✅ 环境变量文件创建完成"
}

# 创建 Nginx 配置
create_nginx_config() {
    log_step "创建 Nginx 配置..."
    
    cat > /etc/nginx/sites-available/mem0-api << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # 重定向到 HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL 配置 (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_private_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 5m;
    
    # 安全头
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 日志
    access_log /var/log/nginx/mem0-api.access.log;
    error_log /var/log/nginx/mem0-api.error.log;
    
    # 反向代理到 API
    location / {
        proxy_pass http://localhost:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://localhost:$PORT/health;
        access_log off;
    }
    
    # 静态文件缓存
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # 启用站点
    if [[ -d "/etc/nginx/sites-enabled" ]]; then
        ln -sf /etc/nginx/sites-available/mem0-api /etc/nginx/sites-enabled/
    else
        # CentOS 风格配置
        cat > /etc/nginx/conf.d/mem0-api.conf < /etc/nginx/sites-available/mem0-api
    fi
    
    # 禁用默认站点
    if [[ -f "/etc/nginx/sites-enabled/default" ]]; then
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    log_info "✅ Nginx 配置创建完成"
}

# 获取 SSL 证书
obtain_ssl_certificate() {
    log_step "获取 SSL 证书..."
    
    # 临时停止 Nginx
    systemctl stop nginx
    
    # 获取证书
    certbot certonly --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --domains "$DOMAIN"
    
    # 重启 Nginx
    systemctl start nginx
    
    # 设置自动续期
    crontab -l 2>/dev/null | grep -v certbot | crontab -
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --reload-hook 'systemctl reload nginx'") | crontab -
    
    log_info "✅ SSL 证书获取完成"
}

# 部署应用
deploy_application() {
    log_step "部署应用..."
    
    local compose_args="--profile production"
    
    if [[ "$MONITORING" == "true" ]]; then
        compose_args="$compose_args --profile monitoring"
    fi
    
    # 构建并启动服务
    docker-compose -f docker-compose.prod.yml $compose_args up --build -d
    
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
        docker-compose -f docker-compose.prod.yml logs --tail=50
        exit 1
    fi
}

# 配置系统服务
configure_systemd() {
    log_step "配置系统服务..."
    
    cat > /etc/systemd/system/mem0-api.service << EOF
[Unit]
Description=Mem0 API Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR/tests/apis
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mem0-api.service
    
    log_info "✅ 系统服务配置完成"
}

# 显示部署信息
show_deployment_info() {
    log_info "🎉 Mem0 API 云服务器部署完成!"
    log_info ""
    log_info "🌐 访问地址:"
    log_info "  • API 服务: https://$DOMAIN"
    log_info "  • API 文档: https://$DOMAIN/docs"
    log_info "  • 健康检查: https://$DOMAIN/health"
    
    if [[ "$MONITORING" == "true" ]]; then
        log_info "  • Prometheus: https://$DOMAIN:9090"
        log_info "  • Grafana: https://$DOMAIN:3000"
    fi
    
    log_info ""
    log_info "📁 项目目录: $PROJECT_DIR/tests/apis"
    log_info ""
    log_info "🔧 管理命令:"
    log_info "  • 查看状态: systemctl status mem0-api"
    log_info "  • 查看日志: docker-compose -f docker-compose.prod.yml logs"
    log_info "  • 重启服务: systemctl restart mem0-api"
    log_info "  • 更新部署: cd $PROJECT_DIR/tests/apis && ./deploy.sh --env prod --build"
    
    log_info ""
    log_info "🔐 SSL 证书:"
    log_info "  • 自动续期已配置"
    log_info "  • 手动续期: certbot renew"
    
    log_info ""
    log_info "⚠️ 重要提醒:"
    log_info "  • 请定期备份 $PROJECT_DIR/data 目录"
    log_info "  • 监控服务器资源使用情况"
    log_info "  • 定期更新 Docker 镜像"
}

# 主函数
main() {
    # 系统检查和准备
    detect_system
    check_permissions
    
    # 系统更新
    update_system
    
    # 安装依赖
    install_dependencies
    install_docker
    install_docker_compose
    install_nginx
    install_certbot
    
    # 配置系统
    configure_firewall
    
    # 项目部署
    create_project_directory
    download_project_files
    create_env_file
    
    # Web 服务器配置
    create_nginx_config
    obtain_ssl_certificate
    
    # 应用部署
    deploy_application
    wait_for_services
    
    # 系统服务配置
    configure_systemd
    
    # 显示部署信息
    show_deployment_info
}

# 捕获中断信号
trap 'log_error "部署被中断"; exit 1' INT TERM

# 执行主函数
main "$@"