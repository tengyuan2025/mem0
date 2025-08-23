#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试记忆系统的添加和查询功能
"""

import requests
import json
import sys

def test_memory_api():
    base_url = "http://192.168.1.105:9000"
    
    print("🧪 测试记忆系统 API")
    print("=" * 40)
    
    # 1. 检查系统状态
    print("\n1. 检查系统状态...")
    try:
        response = requests.get(f"{base_url}/api/status", proxies={'http': None, 'https': None})
        status = response.json()
        print(f"   Qdrant: {'✅' if status.get('qdrant_status') else '❌'}")
        print(f"   Memory: {'✅' if status.get('memory_system') else '❌'}")
        print(f"   模型: {status.get('embedder_model', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 状态检查失败: {e}")
        return
    
    # 2. 添加测试记忆
    print("\n2. 添加测试记忆...")
    test_data = {
        "text": "我今天学习了Python编程，觉得很有意思",
        "user_id": "test_user_123"  # 明确指定用户ID
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/memories", 
            headers={"Content-Type": "application/json"},
            json=test_data,
            proxies={'http': None, 'https': None}
        )
        add_result = response.json()
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(add_result, ensure_ascii=False, indent=2)}")
        
        if not add_result.get('success'):
            print("   ❌ 添加失败")
            return
            
    except Exception as e:
        print(f"   ❌ 添加记忆失败: {e}")
        return
    
    # 3. 查询所有记忆（路径参数版本）
    print("\n3. 查询所有记忆（路径参数版本）...")
    try:
        response = requests.get(
            f"{base_url}/api/memories/test_user_123",
            proxies={'http': None, 'https': None}
        )
        memories = response.json()
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(memories, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
    # 4. 查询所有记忆（查询参数版本）
    print("\n4. 查询所有记忆（查询参数版本）...")
    try:
        response = requests.get(
            f"{base_url}/api/all-memories?user_id=test_user_123",
            proxies={'http': None, 'https': None}
        )
        memories = response.json()
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(memories, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
    # 5. 搜索记忆
    print("\n5. 搜索记忆...")
    search_data = {
        "query": "Python",
        "user_id": "test_user_123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/search",
            headers={"Content-Type": "application/json"},
            json=search_data,
            proxies={'http': None, 'https': None}
        )
        search_result = response.json()
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(search_result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   ❌ 搜索失败: {e}")

if __name__ == "__main__":
    test_memory_api()