#!/usr/bin/env python3
"""
测试搜索记忆功能
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

def search_memories(user_id, query="", limit=5):
    """搜索用户记忆"""
    try:
        response = session.post(
            f"{BASE_URL}/api/v1/memories/search",
            json={
                "user_id": user_id,
                "query": query,
                "limit": limit
            },
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 用户 {user_id} 的记忆搜索结果:")
            # Handle different response formats
            if isinstance(result, dict):
                memories = result.get("memories", [])
            elif isinstance(result, list):
                memories = result
            else:
                memories = []
                
            print(f"   找到 {len(memories)} 条记忆")
            
            for i, memory in enumerate(memories[:3]):  # 只显示前3条
                print(f"\n   记忆 {i+1}:")
                if isinstance(memory, dict):
                    print(f"     ID: {memory.get('id', memory.get('memory_id', 'N/A'))}")
                    print(f"     内容: {memory.get('content', 'N/A')[:100]}...")
                    if memory.get('metadata'):
                        print(f"     元数据: {memory.get('metadata')}")
                else:
                    print(f"     内容: {str(memory)[:100]}...")
                    
        else:
            print(f"❌ 搜索失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 搜索异常: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("       记忆搜索测试")
    print("=" * 60)
    
    # 搜索用户1的记忆
    search_memories("1", "天气")
    
    print("\n" + "-" * 40)
    
    # 搜索用户2的记忆  
    search_memories("2", "温度")
    
    print("\n" + "=" * 60)