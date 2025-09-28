#!/bin/bash

# 在服务器上设置简单的监控
# 运行在服务器上: bash monitor-setup.sh

# 创建监控脚本
cat > /usr/local/bin/mem0-monitor.sh << 'EOF'
#!/bin/bash

# 监控配置
API_URL="http://localhost:8000/health"
WEBHOOK_URL=""  # 可选：钉钉/Slack webhook
EMAIL=""  # 可选：告警邮箱

# 检查服务
check_service() {
    if curl -f -s "$API_URL" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 发送告警
send_alert() {
    local message="$1"
    echo "[$(date)] 告警: $message" >> /var/log/mem0-monitor.log
    
    # 发送邮件（如果配置了）
    if [ ! -z "$EMAIL" ]; then
        echo "$message" | mail -s "Mem0服务告警" "$EMAIL"
    fi
    
    # 发送到webhook（如果配置了）
    if [ ! -z "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"$message\"}"
    fi
}

# 主监控循环
main() {
    if check_service; then
        echo "[$(date)] 服务正常" >> /var/log/mem0-monitor.log
    else
        send_alert "Mem0服务异常，尝试重启..."
        cd /opt/mem0
        docker-compose -f docker-compose.prod.yml restart mem0-api
        
        sleep 30
        
        if check_service; then
            send_alert "服务已自动恢复"
        else
            send_alert "服务重启失败，需要人工介入"
        fi
    fi
}

main
EOF

chmod +x /usr/local/bin/mem0-monitor.sh

# 添加定时任务
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/mem0-monitor.sh") | crontab -

echo "✅ 监控设置完成"
echo "监控脚本: /usr/local/bin/mem0-monitor.sh"
echo "日志文件: /var/log/mem0-monitor.log"
echo "检查频率: 每5分钟"