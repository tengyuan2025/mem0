#!/bin/bash

echo "🔍 正在分析xiaozhi-esp32-server聊天记录存储位置..."
echo "Agent ID: f4d54997b1f94b49941b405997d5dd87"
echo "Session ID: c65cc770-39f6-4be4-9d58-f169d45c9055"
echo "================================================"

# 数据库连接信息
DB_HOST="localhost"
DB_USER="root"
DB_PASS="123456"
DB_NAME="xiaozhi_esp32_server"
CONTAINER_NAME="xiaozhi-esp32-server-db"

# Agent和Session ID
AGENT_ID="f4d54997b1f94b49941b405997d5dd87"
SESSION_ID="c65cc770-39f6-4be4-9d58-f169d45c9055"

echo "1. 📋 获取所有数据库表..."
TABLES=$(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "SHOW TABLES;" --skip-column-names 2>/dev/null | tr -d '\r')

echo "发现以下表："
echo "$TABLES"
echo ""

echo "2. 🔍 搜索包含聊天相关字段的表..."
CHAT_TABLES=$(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
SELECT DISTINCT TABLE_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = '$DB_NAME' 
AND (
    COLUMN_NAME LIKE '%agent%' OR 
    COLUMN_NAME LIKE '%chat%' OR 
    COLUMN_NAME LIKE '%session%' OR 
    COLUMN_NAME LIKE '%conversation%' OR
    COLUMN_NAME LIKE '%message%' OR
    COLUMN_NAME LIKE '%history%' OR
    COLUMN_NAME LIKE '%dialog%'
);" --skip-column-names 2>/dev/null | tr -d '\r')

echo "可能存储聊天记录的表："
echo "$CHAT_TABLES"
echo ""

echo "3. 🔎 在各表中搜索Agent ID..."
FOUND_AGENT=""
for table in $TABLES; do
    if [[ ! -z "$table" ]]; then
        echo "检查表: $table"
        RESULT=$(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
        SELECT COUNT(*) as count FROM $table 
        WHERE CONCAT_WS('|', 
            COALESCE(CONVERT(CONCAT_WS('',
                $(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
                SELECT GROUP_CONCAT(COLUMN_NAME SEPARATOR ', COALESCE(CONVERT(') 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '$DB_NAME' AND TABLE_NAME = '$table';" --skip-column-names 2>/dev/null | tr -d '\r')
            ), CHAR), ''), ''
        ) LIKE '%$AGENT_ID%';" --skip-column-names 2>/dev/null | tr -d '\r')
        
        if [[ "$RESULT" != "0" && ! -z "$RESULT" ]]; then
            echo "✅ 在表 $table 中找到 Agent ID!"
            FOUND_AGENT="$table"
            
            # 显示表结构
            echo "表结构："
            docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "DESCRIBE $table;" 2>/dev/null
            
            # 显示包含Agent ID的记录
            echo "相关记录（前3条）："
            docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "SELECT * FROM $table LIMIT 3;" 2>/dev/null
            echo ""
        fi
    fi
done

echo "4. 🔍 在各表中搜索Session ID..."
FOUND_SESSION=""
for table in $TABLES; do
    if [[ ! -z "$table" ]]; then
        echo "检查表: $table"
        # 简化搜索，直接查找包含Session ID的记录
        RESULT=$(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '$DB_NAME' AND TABLE_NAME = '$table';" --skip-column-names 2>/dev/null | tr -d '\r')
        
        if [[ ! -z "$RESULT" && "$RESULT" != "0" ]]; then
            # 获取所有列名
            COLUMNS=$(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
            SELECT GROUP_CONCAT(COLUMN_NAME) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '$DB_NAME' AND TABLE_NAME = '$table';" --skip-column-names 2>/dev/null | tr -d '\r')
            
            # 对每个可能的列搜索Session ID
            SESSION_COUNT=$(docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
            SELECT COUNT(*) FROM $table WHERE 
            CONCAT_WS('', $(echo $COLUMNS | sed 's/,/ ,/g')) LIKE '%$SESSION_ID%';" --skip-column-names 2>/dev/null | tr -d '\r')
            
            if [[ "$SESSION_COUNT" != "0" && ! -z "$SESSION_COUNT" ]]; then
                echo "✅ 在表 $table 中找到 Session ID!"
                FOUND_SESSION="$table"
                
                # 显示表结构
                echo "表结构："
                docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "DESCRIBE $table;" 2>/dev/null
                
                # 显示包含Session ID的记录
                echo "相关记录："
                docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "
                SELECT * FROM $table 
                WHERE CONCAT_WS('', $(echo $COLUMNS | sed 's/,/ ,/g')) LIKE '%$SESSION_ID%' 
                LIMIT 5;" 2>/dev/null
                echo ""
            fi
        fi
    fi
done

echo "5. 📊 分析所有可能的聊天相关表..."
for table in $CHAT_TABLES; do
    if [[ ! -z "$table" ]]; then
        echo "分析表: $table"
        echo "表结构："
        docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "DESCRIBE $table;" 2>/dev/null
        
        echo "记录数量："
        docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "SELECT COUNT(*) as total_records FROM $table;" 2>/dev/null
        
        echo "最新几条记录："
        docker exec -it $CONTAINER_NAME mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "SELECT * FROM $table ORDER BY id DESC LIMIT 3;" 2>/dev/null
        echo "----------------------------------------"
    fi
done

echo ""
echo "🎯 分析结果："
echo "================================================"

if [[ ! -z "$FOUND_AGENT" ]]; then
    echo "✅ Agent ID 存储在表: $FOUND_AGENT"
else
    echo "❌ 未找到 Agent ID"
fi

if [[ ! -z "$FOUND_SESSION" ]]; then
    echo "✅ Session ID 存储在表: $FOUND_SESSION"
else
    echo "❌ 未找到 Session ID"
fi

if [[ ! -z "$CHAT_TABLES" ]]; then
    echo "📋 可能的聊天记录表: $CHAT_TABLES"
else
    echo "❓ 未发现明显的聊天记录表"
fi

echo ""
echo "🔍 建议检查以下表作为聊天记录存储位置："
echo "$CHAT_TABLES" | while read table; do
    if [[ ! -z "$table" ]]; then
        echo "- $table"
    fi
done

echo ""
echo "✅ 分析完成!"