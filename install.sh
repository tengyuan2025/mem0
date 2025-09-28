#!/bin/bash

# Mem0 一键安装部署脚本
# 适用于全新环境的快速部署

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 检查操作系统
check_os() {
    log "检查操作系统..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    log "检测到操作系统: $OS"
}

# 检查Python版本
check_python() {
    log "检查Python版本..."
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装，请先安装Python 3.8+"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    required_version="3.8"
    
    if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" == "$required_version" ]]; then
        log "Python版本符合要求: $python_version"
    else
        error "Python版本过低: $python_version，需要3.8+"
        exit 1
    fi
}

# 检查并安装系统依赖
install_system_deps() {
    log "安装系统依赖..."
    
    if [[ "$OS" == "linux" ]]; then
        # 检测Linux发行版
        if command -v apt-get &> /dev/null; then
            log "检测到Ubuntu/Debian系统"
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev
        elif command -v yum &> /dev/null; then
            log "检测到CentOS/RHEL系统"
            sudo yum update -y
            sudo yum install -y python3-pip python3-devel gcc openssl-devel libffi-devel
        elif command -v dnf &> /dev/null; then
            log "检测到Fedora系统"
            sudo dnf update -y
            sudo dnf install -y python3-pip python3-devel gcc openssl-devel libffi-devel
        else
            warn "未知Linux发行版，跳过系统依赖安装"
        fi
    elif [[ "$OS" == "macos" ]]; then
        log "MacOS系统，确保已安装Xcode命令行工具"
        if ! command -v gcc &> /dev/null; then
            warn "请运行: xcode-select --install"
        fi
    fi
}

# 创建虚拟环境
create_venv() {
    log "创建Python虚拟环境..."
    
    if [[ -d "venv" ]]; then
        warn "虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        log "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    log "激活虚拟环境..."
    source venv/bin/activate
    
    # 升级pip
    log "升级pip..."
    pip install --upgrade pip setuptools wheel
}

# 安装Python依赖
install_python_deps() {
    log "安装Python依赖包..."
    
    if [[ ! -f "requirements.txt" ]]; then
        error "requirements.txt 文件不存在"
        exit 1
    fi
    
    # 设置PyTorch安装源（加速下载）
    if [[ "$OS" == "linux" ]]; then
        log "为Linux系统安装优化的PyTorch..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    elif [[ "$OS" == "macos" ]]; then
        log "为MacOS系统安装优化的PyTorch..."
        pip install torch torchvision torchaudio
    fi
    
    # 安装其他依赖
    log "安装其他依赖包..."
    pip install -r requirements.txt
    
    log "Python依赖安装完成"
}

# 下载嵌入模型
download_embedding_models() {
    log "下载嵌入模型..."
    
    # 创建数据目录
    mkdir -p data/huggingface data/transformers data/chroma
    
    # 设置环境变量
    export HF_HOME="$(pwd)/data/huggingface"
    export TRANSFORMERS_CACHE="$(pwd)/data/transformers"
    
    info "正在下载嵌入模型，这可能需要几分钟..."
    
    # 下载配置文件中指定的模型
    python3 -c "
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# 读取配置的模型
model_name = os.getenv('MEM0_EMBEDDER_MODEL', 'shibing624/text2vec-base-chinese')
print(f'下载嵌入模型: {model_name}')

try:
    model = SentenceTransformer(model_name)
    print(f'模型 {model_name} 下载并验证成功')
except Exception as e:
    print(f'模型下载失败: {e}')
    # 尝试备用模型
    backup_model = 'BAAI/bge-large-zh-v1.5'
    print(f'尝试下载备用模型: {backup_model}')
    model = SentenceTransformer(backup_model)
    print(f'备用模型 {backup_model} 下载成功')
"
    
    log "嵌入模型下载完成"
}

# 设置配置文件
setup_config() {
    log "设置配置文件..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log "已复制 .env.example 到 .env"
        else
            # 创建基本的.env文件
            cat > .env << 'EOF'
# Mem0 配置文件

# LLM 配置 (请填入你的API密钥)
MEM0_LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here

# 嵌入模型配置
MEM0_EMBEDDER_PROVIDER=sentence_transformers
MEM0_EMBEDDER_MODEL=shibing624/text2vec-base-chinese

# 向量数据库配置
MEM0_VECTOR_STORE_PROVIDER=chroma
MEM0_VECTOR_STORE_TYPE=persistent
CHROMA_PERSIST_DIRECTORY=./data/chroma

# 应用服务配置
APP_HOST=0.0.0.0
APP_PORT=8000
API_SECRET_KEY=your_secret_key_here

# 数据存储目录
MEM0_DIR=./data

# HuggingFace 配置
HF_HOME=./data/huggingface
TRANSFORMERS_CACHE=./data/transformers

# 日志级别
LOG_LEVEL=INFO
EOF
            log "已创建基本 .env 配置文件"
        fi
        
        warn "请编辑 .env 文件，填入你的API密钥和其他配置"
    else
        log ".env 文件已存在，跳过创建"
    fi
}

# 初始化数据库
init_database() {
    log "初始化数据库..."
    
    # 检查是否需要MySQL
    if grep -q "ENABLE_MYSQL=true" .env 2>/dev/null; then
        warn "检测到MySQL配置，请确保MySQL服务已启动并配置正确"
    fi
    
    # 创建SQLite数据库目录
    mkdir -p data
    
    log "数据库初始化完成"
}

# 验证安装
verify_installation() {
    log "验证安装..."
    
    # 检查关键模块是否可以导入
    python3 -c "
import fastapi
import sentence_transformers
import chromadb
import uvicorn
print('✓ 所有核心依赖模块导入成功')
"
    
    # 检查模型是否可用
    python3 -c "
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()
model_name = os.getenv('MEM0_EMBEDDER_MODEL', 'shibing624/text2vec-base-chinese')

try:
    model = SentenceTransformer(model_name)
    test_embedding = model.encode('测试文本')
    print(f'✓ 嵌入模型 {model_name} 工作正常')
except Exception as e:
    print(f'✗ 嵌入模型测试失败: {e}')
    exit(1)
"
    
    log "安装验证完成！"
}

# 显示启动说明
show_usage() {
    info "================================================"
    info "🎉 Mem0 安装完成！"
    info "================================================"
    echo
    info "启动步骤:"
    echo "1. 激活虚拟环境:"
    echo -e "   ${BLUE}source venv/bin/activate${NC}"
    echo
    echo "2. 编辑配置文件 .env，填入你的API密钥"
    echo
    echo "3. 启动服务:"
    echo -e "   ${BLUE}python app.py${NC}"
    echo
    echo "4. 或使用交互式启动脚本:"
    echo -e "   ${BLUE}./start.sh${NC}"
    echo
    info "API文档地址: http://localhost:8000/docs"
    info "================================================"
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
                             
Mem0 智能记忆系统 - 一键安装脚本
EOF
    echo -e "${NC}"
    
    log "开始安装 Mem0..."
    
    check_os
    check_python
    install_system_deps
    create_venv
    install_python_deps
    download_embedding_models
    setup_config
    init_database
    verify_installation
    show_usage
    
    log "安装完成！"
}

# 错误处理
trap 'error "安装过程中出现错误，请检查上面的错误信息"; exit 1' ERR

# 检查参数
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Mem0 一键安装脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  --no-models    跳过模型下载（适用于网络较慢的环境）"
    echo
    exit 0
fi

if [[ "$1" == "--no-models" ]]; then
    log "跳过模型下载模式"
    download_embedding_models() {
        log "跳过嵌入模型下载（使用 --no-models 参数）"
        warn "请稍后手动下载模型或在首次运行时自动下载"
    }
fi

# 运行主安装流程
main