#!/bin/bash

echo "🔍 检查端口9000的状态..."

echo "📋 检查端口监听情况："
netstat -tlnp | grep :9000 || echo "❌ 9000端口未监听"

echo ""
echo "📋 检查进程情况："
ps aux | grep uvicorn | grep 9000 || echo "❌ 没有找到9000端口的uvicorn进程"

echo ""
echo "📋 检查防火墙状态："
if command -v ufw &> /dev/null; then
    echo "UFW防火墙状态:"
    ufw status
elif command -v iptables &> /dev/null; then
    echo "iptables规则:"
    iptables -L INPUT | grep 9000 || echo "❌ 没有找到9000端口的iptables规则"
else
    echo "⚠️ 未找到防火墙工具"
fi

echo ""
echo "📋 测试本地连接："
if curl -s --connect-timeout 5 127.0.0.1:9000/health > /dev/null; then
    echo "✅ 本地连接9000端口成功"
else
    echo "❌ 本地连接9000端口失败"
fi

echo ""
echo "📋 比较8000端口（工作正常的端口）："
netstat -tlnp | grep :8000 || echo "❌ 8000端口未监听"