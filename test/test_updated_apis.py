#!/usr/bin/env python3
"""
测试更新后的API功能
1. 测试创建记忆返回结果包含记忆内容
2. 测试新的查询接口支持user_id和session_id参数
"""
import requests
import json
import os

# Disable proxy
os.environ.pop('http_proxy', None)
os.environ.pop('HTTP_PROXY', None) 
os.environ.pop('https_proxy', None)
os.environ.pop('HTTPS_PROXY', None)

session = requests.Session()
session.proxies = {}

BASE_URL = "http://localhost:8002"
API_TOKEN = "tengyuan2025"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_create_memory_with_content():
    """测试创建记忆返回结果包含记忆内容"""
    
    print("1️⃣  测试创建记忆返回完整内容...")
    
    messages = [
        {
            "user_id": 101,
            "content": "我今天学习了Vue.js的响应式原理",
            "role": "user",
            "session_id": 789012
        },
        {
            "user_id": 102,
            "content": "我对React Hooks有了更深的理解",
            "role": "user", 
            "session_id": 789012
        },
        {
            "user_id": 999,
            "content": "很好！前端框架的核心都是数据驱动视图更新",
            "role": "assistant",
            "session_id": 789012
        }
    ]
    
    try:
        response = session.post(
            f"{BASE_URL}/api/v1/memories/add",
            json=messages,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 创建记忆成功!")
            print(f"📥 返回结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查返回结果是否包含记忆内容
            if result.get("status") == "success":
                for user_result in result.get("results", []):
                    if "content" in user_result:
                        print(f"\n👤 用户 {user_result['user_id']} 的记忆内容:")
                        print(f"   📝 内容: {user_result.get('content', 'N/A')[:100]}...")
                        print(f"   🔗 记忆ID: {user_result.get('memory_id')}")
                        print(f"   📅 会话ID: {user_result.get('session_id')}")
                    else:
                        print(f"⚠️  用户 {user_result['user_id']} 的返回结果缺少content字段")
                        
            return True
        else:
            print(f"❌ 创建失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_query_memories_with_filters():
    """测试新的查询接口"""
    
    print("\n\n2️⃣  测试查询记忆接口...")
    
    # 测试1: 查询所有记忆
    print("\n📋 测试1: 查询所有记忆")
    try:
        response = session.get(
            f"{BASE_URL}/api/v1/mysql/memories",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 查询成功，共找到 {result.get('count', 0)} 条记忆")
            print(f"   筛选条件: {result.get('filters')}")
        else:
            print(f"❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
    
    # 测试2: 按user_id查询
    print("\n📋 测试2: 按user_id查询 (user_id=101)")
    try:
        response = session.get(
            f"{BASE_URL}/api/v1/mysql/memories?user_id=101",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 按用户查询成功，找到 {result.get('count', 0)} 条记忆")
            for memory in result.get('memories', [])[:2]:  # 只显示前2条
                print(f"   📝 {memory.get('content', 'N/A')[:50]}...")
        else:
            print(f"❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
    
    # 测试3: 按session_id查询
    print("\n📋 测试3: 按session_id查询 (session_id=789012)")
    try:
        response = session.get(
            f"{BASE_URL}/api/v1/mysql/memories?session_id=789012",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 按会话查询成功，找到 {result.get('count', 0)} 条记忆")
            for memory in result.get('memories', [])[:2]:  # 只显示前2条
                print(f"   👤 用户{memory.get('user_id')}: {memory.get('content', 'N/A')[:40]}...")
        else:
            print(f"❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
    
    # 测试4: 组合条件查询
    print("\n📋 测试4: 组合条件查询 (user_id=101 AND session_id=789012)")
    try:
        response = session.get(
            f"{BASE_URL}/api/v1/mysql/memories?user_id=101&session_id=789012",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 组合条件查询成功，找到 {result.get('count', 0)} 条记忆")
            print(f"   筛选条件: {result.get('filters')}")
        else:
            print(f"❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("       测试API更新功能")
    print("=" * 60)
    
    # 测试1: 创建记忆返回完整内容
    success1 = test_create_memory_with_content()
    
    # 测试2: 新的查询接口
    test_query_memories_with_filters()
    
    print("\n" + "=" * 60)
    if success1:
        print("✅ 所有功能测试完成！")
        print("\n💡 现在可以访问 http://localhost:8002/docs 查看更新的API:")
        print("   - /api/v1/memories/add: 返回结果包含记忆内容")
        print("   - /api/v1/mysql/memories: 支持user_id和session_id筛选")
    else:
        print("❌ 部分功能测试失败")
    
    print("\n" + "=" * 60)