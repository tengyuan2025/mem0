#!/bin/bash

# Mem0本地Python环境启动脚本

set -e

echo "=========================================="
echo "        Mem0 本地Python环境启动脚本"
echo "=========================================="

# 检查是否存在.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，正在从 .env.example 创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑配置后重新运行此脚本"
    echo ""
    echo "请按照以下步骤配置："
    echo "1. 编辑 .env 文件"
    echo "2. 设置您的 LLM API 密钥（如 DASHSCOPE_API_KEY）"
    echo "3. 设置安全的 API_SECRET_KEY"
    echo "4. 根据需要调整其他配置"
    exit 1
fi

# 检查Python环境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 未找到 Python，请先安装 Python 3.9+"
        exit 1
    fi
    
    # 检查Python版本
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "✅ 检测到 Python $PYTHON_VERSION"
}

# 创建并激活虚拟环境
setup_venv() {
    if [ ! -d "venv" ]; then
        echo "📦 创建虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    
    echo "🔄 激活虚拟环境..."
    source venv/bin/activate
}

# 检查并安装依赖
install_dependencies() {
    echo "📚 检查依赖..."
    
    # 检查关键依赖是否已安装
    if python -c "import fastapi, uvicorn" 2>/dev/null; then
        echo "✅ 依赖已安装，跳过安装步骤"
        return
    fi
    
    echo "需要安装依赖..."
    echo "正在升级 pip..."
    pip install --upgrade pip
    echo ""
    echo "正在安装项目依赖（这可能需要几分钟）..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 依赖安装失败"
        exit 1
    fi
    
    echo "✅ 依赖安装完成"
}

# 启动数据库服务
start_databases() {
    echo ""
    echo "🗄️ 启动数据库服务..."
    echo "请选择："
    echo "1) 使用 Docker Compose 启动数据库服务（推荐）"
    echo "2) 跳过（已有数据库服务运行）"
    echo ""
    read -p "请输入选项 (1-2): " db_choice
    
    case $db_choice in
        1)
            if ! command -v docker &> /dev/null; then
                echo "❌ Docker 未安装，请先安装 Docker 或手动启动数据库服务"
                exit 1
            fi
            
            echo "🚀 启动数据库服务..."
            docker-compose -f docker-compose-db.yml up -d
            
            # 等待服务就绪
            echo "⏳ 等待数据库服务就绪..."
            sleep 10
            
            echo "✅ 数据库服务已启动"
            echo ""
            echo "服务端口："
            echo "  - PostgreSQL: 5432"
            echo "  - Redis: 6379"
            echo "  - ChromaDB: 8001"
            echo "  - Neo4j: 7474 (HTTP), 7687 (Bolt)"
            ;;
        2)
            echo "⏭️ 跳过数据库服务启动"
            ;;
        *)
            echo "❌ 无效选项"
            exit 1
            ;;
    esac
}

# 启动API服务
start_api() {
    echo ""
    echo "🚀 启动 Mem0 API 服务..."
    echo ""
    echo "服务将在 http://localhost:9000 启动"
    echo "API文档: http://localhost:9000/docs"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo ""
    
    python app.py
}

# 主流程
main() {
    echo ""
    check_python
    setup_venv
    install_dependencies
    start_databases
    start_api
}

# 清理函数
cleanup() {
    echo ""
    echo "⚠️ 正在停止服务..."
    
    # 询问是否停止数据库
    echo ""
    read -p "是否停止数据库服务？(y/n): " stop_db
    if [ "$stop_db" = "y" ] || [ "$stop_db" = "Y" ]; then
        if [ -f "docker-compose-db.yml" ]; then
            docker-compose -f docker-compose-db.yml down
            echo "✅ 数据库服务已停止"
        fi
    fi
    
    deactivate 2>/dev/null || true
    echo "✅ 清理完成"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 运行主流程
main