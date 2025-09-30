#!/usr/bin/env python3
"""
测试新的多用户记忆功能
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:9000"
API_TOKEN = "your-secret-key-change-this"  # 需要与.env中的API_SECRET_KEY一致

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_multiuser_memory():
    """测试多用户记忆添加"""
    
    # 模拟一个多用户对话
    test_request = {
        "messages": [
            {
                "role": "user",
                "content": "我叫张三，我是一名软件工程师，正在学习Python",
                "user_id": "user_001",
                "session_id": 12345
            },
            {
                "role": "assistant", 
                "content": "你好张三！很高兴认识你这位软件工程师。Python是一门很棒的语言，有什么特定的方面想学习吗？"
            },
            {
                "role": "user",
                "content": "我叫李四，我是产品经理，想了解一下技术开发流程",
                "user_id": "user_002", 
                "session_id": 12345
            },
            {
                "role": "assistant",
                "content": "你好李四！作为产品经理了解技术开发流程很重要。我来为你介绍一下敏捷开发流程..."
            },
            {
                "role": "user",
                "content": "谢谢！我特别想了解前端和后端是如何配合的",
                "user_id": "user_002",
                "session_id": 12345
            }
        ],
        "metadata": {
            "source": "group_chat",
            "topic": "技术学习讨论"
        }
    }
    
    print("🚀 测试多用户记忆添加...")
    print(f"📤 请求内容:\n{json.dumps(test_request, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/memories/add", 
            json=test_request,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容:\n{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ 多用户记忆添加测试成功!")
                
                # 测试搜索每个用户的记忆
                for user_id in ["user_001", "user_002"]:
                    print(f"\n🔍 搜索用户 {user_id} 的记忆...")
                    search_response = requests.post(
                        f"{BASE_URL}/api/v1/memories/search",
                        json={
                            "user_id": user_id,
                            "query": "学习 技能 职业",
                            "limit": 5
                        },
                        headers=headers
                    )
                    
                    if search_response.status_code == 200:
                        search_result = search_response.json()
                        print(f"📋 用户 {user_id} 的记忆搜索结果:")
                        for memory in search_result.get("memories", []):
                            print(f"  - {memory.get('content', 'N/A')}")
                    else:
                        print(f"❌ 用户 {user_id} 记忆搜索失败: {search_response.text}")
                
            else:
                print(f"⚠️  添加记忆返回状态: {result.get('status')}")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务已启动")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_single_user_multiple_messages():
    """测试单用户多条消息"""
    
    test_request = {
        "messages": [
            {
                "role": "user",
                "content": "我今天学会了使用Docker部署应用",
                "user_id": "user_003",
                "session_id": 67890
            },
            {
                "role": "assistant",
                "content": "太棒了！Docker是现代开发中很重要的工具。你部署了什么类型的应用？"
            },
            {
                "role": "user", 
                "content": "部署了一个Node.js的Web应用，还配置了MongoDB数据库",
                "user_id": "user_003",
                "session_id": 67890
            },
            {
                "role": "user",
                "content": "遇到了一些网络配置的问题，但最终解决了",
                "user_id": "user_003", 
                "session_id": 67890
            }
        ]
    }
    
    print("\n\n🚀 测试单用户多条消息记忆...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/memories/add",
            json=test_request, 
            headers=headers,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        result = response.json()
        print(f"📥 响应内容:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get("status") == "success":
            print("✅ 单用户多消息记忆添加测试成功!")
        else:
            print(f"⚠️  测试结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("       多用户记忆功能测试")
    print("=" * 60)
    
    # 测试1: 多用户对话
    test_multiuser_memory()
    
    # 测试2: 单用户多条消息
    test_single_user_multiple_messages()
    
    print("\n" + "=" * 60)
    print("测试完成！")