#!/bin/bash

echo "🔍 详细端口诊断脚本"
echo "===================="

echo ""
echo "1️⃣ 检查端口监听情况："
echo "9000端口："
netstat -tlnp | grep :9000
echo ""
echo "8000端口（对比）："
netstat -tlnp | grep :8000

echo ""
echo "2️⃣ 检查进程情况："
echo "所有uvicorn进程："
ps aux | grep uvicorn | grep -v grep

echo ""
echo "3️⃣ 检查应用日志（最后20行）："
if [ -f "/root/mem0/logs/app.log" ]; then
    tail -20 /root/mem0/logs/app.log
else
    echo "❌ 应用日志文件不存在"
fi

echo ""
echo "4️⃣ 测试本地连接："
echo "测试9000端口健康检查："
curl -v --connect-timeout 5 127.0.0.1:9000/health 2>&1 | head -10

echo ""
echo "测试8000端口健康检查（对比）："
curl -v --connect-timeout 5 127.0.0.1:8000/health 2>&1 | head -10

echo ""
echo "5️⃣ 检查防火墙："
if command -v ufw >/dev/null 2>&1; then
    echo "UFW状态："
    ufw status numbered
else
    echo "UFW未安装"
fi

if command -v iptables >/dev/null 2>&1; then
    echo ""
    echo "iptables INPUT规则："
    iptables -L INPUT -n --line-numbers | grep -E "(9000|8000|ACCEPT|DROP)"
else
    echo "iptables未找到"
fi

echo ""
echo "6️⃣ 检查系统资源："
echo "内存使用："
free -h
echo ""
echo "磁盘使用："
df -h /

echo ""
echo "7️⃣ 检查应用配置："
if [ -f "/root/mem0/.env" ]; then
    echo "APP_PORT配置："
    grep "APP_PORT" /root/mem0/.env || echo "未找到APP_PORT配置"
else
    echo "❌ .env文件不存在"
fi