#!/bin/bash

# Mem0 云服务器初始化脚本
# 适用于 Ubuntu 20.04/22.04 和 CentOS 7/8

set -e

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

# 配置变量
DEPLOY_USER="deploy"
DEPLOY_HOME="/home/$DEPLOY_USER"
APP_DIR="/opt/mem0"
DOCKER_COMPOSE_VERSION="2.24.0"

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此脚本需要root权限运行"
        error "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    log "检测操作系统..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        error "无法检测操作系统"
        exit 1
    fi
    
    case $OS in
        ubuntu)
            log "检测到 Ubuntu $VER"
            PACKAGE_MANAGER="apt"
            ;;
        centos|rhel|anolis)
            log "检测到 CentOS/RHEL $VER"
            PACKAGE_MANAGER="yum"
            ;;
        alinux|alios|alibaba)
            log "检测到 Alibaba Cloud Linux $VER"
            PACKAGE_MANAGER="yum"
            ;;
        rocky|almalinux)
            log "检测到 Rocky/AlmaLinux $VER"
            PACKAGE_MANAGER="yum"
            ;;
        fedora)
            log "检测到 Fedora $VER"
            PACKAGE_MANAGER="dnf"
            ;;
        *)
            # 尝试检测包管理器
            if command -v yum &> /dev/null; then
                warn "未识别的系统 $OS，但检测到yum，尝试以CentOS方式处理"
                PACKAGE_MANAGER="yum"
            elif command -v apt-get &> /dev/null; then
                warn "未识别的系统 $OS，但检测到apt，尝试以Ubuntu方式处理"
                PACKAGE_MANAGER="apt"
            else
                error "不支持的操作系统: $OS"
                exit 1
            fi
            ;;
    esac
}

# 更新系统
update_system() {
    log "更新系统包..."
    
    case $PACKAGE_MANAGER in
        apt)
            apt-get update -y
            apt-get upgrade -y
            apt-get install -y curl wget git unzip vim htop iotop nload ufw fail2ban
            ;;
        yum)
            yum update -y
            yum install -y epel-release
            yum install -y curl wget git unzip vim htop iotop nload firewalld fail2ban
            ;;
    esac
}

# 配置防火墙
configure_firewall() {
    log "配置防火墙..."
    
    case $PACKAGE_MANAGER in
        apt)
            ufw --force reset
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow ssh
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 8000/tcp  # Mem0 API
            ufw --force enable
            ;;
        yum)
            systemctl enable firewalld
            systemctl start firewalld
            firewall-cmd --permanent --zone=public --add-service=ssh
            firewall-cmd --permanent --zone=public --add-service=http
            firewall-cmd --permanent --zone=public --add-service=https
            firewall-cmd --permanent --zone=public --add-port=8000/tcp
            firewall-cmd --reload
            ;;
    esac
}

# 配置SSH安全
configure_ssh() {
    log "配置SSH安全..."
    
    # 备份原始配置
    if [ ! -f /etc/ssh/sshd_config.backup ]; then
        cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    fi
    
    # 检查系统是否支持sshd_config.d目录
    if [ -d /etc/ssh/sshd_config.d ]; then
        log "使用 sshd_config.d 目录配置SSH"
        cat > /etc/ssh/sshd_config.d/99-mem0.conf << 'EOF'
# Mem0 SSH安全配置
Protocol 2
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 600
ClientAliveCountMax 3
EOF
    else
        log "直接修改 sshd_config 文件"
        # 直接在主配置文件中添加安全配置
        if ! grep -q "# Mem0 SSH Config" /etc/ssh/sshd_config; then
            cat >> /etc/ssh/sshd_config << 'EOF'

# Mem0 SSH Config
PasswordAuthentication no
ChallengeResponseAuthentication no
MaxAuthTries 3
ClientAliveInterval 600
ClientAliveCountMax 3
EOF
        fi
    fi
    
    # 验证配置文件语法
    if sshd -t; then
        log "SSH配置验证成功"
        systemctl restart sshd || log "SSH服务重启失败，但继续安装"
    else
        warn "SSH配置验证失败，跳过SSH重启"
    fi
}

# 创建部署用户
create_deploy_user() {
    log "创建部署用户..."
    
    if id "$DEPLOY_USER" &>/dev/null; then
        warn "用户 $DEPLOY_USER 已存在"
    else
        useradd -m -s /bin/bash $DEPLOY_USER
        usermod -aG sudo $DEPLOY_USER
        log "创建用户 $DEPLOY_USER 成功"
    fi
    
    # 创建SSH目录
    mkdir -p $DEPLOY_HOME/.ssh
    chmod 700 $DEPLOY_HOME/.ssh
    touch $DEPLOY_HOME/.ssh/authorized_keys
    chmod 600 $DEPLOY_HOME/.ssh/authorized_keys
    chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_HOME/.ssh
    
    # 允许sudo免密码
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$DEPLOY_USER
    chmod 440 /etc/sudoers.d/$DEPLOY_USER
}

# 安装Docker
install_docker() {
    log "安装Docker..."
    
    # 检查Docker是否已安装
    if command -v docker &> /dev/null; then
        warn "Docker已安装，跳过安装"
        return
    fi
    
    case $PACKAGE_MANAGER in
        apt)
            # 安装依赖
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            # 添加Docker官方GPG密钥
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # 添加Docker仓库
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # 安装Docker
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
            
        yum)
            # 安装依赖
            yum install -y yum-utils
            
            # 添加Docker仓库
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # 安装Docker
            yum install -y docker-ce docker-ce-cli containerd.io
            ;;
    esac
    
    # 启动Docker服务
    systemctl enable docker
    systemctl start docker
    
    # 将部署用户添加到docker组
    usermod -aG docker $DEPLOY_USER
    
    log "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log "安装Docker Compose..."
    
    # 检查是否已安装
    if command -v docker-compose &> /dev/null; then
        warn "Docker Compose已安装，跳过安装"
        return
    fi
    
    # 下载并安装Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # 创建软链接
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log "Docker Compose安装完成"
}

# 安装Nginx
install_nginx() {
    log "安装Nginx..."
    
    case $PACKAGE_MANAGER in
        apt)
            apt-get install -y nginx
            ;;
        yum)
            yum install -y nginx
            ;;
    esac
    
    systemctl enable nginx
    systemctl start nginx
    
    log "Nginx安装完成"
}

# 安装监控工具
install_monitoring() {
    log "安装监控工具..."
    
    case $PACKAGE_MANAGER in
        apt)
            apt-get install -y htop iotop nload nethogs tree jq
            ;;
        yum)
            yum install -y htop iotop nload nethogs tree jq
            ;;
    esac
    
    # 安装node_exporter（Prometheus监控）
    if ! command -v node_exporter &> /dev/null; then
        log "安装node_exporter..."
        NODE_EXPORTER_VERSION="1.7.0"
        wget https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
        tar xvfz node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
        mv node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
        rm -rf node_exporter-*
        
        # 创建systemd服务
        cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=nobody
Group=nobody
Type=simple
ExecStart=/usr/local/bin/node_exporter
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable node_exporter
        systemctl start node_exporter
    fi
}

# 创建应用目录
create_app_directory() {
    log "创建应用目录..."
    
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/{config,logs,data,backups}
    chown -R $DEPLOY_USER:$DEPLOY_USER $APP_DIR
    
    log "应用目录创建完成: $APP_DIR"
}

# 配置日志轮转
configure_logrotate() {
    log "配置日志轮转..."
    
    cat > /etc/logrotate.d/mem0 << 'EOF'
/opt/mem0/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        docker-compose -f /opt/mem0/docker-compose.prod.yml restart mem0-api || true
    endscript
}

/opt/mem0/logs/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        docker-compose -f /opt/mem0/docker-compose.prod.yml restart nginx || true
    endscript
}
EOF
}

# 配置备份脚本
setup_backup() {
    log "设置备份脚本..."
    
    cat > /usr/local/bin/mem0-backup.sh << 'EOF'
#!/bin/bash

# Mem0备份脚本
BACKUP_DIR="/opt/mem0/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
echo "备份PostgreSQL数据库..."
docker-compose -f /opt/mem0/docker-compose.prod.yml exec -T postgres pg_dump -U mem0 mem0_db | gzip > $BACKUP_DIR/postgres_${DATE}.sql.gz

# 备份向量数据库
echo "备份ChromaDB数据..."
tar -czf $BACKUP_DIR/chroma_${DATE}.tar.gz -C /opt/mem0/data chroma/

# 备份配置文件
echo "备份配置文件..."
tar -czf $BACKUP_DIR/config_${DATE}.tar.gz -C /opt/mem0 config/ .env docker-compose.prod.yml

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR"
EOF
    
    chmod +x /usr/local/bin/mem0-backup.sh
    
    # 添加定时任务
    echo "0 2 * * * root /usr/local/bin/mem0-backup.sh > /var/log/mem0-backup.log 2>&1" >> /etc/crontab
}

# 设置系统优化
optimize_system() {
    log "优化系统配置..."
    
    # 内核参数优化
    cat > /etc/sysctl.d/99-mem0.conf << 'EOF'
# Mem0系统优化配置
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5
net.core.somaxconn=65535
net.core.netdev_max_backlog=5000
net.ipv4.tcp_max_syn_backlog=65535
net.ipv4.tcp_fin_timeout=30
net.ipv4.tcp_keepalive_time=1200
net.ipv4.tcp_max_tw_buckets=5000
net.ipv4.ip_local_port_range=1024 65535
fs.file-max=2097152
EOF
    
    sysctl -p /etc/sysctl.d/99-mem0.conf
    
    # 设置文件描述符限制
    cat > /etc/security/limits.d/99-mem0.conf << 'EOF'
# Mem0文件描述符限制
* soft nofile 65535
* hard nofile 65535
root soft nofile 65535
root hard nofile 65535
EOF
}

# 创建健康检查脚本
create_health_check() {
    log "创建健康检查脚本..."
    
    cat > /usr/local/bin/mem0-health.sh << 'EOF'
#!/bin/bash

# Mem0健康检查脚本
APP_URL="http://localhost:8000"
LOG_FILE="/var/log/mem0-health.log"

# 检查API服务
check_api() {
    if curl -f -s $APP_URL/health > /dev/null; then
        echo "$(date): API服务正常" >> $LOG_FILE
        return 0
    else
        echo "$(date): API服务异常" >> $LOG_FILE
        return 1
    fi
}

# 检查Docker容器
check_containers() {
    failed_containers=$(docker-compose -f /opt/mem0/docker-compose.prod.yml ps --services --filter "status=exited")
    if [ -n "$failed_containers" ]; then
        echo "$(date): 发现停止的容器: $failed_containers" >> $LOG_FILE
        return 1
    else
        echo "$(date): 所有容器运行正常" >> $LOG_FILE
        return 0
    fi
}

# 主检查函数
main() {
    cd /opt/mem0
    
    if check_api && check_containers; then
        exit 0
    else
        echo "$(date): 健康检查失败，尝试重启服务" >> $LOG_FILE
        docker-compose -f docker-compose.prod.yml restart
        sleep 30
        
        if check_api; then
            echo "$(date): 服务重启成功" >> $LOG_FILE
        else
            echo "$(date): 服务重启失败，需要人工介入" >> $LOG_FILE
        fi
    fi
}

main
EOF
    
    chmod +x /usr/local/bin/mem0-health.sh
    
    # 添加定时健康检查
    echo "*/5 * * * * root /usr/local/bin/mem0-health.sh" >> /etc/crontab
}

# 主安装流程
main() {
    echo -e "${GREEN}"
    cat << 'EOF'
 __  __                 ___  
|  \/  | ___ _ __ ___   / _ \ 
| |\/| |/ _ \ '_ ` _ \ | | | |
| |  | |  __/ | | | | | |_| |
|_|  |_|\___|_| |_| |_|\___/ 
                             
Mem0 云服务器初始化脚本
EOF
    echo -e "${NC}"
    
    log "开始初始化云服务器..."
    
    check_root
    detect_os
    update_system
    configure_firewall
    create_deploy_user
    configure_ssh
    install_docker
    install_docker_compose
    install_nginx
    install_monitoring
    create_app_directory
    configure_logrotate
    setup_backup
    optimize_system
    create_health_check
    
    log "=== 初始化完成 ==="
    log "部署用户: $DEPLOY_USER"
    log "应用目录: $APP_DIR"
    log "请确保将您的SSH公钥添加到: $DEPLOY_HOME/.ssh/authorized_keys"
    
    echo -e "${YELLOW}"
    cat << 'EOF'
下一步操作:
1. 将您的SSH公钥添加到deploy用户
2. 配置GitHub Actions Secrets
3. 推送代码触发自动部署

GitHub Actions需要的Secrets:
- STAGING_SSH_PRIVATE_KEY / PRODUCTION_SSH_PRIVATE_KEY
- STAGING_SSH_HOST / PRODUCTION_SSH_HOST
- STAGING_SSH_USER / PRODUCTION_SSH_USER
- API_SECRET_KEY
- POSTGRES_PASSWORD
- 其他API密钥
EOF
    echo -e "${NC}"
}

# 错误处理
trap 'error "安装过程中出现错误，请检查日志"; exit 1' ERR

# 检查参数
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Mem0 云服务器初始化脚本"
    echo
    echo "用法: sudo $0"
    echo
    echo "此脚本将安装和配置以下组件:"
    echo "- Docker & Docker Compose"
    echo "- Nginx"
    echo "- 防火墙配置"
    echo "- 部署用户"
    echo "- 监控工具"
    echo "- 备份脚本"
    echo "- 健康检查"
    echo
    exit 0
fi

# 运行主安装流程
main