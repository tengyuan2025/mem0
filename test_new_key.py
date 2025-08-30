#!/usr/bin/env python3
"""
测试新的API密钥
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
API_TOKEN = "tengyuan2025"  # 新的API密钥

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_new_api_key():
    """测试新的API密钥"""
    
    # 测试数据
    messages = [
        {
            "user_id": 1,
            "content": "测试新的API密钥功能",
            "role": "user",
            "session_id": 123456
        }
    ]
    
    print("🔑 测试新API密钥: tengyuan2025")
    
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
            print("✅ 新API密钥认证成功!")
            print(f"📥 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        elif response.status_code == 403:
            print("❌ 403错误：API密钥认证失败")
        else:
            print(f"❌ 其他错误: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_new_api_key()