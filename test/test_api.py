#!/usr/bin/env python3
"""
Mem0 API 测试脚本
用于测试部署的Mem0服务是否正常工作
"""

import os
# 取消代理设置，避免本地测试问题
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

import requests
import json
import time
from typing import Dict, Any

# API配置
API_BASE_URL = "http://localhost:9000"
API_KEY = "your-secret-key-change-this"  # 需要与.env中的API_SECRET_KEY一致

# 测试用户
TEST_USER_ID = "test_user_001"

def print_response(response_name: str, response: Dict[str, Any]):
    """打印格式化的响应"""
    print(f"\n📋 {response_name}:")
    print(json.dumps(response, indent=2, ensure_ascii=False))

def test_health_check():
    """测试健康检查"""
    print("\n" + "="*50)
    print("1️⃣  测试健康检查")
    print("="*50)
    
    response = requests.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
    print_response("健康检查", response.json())
    print("✅ 健康检查通过")

def test_root_endpoint():
    """测试根路径"""
    print("\n" + "="*50)
    print("2️⃣  测试服务信息")
    print("="*50)
    
    response = requests.get(f"{API_BASE_URL}/")
    assert response.status_code == 200
    print_response("服务信息", response.json())
    print("✅ 服务信息获取成功")

def test_add_memory():
    """测试添加记忆"""
    print("\n" + "="*50)
    print("3️⃣  测试添加记忆")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 添加第一条记忆
    data1 = {
        "user_id": TEST_USER_ID,
        "messages": [
            {"role": "user", "content": "我喜欢喝咖啡，特别是拿铁。"},
            {"role": "assistant", "content": "了解了，您喜欢喝拿铁咖啡。"}
        ],
        "metadata": {"category": "preference", "topic": "beverage"}
    }
    
    response1 = requests.post(
        f"{API_BASE_URL}/api/v1/memories/add",
        headers=headers,
        json=data1
    )
    assert response1.status_code == 200
    result1 = response1.json()
    print_response("添加记忆1", result1)
    
    # 添加第二条记忆
    data2 = {
        "user_id": TEST_USER_ID,
        "messages": [
            {"role": "user", "content": "我住在北京，在一家科技公司工作。"},
            {"role": "assistant", "content": "明白了，您在北京的科技公司工作。"}
        ],
        "metadata": {"category": "personal", "topic": "work"}
    }
    
    response2 = requests.post(
        f"{API_BASE_URL}/api/v1/memories/add",
        headers=headers,
        json=data2
    )
    assert response2.status_code == 200
    result2 = response2.json()
    print_response("添加记忆2", result2)
    
    print("✅ 记忆添加成功")
    return result1.get("memory_id"), result2.get("memory_id")

def test_search_memory():
    """测试搜索记忆"""
    print("\n" + "="*50)
    print("4️⃣  测试搜索记忆")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 搜索咖啡相关的记忆
    data = {
        "user_id": TEST_USER_ID,
        "query": "咖啡",
        "limit": 5
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/memories/search",
        headers=headers,
        json=data
    )
    assert response.status_code == 200
    results = response.json()
    print_response("搜索结果（咖啡）", results)
    
    # 搜索工作相关的记忆
    data2 = {
        "user_id": TEST_USER_ID,
        "query": "工作地点",
        "limit": 5
    }
    
    response2 = requests.post(
        f"{API_BASE_URL}/api/v1/memories/search",
        headers=headers,
        json=data2
    )
    assert response2.status_code == 200
    results2 = response2.json()
    print_response("搜索结果（工作）", results2)
    
    print("✅ 记忆搜索成功")

def test_chat_with_memory():
    """测试带记忆的聊天"""
    print("\n" + "="*50)
    print("5️⃣  测试带记忆的聊天")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 测试聊天1：询问用户喜好
    data1 = {
        "user_id": TEST_USER_ID,
        "message": "你知道我喜欢喝什么吗？",
        "use_memory": True
    }
    
    response1 = requests.post(
        f"{API_BASE_URL}/api/v1/chat",
        headers=headers,
        json=data1
    )
    assert response1.status_code == 200
    result1 = response1.json()
    print_response("聊天响应1", result1)
    
    # 测试聊天2：询问工作信息
    data2 = {
        "user_id": TEST_USER_ID,
        "message": "我在哪里工作？",
        "use_memory": True
    }
    
    response2 = requests.post(
        f"{API_BASE_URL}/api/v1/chat",
        headers=headers,
        json=data2
    )
    assert response2.status_code == 200
    result2 = response2.json()
    print_response("聊天响应2", result2)
    
    print("✅ 聊天功能正常")

def test_get_user_memories():
    """测试获取用户所有记忆"""
    print("\n" + "="*50)
    print("6️⃣  测试获取用户所有记忆")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(
        f"{API_BASE_URL}/api/v1/users/{TEST_USER_ID}/memories",
        headers=headers,
        params={"limit": 10}
    )
    assert response.status_code == 200
    results = response.json()
    print_response("用户所有记忆", results)
    print(f"✅ 成功获取 {results['count']} 条记忆")

def test_update_memory(memory_id: str):
    """测试更新记忆"""
    if not memory_id:
        print("\n⚠️  跳过更新测试（没有记忆ID）")
        return
        
    print("\n" + "="*50)
    print("7️⃣  测试更新记忆")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    data = {
        "memory_id": memory_id,
        "content": "用户特别喜欢喝拿铁咖啡，每天早上都要喝一杯。",
        "metadata": {"updated": True, "importance": "high"}
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/memories/update",
        headers=headers,
        json=data
    )
    assert response.status_code == 200
    result = response.json()
    print_response("更新结果", result)
    print("✅ 记忆更新成功")

def test_delete_memory():
    """测试删除记忆"""
    print("\n" + "="*50)
    print("8️⃣  测试删除记忆")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 删除测试用户的所有记忆
    data = {
        "user_id": TEST_USER_ID
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/memories/delete",
        headers=headers,
        json=data
    )
    assert response.status_code == 200
    result = response.json()
    print_response("删除结果", result)
    print("✅ 记忆删除成功")

def main():
    """运行所有测试"""
    print("\n" + "🚀"*25)
    print("         Mem0 API 测试套件")
    print("🚀"*25)
    
    try:
        # 等待服务启动
        print("\n⏳ 等待服务完全启动...")
        time.sleep(2)
        
        # 运行测试
        test_health_check()
        test_root_endpoint()
        
        memory_id1, memory_id2 = test_add_memory()
        time.sleep(1)  # 等待索引更新
        
        test_search_memory()
        test_chat_with_memory()
        test_get_user_memories()
        
        if memory_id1:
            test_update_memory(memory_id1)
        
        # 清理测试数据
        test_delete_memory()
        
        print("\n" + "="*50)
        print("✅✅✅ 所有测试通过！服务运行正常 ✅✅✅")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务")
        print("请确保服务已启动：")
        print("1. 运行 ./start.sh")
        print("2. 检查服务是否在 http://localhost:9000 运行")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()