#!/bin/bash

echo "🔍 快速分析聊天记录存储位置..."
echo "Agent ID: f4d54997b1f94b49941b405997d5dd87"
echo "Session ID: c65cc770-39f6-4be4-9d58-f169d45c9055"
echo "================================================"

CONTAINER="xiaozhi-esp32-server-db"
DB="xiaozhi_esp32_server"

# 1. 获取所有表
echo "📋 数据库中的所有表："
docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "SHOW TABLES;" 2>/dev/null

echo ""
echo "🔍 查找聊天相关的表结构..."

# 2. 查找聊天相关表
docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = '$DB' 
AND (COLUMN_NAME LIKE '%chat%' 
     OR COLUMN_NAME LIKE '%message%' 
     OR COLUMN_NAME LIKE '%conversation%' 
     OR COLUMN_NAME LIKE '%session%' 
     OR COLUMN_NAME LIKE '%agent%'
     OR COLUMN_NAME LIKE '%history%')
ORDER BY TABLE_NAME, ORDINAL_POSITION;" 2>/dev/null

echo ""
echo "🔎 直接搜索Agent ID在哪个表中..."

# 3. 搜索特定ID - 使用更简单的方法
TABLES=$(docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "SHOW TABLES;" --skip-column-names 2>/dev/null | tr -d '\r\n')

for table in $TABLES; do
    if [[ ! -z "$table" && "$table" != "Tables_in_$DB" ]]; then
        echo "检查表: $table"
        
        # 尝试搜索Agent ID
        COUNT=$(docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "
        SELECT COUNT(*) FROM \`$table\` 
        WHERE CONCAT_WS(' ', 
            $(docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "
            SELECT GROUP_CONCAT(CONCAT('COALESCE(\`', COLUMN_NAME, '\`, \'\')') SEPARATOR ', ')
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '$DB' AND TABLE_NAME = '$table';" --skip-column-names 2>/dev/null)
        ) LIKE '%f4d54997b1f94b49941b405997d5dd87%';" --skip-column-names 2>/dev/null | tr -d '\r\n')
        
        if [[ "$COUNT" =~ ^[0-9]+$ ]] && [[ $COUNT -gt 0 ]]; then
            echo "✅ 找到Agent ID在表: $table (共$COUNT条记录)"
            
            echo "表结构："
            docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "DESCRIBE \`$table\`;" 2>/dev/null
            
            echo "示例数据："
            docker exec -it $CONTAINER mysql -u root -p123456 $DB -e "SELECT * FROM \`$table\` LIMIT 3;" 2>/dev/null
            echo "----------------------------------------"
        fi
    fi
done

echo ""
echo "🎯 最终结论："
echo "基于API路径 /xiaozhi/agent/{agent_id}/chat-history/{session_id}"
echo "聊天记录很可能存储在包含以下字段的表中："
echo "- agent_id 或相关字段存储Agent ID" 
echo "- session_id 或conversation_id存储会话ID"
echo "- message_content 或content存储聊天内容"
echo "- timestamp 或created_at存储时间"
echo ""