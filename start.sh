#!/bin/bash

# Mem0自托管服务启动脚本

set -e

echo "=========================================="
echo "        Mem0 自托管服务启动脚本"
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

# 选择启动方式
echo ""
echo "请选择启动方式："
echo "1) Docker Compose（推荐，包含所有服务）"
echo "2) 本地Python环境（需要手动安装数据库）"
echo "3) 仅启动API服务（Docker）"
echo "4) 启动 Milvus 向量数据库（Docker）"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 使用 Docker Compose 启动所有服务..."
        
        # 检查Docker是否安装
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker 未安装，请先安装 Docker"
            exit 1
        fi
        
        # 检查Docker服务是否运行，如果未运行则尝试启动
        if ! docker info &> /dev/null; then
            echo "⚠️  Docker 服务未运行，正在尝试启动..."
            
            # 检测操作系统
            OS_TYPE=$(uname -s)
            
            if [ "$OS_TYPE" = "Darwin" ]; then
                # macOS - 启动Docker Desktop
                if [ -d "/Applications/Docker.app" ]; then
                    echo "🔄 正在启动 Docker Desktop..."
                    open -a Docker
                    
                    # 等待Docker启动，最多等待60秒
                    echo "⏳ 等待 Docker 服务就绪..."
                    WAIT_TIME=0
                    MAX_WAIT=60
                    
                    while ! docker info &> /dev/null; do
                        if [ $WAIT_TIME -ge $MAX_WAIT ]; then
                            echo "❌ Docker 启动超时，请手动启动 Docker Desktop"
                            exit 1
                        fi
                        sleep 2
                        WAIT_TIME=$((WAIT_TIME + 2))
                        echo -n "."
                    done
                    echo ""
                    echo "✅ Docker Desktop 已启动"
                    
                elif [ -d "$HOME/Applications/Docker.app" ]; then
                    echo "🔄 正在启动 Docker Desktop..."
                    open -a "$HOME/Applications/Docker.app"
                    
                    # 等待Docker启动
                    echo "⏳ 等待 Docker 服务就绪..."
                    WAIT_TIME=0
                    MAX_WAIT=60
                    
                    while ! docker info &> /dev/null; do
                        if [ $WAIT_TIME -ge $MAX_WAIT ]; then
                            echo "❌ Docker 启动超时，请手动启动 Docker Desktop"
                            exit 1
                        fi
                        sleep 2
                        WAIT_TIME=$((WAIT_TIME + 2))
                        echo -n "."
                    done
                    echo ""
                    echo "✅ Docker Desktop 已启动"
                    
                else
                    echo "❌ 未找到 Docker Desktop，请先安装 Docker Desktop"
                    echo "下载地址: https://www.docker.com/products/docker-desktop"
                    exit 1
                fi
                
            elif [ "$OS_TYPE" = "Linux" ]; then
                # Linux - 尝试使用systemctl启动Docker服务
                if command -v systemctl &> /dev/null; then
                    echo "🔄 正在启动 Docker 服务..."
                    if sudo systemctl start docker 2>/dev/null; then
                        echo "⏳ 等待 Docker 服务就绪..."
                        sleep 3
                        if docker info &> /dev/null; then
                            echo "✅ Docker 服务已启动"
                        else
                            echo "❌ Docker 服务启动失败"
                            exit 1
                        fi
                    else
                        echo "❌ 无法启动 Docker 服务，请手动运行: sudo systemctl start docker"
                        exit 1
                    fi
                elif command -v service &> /dev/null; then
                    echo "🔄 正在启动 Docker 服务..."
                    if sudo service docker start 2>/dev/null; then
                        echo "⏳ 等待 Docker 服务就绪..."
                        sleep 3
                        if docker info &> /dev/null; then
                            echo "✅ Docker 服务已启动"
                        else
                            echo "❌ Docker 服务启动失败"
                            exit 1
                        fi
                    else
                        echo "❌ 无法启动 Docker 服务，请手动运行: sudo service docker start"
                        exit 1
                    fi
                else
                    echo "❌ Docker 服务未运行"
                    echo "请手动启动 Docker 服务"
                    exit 1
                fi
                
            else
                echo "❌ Docker 服务未运行"
                echo "请手动启动 Docker 服务"
                exit 1
            fi
        else
            echo "✅ Docker 服务运行中"
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            # 尝试使用docker compose命令（新版本）
            if docker compose version &> /dev/null; then
                echo "✅ 检测到 Docker Compose (docker compose)"
                docker compose -f docker-compose-china.yml up -d
            else
                echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
                exit 1
            fi
        else
            echo "✅ 检测到 Docker Compose (docker-compose)"
            docker-compose -f docker-compose-china.yml up -d
        fi
        
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 10
        
        # 检查服务状态
        if docker compose version &> /dev/null; then
            docker compose -f docker-compose-china.yml ps
        else
            docker-compose -f docker-compose-china.yml ps
        fi
        
        echo ""
        echo "✅ 所有服务已启动！"
        echo ""
        echo "服务访问地址："
        echo "- API服务: http://localhost:9000"
        echo "- API文档: http://localhost:9000/docs"
        echo "- ChromaDB: http://localhost:8001"
        echo "- Neo4j浏览器: http://localhost:7474"
        echo ""
        echo "查看日志："
        echo "- docker compose logs -f mem0-api"
        echo ""
        echo "停止服务："
        echo "- docker compose down"
        ;;
        
    2)
        echo ""
        echo "🚀 在本地Python环境中启动..."
        
        # 检查Python版本
        if ! python3 --version | grep -E "3\.(9|10|11|12|13)" &> /dev/null; then
            echo "❌ 需要 Python 3.9 或更高版本"
            exit 1
        fi
        
        # 创建虚拟环境
        if [ ! -d "venv" ]; then
            echo "📦 创建虚拟环境..."
            python3 -m venv venv
        fi
        
        # 激活虚拟环境
        echo "🔧 激活虚拟环境..."
        source venv/bin/activate
        
        # 检查并安装依赖
        if [ ! -f "venv/.deps_installed" ] || [ "requirements-core.txt" -nt "venv/.deps_installed" ]; then
            echo "📥 检测到依赖需要安装或更新，正在安装核心依赖..."
            pip install -r requirements-core.txt
            touch venv/.deps_installed
            echo "✅ 依赖安装完成"
        else
            echo "✅ 依赖已是最新版本，跳过安装步骤"
        fi
        
        echo ""
        echo "ℹ️  服务依赖说明："
        echo "- ChromaDB: 使用本地持久化存储，无需启动服务"
        echo "- MySQL: 可选，如需启用请设置 ENABLE_MYSQL=true 并启动服务"
        echo ""
        
        # 检查MySQL配置并提示
        if grep -q "ENABLE_MYSQL=true" .env 2>/dev/null; then
            echo "ℹ️  检测到 MySQL 已启用，如未启动服务可能会有连接错误"
        else
            echo "ℹ️  使用本地存储模式"
        fi
        
        # 设置NO_PROXY环境变量，避免本地访问被代理
        export NO_PROXY=localhost,127.0.0.1,0.0.0.0
        export no_proxy=localhost,127.0.0.1,0.0.0.0
        
        # 设置HuggingFace镜像（解决国内访问问题）
        export HF_ENDPOINT=https://hf-mirror.com
        # 如果模型已下载，可以设置离线模式
        export HF_HUB_OFFLINE=1
        
        # 启动服务
        echo ""
        echo "🚀 启动API服务..."
        echo ""
        
        # 后台启动服务
        python app.py &
        APP_PID=$!
        
        # 等待服务启动
        echo "⏳ 等待服务启动..."
        sleep 3
        
        # 检查服务是否启动成功
        if kill -0 $APP_PID 2>/dev/null; then
            echo ""
            echo "✅ Mem0 自托管服务启动成功！"
            echo ""
            echo "=========================================="
            echo "           服务访问地址"
            echo "=========================================="
            echo "🌐 API 服务:      http://localhost:9000"
            echo "📖 API 文档:      http://localhost:9000/docs"
            echo "🔧 健康检查:      http://localhost:9000/health"
            echo ""
            
            # 显示配置信息
            echo "=========================================="
            echo "           服务配置信息"
            echo "=========================================="
            if grep -q "ENABLE_MYSQL=true" .env 2>/dev/null; then
                echo "💾 MySQL:        已启用"
            else
                echo "💾 MySQL:        未启用"
            fi
            echo "🗂️  ChromaDB:     本地持久化存储"
            echo "🤖 LLM Provider: $(grep "^MEM0_LLM_PROVIDER=" .env 2>/dev/null | cut -d'=' -f2 | head -1)"
            echo "🔤 Embedding:    $(grep "^MEM0_EMBEDDER_MODEL=" .env 2>/dev/null | cut -d'=' -f2 | head -1)"
            echo ""
            
            echo "=========================================="
            echo "           使用说明"
            echo "=========================================="
            echo "• 停止服务: 按 Ctrl+C"
            echo "• 查看日志: 服务运行中会显示实时日志"
            echo "• 测试接口: curl http://localhost:9000/health"
            echo ""
            echo "🎉 服务已就绪，开始使用吧！"
            echo ""
            
            # 等待用户停止服务
            wait $APP_PID
        else
            echo "❌ 服务启动失败，请检查错误信息"
            exit 1
        fi
        ;;
        
    3)
        echo ""
        echo "🚀 仅启动API服务（Docker）..."
        
        # 检查Docker是否安装
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker 未安装，请先安装 Docker"
            exit 1
        fi
        
        # 检查Docker服务是否运行，如果未运行则尝试启动
        if ! docker info &> /dev/null; then
            echo "⚠️  Docker 服务未运行，正在尝试启动..."
            
            # 检测操作系统
            OS_TYPE=$(uname -s)
            
            if [ "$OS_TYPE" = "Darwin" ]; then
                # macOS - 启动Docker Desktop
                if [ -d "/Applications/Docker.app" ]; then
                    echo "🔄 正在启动 Docker Desktop..."
                    open -a Docker
                    
                    # 等待Docker启动，最多等待60秒
                    echo "⏳ 等待 Docker 服务就绪..."
                    WAIT_TIME=0
                    MAX_WAIT=60
                    
                    while ! docker info &> /dev/null; do
                        if [ $WAIT_TIME -ge $MAX_WAIT ]; then
                            echo "❌ Docker 启动超时，请手动启动 Docker Desktop"
                            exit 1
                        fi
                        sleep 2
                        WAIT_TIME=$((WAIT_TIME + 2))
                        echo -n "."
                    done
                    echo ""
                    echo "✅ Docker Desktop 已启动"
                    
                elif [ -d "$HOME/Applications/Docker.app" ]; then
                    echo "🔄 正在启动 Docker Desktop..."
                    open -a "$HOME/Applications/Docker.app"
                    
                    # 等待Docker启动
                    echo "⏳ 等待 Docker 服务就绪..."
                    WAIT_TIME=0
                    MAX_WAIT=60
                    
                    while ! docker info &> /dev/null; do
                        if [ $WAIT_TIME -ge $MAX_WAIT ]; then
                            echo "❌ Docker 启动超时，请手动启动 Docker Desktop"
                            exit 1
                        fi
                        sleep 2
                        WAIT_TIME=$((WAIT_TIME + 2))
                        echo -n "."
                    done
                    echo ""
                    echo "✅ Docker Desktop 已启动"
                    
                else
                    echo "❌ 未找到 Docker Desktop，请先安装 Docker Desktop"
                    echo "下载地址: https://www.docker.com/products/docker-desktop"
                    exit 1
                fi
                
            elif [ "$OS_TYPE" = "Linux" ]; then
                # Linux - 尝试使用systemctl启动Docker服务
                if command -v systemctl &> /dev/null; then
                    echo "🔄 正在启动 Docker 服务..."
                    if sudo systemctl start docker 2>/dev/null; then
                        echo "⏳ 等待 Docker 服务就绪..."
                        sleep 3
                        if docker info &> /dev/null; then
                            echo "✅ Docker 服务已启动"
                        else
                            echo "❌ Docker 服务启动失败"
                            exit 1
                        fi
                    else
                        echo "❌ 无法启动 Docker 服务，请手动运行: sudo systemctl start docker"
                        exit 1
                    fi
                elif command -v service &> /dev/null; then
                    echo "🔄 正在启动 Docker 服务..."
                    if sudo service docker start 2>/dev/null; then
                        echo "⏳ 等待 Docker 服务就绪..."
                        sleep 3
                        if docker info &> /dev/null; then
                            echo "✅ Docker 服务已启动"
                        else
                            echo "❌ Docker 服务启动失败"
                            exit 1
                        fi
                    else
                        echo "❌ 无法启动 Docker 服务，请手动运行: sudo service docker start"
                        exit 1
                    fi
                else
                    echo "❌ Docker 服务未运行"
                    echo "请手动启动 Docker 服务"
                    exit 1
                fi
                
            else
                echo "❌ Docker 服务未运行"
                echo "请手动启动 Docker 服务"
                exit 1
            fi
        else
            echo "✅ Docker 服务运行中"
        fi
        
        # 构建镜像
        echo "📦 构建Docker镜像..."
        docker build -t mem0-api:latest .
        
        # 启动容器
        echo "🚀 启动容器..."
        docker run -d \
            --name mem0-api \
            --env-file .env \
            -p 9000:9000 \
            -v $(pwd)/logs:/app/logs \
            -v $(pwd)/data:/app/data \
            --restart unless-stopped \
            mem0-api:latest
        
        echo ""
        echo "✅ API服务已启动！"
        echo ""
        echo "服务访问地址："
        echo "- API服务: http://localhost:9000"
        echo "- API文档: http://localhost:9000/docs"
        echo ""
        echo "⚠️  注意：您需要单独配置和启动数据库服务"
        ;;
        
    4)
        echo ""
        echo "🚀 启动 Milvus 向量数据库..."
        
        # 检查Docker是否安装
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker 未安装，请先安装 Docker"
            exit 1
        fi
        
        # 检查Docker服务是否运行
        if ! docker info &> /dev/null; then
            echo "❌ Docker 服务未运行"
            echo "请启动 Docker Desktop 或运行: sudo systemctl start docker"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            # 尝试使用docker compose命令（新版本）
            if docker compose version &> /dev/null; then
                echo "✅ 检测到 Docker Compose (docker compose)"
                docker compose -f docker-compose-milvus.yml up -d
            else
                echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
                exit 1
            fi
        else
            echo "✅ 检测到 Docker Compose (docker-compose)"
            docker-compose -f docker-compose-milvus.yml up -d
        fi
        
        echo ""
        echo "⏳ 等待 Milvus 服务启动..."
        sleep 15
        
        # 检查服务状态
        if docker compose version &> /dev/null; then
            docker compose -f docker-compose-milvus.yml ps
        else
            docker-compose -f docker-compose-milvus.yml ps
        fi
        
        echo ""
        echo "✅ Milvus 向量数据库已启动！"
        echo ""
        echo "服务访问地址："
        echo "- Milvus 服务: localhost:19530"
        echo "- MinIO 控制台: http://localhost:9001 (minioadmin/minioadmin)"
        echo "- MinIO API: http://localhost:9000"
        echo ""
        echo "现在你可以启动 Mem0 API 服务："
        echo "- 使用选项2：本地Python环境启动"
        echo "- 或直接运行: python app.py"
        echo ""
        echo "停止 Milvus 服务："
        echo "- docker compose -f docker-compose-milvus.yml down"
        ;;
        
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "          启动完成"
echo "=========================================="