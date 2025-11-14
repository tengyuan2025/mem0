#!/usr/bin/env python3
"""
测试带有session_id的API功能
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
API_TOKEN = "your-secret-key-change-this"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_session_id_memory():
    """测试带有session_id的记忆添加"""
    
    # 测试数据：包含session_id的消息
    messages = [
        {
            "user_id": 1,
            "content": "我最近在学习Python编程",
            "role": "user",
            "session_id": 123456
        },
        {
            "user_id": 2, 
            "content": "我也想学，有什么好的资源推荐吗？",
            "role": "user",
            "session_id": 123456
        },
        {
            "user_id": 3,
            "content": "建议从官方教程开始，然后做一些实际项目",
            "role": "assistant",
            "session_id": 123456
        }
    ]
    
    print("🧪 测试带session_id的记忆添加...")
    print(f"📤 发送 {len(messages)} 条消息，session_id: 123456")
    
    try:
        response = session.post(
            f"{BASE_URL}/api/v1/memories/add",
            json=messages,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应内容:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("status") == "success":
                print("\n✅ 带session_id的记忆添加成功!")
                
                # 显示每个用户的记忆
                for user_result in result.get("results", []):
                    print(f"\n👤 用户 {user_result['user_id']}:")
                    print(f"   状态: {user_result.get('status')}")
                    if user_result.get('memory_id'):
                        print(f"   记忆ID: {user_result['memory_id']}")
                return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("       Session ID 功能测试")
    print("=" * 60)
    
    # 测试session_id功能
    success = test_session_id_memory()
    
    if success:
        print("\n✅ Session ID 功能测试通过！")
        print("\n📋 现在可以访问 http://localhost:8002/docs 查看更新的API文档")
        print("   每个消息对象现在都包含 session_id 字段")
    else:
        print("\n❌ Session ID 功能测试失败")
    
    print("\n" + "=" * 60)