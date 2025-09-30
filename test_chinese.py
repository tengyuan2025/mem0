#!/usr/bin/env python3
"""
Mem0 中文功能测试
专门测试中文语义理解和记忆功能
"""

import os
import requests
import json
import time

# 取消代理设置
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

API_BASE_URL = "http://localhost:9000"
API_KEY = "your-secret-key-change-this"
TEST_USER_ID = "chinese_user_001"

def test_chinese_memory():
    """测试中文记忆功能"""
    
    print("🇨🇳 Mem0 中文智能记忆系统测试")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 1. 测试服务信息
    print("\n📊 服务信息:")
    response = requests.get(f"{API_BASE_URL}/")
    if response.status_code == 200:
        info = response.json()
        print(f"✅ {info['service']} v{info['version']}")
        print(f"🔧 特性: {', '.join(info['features'])}")
        print(f"🧠 文本匹配器: {info['text_matcher']}")
    
    print("\n" + "="*60)
    print("开始中文记忆功能测试...")
    
    # 2. 添加中文个人信息记忆
    print("\n1️⃣ 添加个人信息记忆...")
    
    memories_to_add = [
        {
            "messages": [
                {"role": "user", "content": "我是张明，今年28岁，在北京一家互联网科技公司做软件工程师"},
                {"role": "assistant", "content": "您好张明！了解了，您28岁，在北京的互联网科技公司担任软件工程师"}
            ],
            "metadata": {"category": "个人信息", "type": "基本资料"}
        },
        {
            "messages": [
                {"role": "user", "content": "我平时喜欢喝咖啡，特别偏爱拿铁和卡布奇诺，不太喜欢美式咖啡"},
                {"role": "assistant", "content": "记住了，您喜欢拿铁和卡布奇诺，不太喜欢美式咖啡"}
            ],
            "metadata": {"category": "偏好", "type": "饮品"}
        },
        {
            "messages": [
                {"role": "user", "content": "我每天早上7点起床，8点半到公司，晚上6点下班，周末喜欢去公园跑步"},
                {"role": "assistant", "content": "了解您的作息时间，工作日8点半上班6点下班，周末喜欢公园跑步"}
            ],
            "metadata": {"category": "习惯", "type": "作息"}
        },
        {
            "messages": [
                {"role": "user", "content": "我住在朝阳区，公司在海淀区，每天坐地铁通勤大概需要45分钟"},
                {"role": "assistant", "content": "您住朝阳区，公司在海淀区，地铁通勤45分钟"}
            ],
            "metadata": {"category": "地理", "type": "居住工作"}
        }
    ]
    
    memory_ids = []
    for i, memory_data in enumerate(memories_to_add):
        data = {
            "user_id": TEST_USER_ID,
            "messages": memory_data["messages"],
            "metadata": memory_data["metadata"]
        }
        
        response = requests.post(f"{API_BASE_URL}/api/v1/memories/add", headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            memory_ids.append(result["memory_id"])
            print(f"  ✅ 记忆{i+1}: {result['memory_id']} (关键词: {result['keywords_count']}个)")
        else:
            print(f"  ❌ 记忆{i+1}添加失败: {response.status_code}")
    
    # 3. 测试中文语义搜索
    print(f"\n2️⃣ 测试中文语义搜索 (共{len(memory_ids)}条记忆)...")
    
    test_queries = [
        "我的工作是什么？",
        "我喜欢喝什么？",
        "我住在哪里？",
        "我几点上班？",
        "周末做什么运动？",
        "通勤时间多长？",
        "我的年龄",
        "咖啡偏好"
    ]
    
    for query in test_queries:
        search_data = {"user_id": TEST_USER_ID, "query": query, "limit": 3}
        response = requests.post(f"{API_BASE_URL}/api/v1/memories/search", headers=headers, json=search_data)
        
        if response.status_code == 200:
            results = response.json()
            if results:
                best_match = results[0]
                content = best_match["content"].split("|")[0].replace("user:", "").strip()
                print(f"  📝 '{query}' → {content} (相关度: {best_match['score']:.3f})")
            else:
                print(f"  ❓ '{query}' → 未找到相关记忆")
        else:
            print(f"  ❌ 搜索失败: {query}")
    
    # 4. 测试智能对话
    print(f"\n3️⃣ 测试智能对话...")
    
    chat_questions = [
        "你知道我叫什么名字吗？",
        "我在哪个城市工作？",
        "我平时喜欢喝什么咖啡？",
        "我的通勤时间是多久？",
        "你还记得我的职业吗？",
        "我住在北京的哪个区？"
    ]
    
    for question in chat_questions:
        chat_data = {"user_id": TEST_USER_ID, "message": question, "use_memory": True}
        response = requests.post(f"{API_BASE_URL}/api/v1/chat", headers=headers, json=chat_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  👤 '{question}'")
            print(f"  🤖 {result['response']}")
            print()
        else:
            print(f"  ❌ 对话失败: {question}")
    
    # 5. 统计信息
    print("4️⃣ 记忆统计...")
    response = requests.get(f"{API_BASE_URL}/api/v1/users/{TEST_USER_ID}/memories", headers=headers)
    if response.status_code == 200:
        result = response.json()
        total_memories = result["count"]
        print(f"  📊 用户记忆总数: {total_memories}")
        
        # 按类别统计
        categories = {}
        for memory in result["memories"]:
            category = memory["metadata"].get("category", "未分类")
            categories[category] = categories.get(category, 0) + 1
        
        print("  📈 记忆分类统计:")
        for category, count in categories.items():
            print(f"    - {category}: {count}条")
    
    print("\n" + "="*60)
    print("🎉 中文记忆功能测试完成！")
    print("\n💡 特点:")
    print("- ✅ 完全本地运行，无需任何在线API")
    print("- ✅ 专门优化的中文分词和语义匹配")
    print("- ✅ 支持中英文混合内容")
    print("- ✅ 智能关键词提取和相似度计算")
    print("- ✅ 上下文感知的智能回复")

if __name__ == "__main__":
    test_chinese_memory()