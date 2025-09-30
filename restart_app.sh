#!/bin/bash

echo "🔄 重启应用到9000端口"
echo "===================="

# 切换到应用目录
cd /root/mem0

echo "1️⃣ 停止现有进程..."
# 停止所有9000端口的进程
pkill -f "uvicorn.*9000" || echo "没有找到9000端口的进程"

# 等待进程完全停止
sleep 3

echo ""
echo "2️⃣ 检查进程是否已停止..."
ps aux | grep uvicorn | grep 9000 | grep -v grep || echo "✅ 9000端口进程已停止"

echo ""
echo "3️⃣ 检查环境变量..."
if [ -f ".env" ]; then
    source .env
    echo "APP_PORT = $APP_PORT"
    echo "APP_HOST = $APP_HOST"
else
    echo "❌ .env文件不存在"
fi

echo ""
echo "4️⃣ 启动应用..."
echo "启动命令: python3 -m uvicorn app:app --host 0.0.0.0 --port 9000"

# 确保日志目录存在
mkdir -p logs

# 启动应用
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 9000 > logs/app.log 2>&1 &
APP_PID=$!

echo "✅ 应用已启动，PID: $APP_PID"
echo $APP_PID > mem0_app.pid

echo ""
echo "5️⃣ 等待应用启动（10秒）..."
sleep 10

echo ""
echo "6️⃣ 检查启动状态..."
if ps -p $APP_PID > /dev/null; then
    echo "✅ 进程运行正常"
else
    echo "❌ 进程已退出，查看日志:"
    tail -20 logs/app.log
    exit 1
fi

echo ""
echo "7️⃣ 检查端口监听..."
netstat -tlnp | grep :9000 || echo "❌ 9000端口未监听"

echo ""
echo "8️⃣ 测试连接..."
if curl -f http://127.0.0.1:9000/health 2>/dev/null; then
    echo "✅ 健康检查成功"
else
    echo "❌ 健康检查失败"
    echo "查看应用日志:"
    tail -10 logs/app.log
fi

echo ""
echo "🎉 重启完成！"