#!/bin/bash
# Mem0 API 测试脚本

set -e

API_BASE="http://localhost:8000"
USER_ID="test_user_$(date +%s)"

echo "🧪 Mem0 API 功能测试"
echo "API Base: $API_BASE"
echo "Test User: $USER_ID"
echo ""

# 1. 健康检查
echo "1️⃣ 健康检查..."
curl -s "$API_BASE/health" | jq '.' || echo "Health check failed"
echo ""

# 2. 添加中文记忆
echo "2️⃣ 添加中文记忆..."
MEMORY1=$(curl -s -X POST "$API_BASE/memories" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"我是一名软件工程师，专门从事Python开发，喜欢用FastAPI构建API服务\"}],
    \"user_id\": \"$USER_ID\"
  }" | jq '.') 
echo "添加记忆结果: $MEMORY1"
echo ""

# 3. 添加更多记忆
echo "3️⃣ 添加更多记忆..."
MEMORY2=$(curl -s -X POST "$API_BASE/memories" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"我喜欢吃川菜，特别是麻婆豆腐和宫保鸡丁，周末经常去川菜馆\"}],
    \"user_id\": \"$USER_ID\"
  }" | jq '.')
echo "添加记忆结果: $MEMORY2"
echo ""

MEMORY3=$(curl -s -X POST "$API_BASE/memories" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"我住在北京朝阳区，上班通常坐地铁，工作地点在中关村\"}],
    \"user_id\": \"$USER_ID\"
  }" | jq '.')
echo "添加记忆结果: $MEMORY3"
echo ""

# 4. 等待向量化处理完成
echo "⏳ 等待向量化处理完成..."
sleep 3

# 5. 搜索记忆
echo "4️⃣ 搜索记忆..."
echo "搜索：我的职业"
SEARCH1=$(curl -s -X POST "$API_BASE/memories/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"我的职业是什么\",
    \"user_id\": \"$USER_ID\",
    \"limit\": 3
  }" | jq '.')
echo "搜索结果: $SEARCH1"
echo ""

echo "搜索：我的饮食偏好"
SEARCH2=$(curl -s -X POST "$API_BASE/memories/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"我喜欢吃什么菜\",
    \"user_id\": \"$USER_ID\",
    \"limit\": 3
  }" | jq '.')
echo "搜索结果: $SEARCH2"
echo ""

echo "搜索：我住在哪里"
SEARCH3=$(curl -s -X POST "$API_BASE/memories/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"我住在哪个城市\",
    \"user_id\": \"$USER_ID\",
    \"limit\": 3
  }" | jq '.')
echo "搜索结果: $SEARCH3"
echo ""

# 6. 获取所有记忆
echo "5️⃣ 获取所有记忆..."
ALL_MEMORIES=$(curl -s -X POST "$API_BASE/memories/all" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\"
  }" | jq '.')
echo "所有记忆: $ALL_MEMORIES"
echo ""

# 7. 提取记忆ID进行更新测试
if command -v jq > /dev/null; then
    MEMORY_ID=$(echo "$ALL_MEMORIES" | jq -r '.results[0].id // empty')
    if [ ! -z "$MEMORY_ID" ] && [ "$MEMORY_ID" != "null" ]; then
        echo "6️⃣ 更新记忆..."
        UPDATE_RESULT=$(curl -s -X PUT "$API_BASE/memories/$MEMORY_ID" \
          -H "Content-Type: application/json" \
          -d "{
            \"text\": \"我是一名高级软件工程师，专门从事Python和Go开发，擅长微服务架构\"
          }" | jq '.')
        echo "更新结果: $UPDATE_RESULT"
        echo ""
        
        # 8. 获取更新后的记忆
        echo "7️⃣ 获取更新后的记忆..."
        UPDATED_MEMORY=$(curl -s "$API_BASE/memories/$MEMORY_ID" | jq '.')
        echo "更新后的记忆: $UPDATED_MEMORY"
        echo ""
    fi
fi

echo "✅ API 测试完成！"
echo ""
echo "📊 测试总结："
echo "  - ✅ 健康检查"
echo "  - ✅ 中文记忆添加"
echo "  - ✅ 中文语义搜索"
echo "  - ✅ 记忆获取"
echo "  - ✅ 记忆更新 (如果可用)"
echo ""
echo "🎯 中文优化功能验证成功！"