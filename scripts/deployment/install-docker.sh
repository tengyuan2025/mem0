#!/bin/bash

# Docker自动安装脚本（支持多种Linux发行版）
# 包含重试机制和错误处理

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

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        error "无法检测操作系统"
        exit 1
    fi
    
    log "检测到系统: $OS $VER"
}

# 重试函数
retry() {
    local n=1
    local max=3
    local delay=5
    while true; do
        "$@" && break || {
            if [[ $n -lt $max ]]; then
                warn "命令失败，第 $n 次重试..."
                sleep $delay
                ((n++))
            else
                error "命令失败，已重试 $max 次"
                return 1
            fi
        }
    done
}

# 安装Docker - CentOS/RHEL/Alibaba Cloud Linux
install_docker_centos() {
    log "为CentOS/RHEL系统安装Docker..."
    
    # 卸载旧版本
    yum remove -y docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine 2>/dev/null || true
    
    # 安装依赖
    yum install -y yum-utils device-mapper-persistent-data lvm2
    
    # 添加仓库（优先阿里云）
    log "配置Docker仓库..."
    yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo || \
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # 安装Docker
    log "安装Docker CE..."
    retry yum install -y docker-ce docker-ce-cli containerd.io
    
    # 配置镜像加速
    configure_docker_mirror
    
    # 启动Docker
    systemctl enable docker
    systemctl start docker
    
    log "Docker安装完成"
}

# 安装Docker - Ubuntu/Debian
install_docker_debian() {
    log "为Ubuntu/Debian系统安装Docker..."
    
    # 卸载旧版本
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # 更新包索引
    apt-get update
    
    # 安装依赖
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker仓库
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    apt-get update
    retry apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 配置镜像加速
    configure_docker_mirror
    
    # 启动Docker
    systemctl enable docker
    systemctl start docker
    
    log "Docker安装完成"
}

# 配置Docker镜像加速
configure_docker_mirror() {
    log "配置Docker镜像加速..."
    
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF
    
    systemctl daemon-reload
    systemctl restart docker
}

# 安装Docker Compose
install_docker_compose() {
    log "安装Docker Compose..."
    
    # 检查是否已安装
    if command -v docker-compose &>/dev/null; then
        log "Docker Compose已安装: $(docker-compose --version)"
        return 0
    fi
    
    # Docker Compose版本
    COMPOSE_VERSION="2.24.0"
    
    # 下载Docker Compose（带重试）
    local compose_url="https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)"
    
    log "从 $compose_url 下载Docker Compose..."
    
    # 尝试多个下载源
    retry curl -L "$compose_url" -o /tmp/docker-compose || \
    retry curl -L "https://get.daocloud.io/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /tmp/docker-compose || \
    retry wget -O /tmp/docker-compose "$compose_url" || {
        # 如果都失败了，尝试使用pip安装
        warn "下载失败，尝试使用pip安装..."
        pip install docker-compose || {
            error "Docker Compose安装失败"
            return 1
        }
        return 0
    }
    
    # 验证下载文件
    if [ ! -f /tmp/docker-compose ] || [ ! -s /tmp/docker-compose ]; then
        error "下载的Docker Compose文件无效"
        return 1
    fi
    
    # 安装
    mv /tmp/docker-compose /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # 创建软链接
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log "Docker Compose安装完成"
}

# 验证安装
verify_installation() {
    log "验证Docker安装..."
    
    # 确保Docker服务正在运行
    systemctl is-active docker || systemctl start docker
    
    # 验证Docker
    if docker --version; then
        log "✅ Docker已安装: $(docker --version)"
    else
        error "Docker安装失败"
        return 1
    fi
    
    # 验证Docker运行
    if docker ps &>/dev/null; then
        log "✅ Docker运行正常"
    else
        error "Docker无法运行"
        return 1
    fi
    
    # 验证Docker Compose
    if docker-compose --version; then
        log "✅ Docker Compose已安装: $(docker-compose --version)"
    else
        warn "Docker Compose安装失败，但Docker可用"
    fi
    
    # 测试运行
    if docker run --rm hello-world &>/dev/null; then
        log "✅ Docker可以拉取和运行镜像"
    else
        warn "Docker运行测试容器失败"
    fi
}

# 主函数
main() {
    log "开始自动安装Docker..."
    
    # 检测操作系统
    detect_os
    
    # 检查是否已安装
    if command -v docker &>/dev/null && docker ps &>/dev/null; then
        log "Docker已安装并运行正常"
        docker --version
        docker-compose --version 2>/dev/null || install_docker_compose
        exit 0
    fi
    
    # 根据系统类型安装
    case $OS in
        centos|rhel|almalinux|rocky|alinux|alibaba)
            install_docker_centos
            ;;
        ubuntu|debian)
            install_docker_debian
            ;;
        *)
            # 尝试通用安装脚本
            warn "未识别的系统 $OS，尝试通用安装..."
            retry curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun || \
            retry curl -fsSL https://get.docker.com | bash
            configure_docker_mirror
            ;;
    esac
    
    # 安装Docker Compose
    install_docker_compose
    
    # 验证安装
    verify_installation
    
    log "🎉 Docker环境安装完成！"
}

# 运行主函数
main "$@"