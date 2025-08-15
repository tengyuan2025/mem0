#!/bin/bash
# 停止本地 Mem0 环境脚本

echo "🛑 停止 Mem0 本地环境..."

# 停止 Qdrant 进程
if [ -f "qdrant.pid" ]; then
    QDRANT_PID=$(cat qdrant.pid)
    if kill -0 $QDRANT_PID 2>/dev/null; then
        echo "🛑 停止 Qdrant 进程 (PID: $QDRANT_PID)..."
        kill $QDRANT_PID
        sleep 2
        
        # 强制停止如果还在运行
        if kill -0 $QDRANT_PID 2>/dev/null; then
            echo "⚠️ 强制停止 Qdrant 进程..."
            kill -9 $QDRANT_PID
        fi
        
        echo "✅ Qdrant 已停止"
    else
        echo "ℹ️ Qdrant 进程已不存在"
    fi
    
    # 清理 PID 文件
    rm -f qdrant.pid
else
    echo "ℹ️ 未找到 Qdrant PID 文件"
fi

# 检查是否还有 Qdrant 进程在运行
if pgrep -f "qdrant" > /dev/null; then
    echo "⚠️ 发现其他 Qdrant 进程，正在停止..."
    pkill -f "qdrant"
    sleep 2
    
    # 强制停止
    if pgrep -f "qdrant" > /dev/null; then
        echo "⚠️ 强制停止所有 Qdrant 进程..."
        pkill -9 -f "qdrant"
    fi
fi

echo "✅ 本地环境已停止"
echo ""
echo "💡 提示："
echo "  - 数据文件保存在 ./qdrant_data 目录"
echo "  - 日志文件保存在 ./qdrant.log"
echo "  - 如需完全清理，可删除 qdrant_data 目录"
