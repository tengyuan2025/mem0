#!/usr/bin/env python3
"""
Mem0 最小化版本测试脚本
"""

import os
import requests
import json

# 取消代理设置
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

API_BASE_URL = "http://localhost:9000"
API_KEY = "your-secret-key-change-this"
TEST_USER_ID = "test_user_001"

def test_service():
    """测试服务基本功能"""
    
    print("🚀 开始测试Mem0最小化版本")
    print("=" * 50)
    
    # 1. 测试健康检查
    print("\n1️⃣ 测试健康检查...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 2. 测试服务信息
    print("\n2️⃣ 测试服务信息...")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print("✅ 服务信息获取成功")
            print(f"服务: {info.get('service')}")
            print(f"版本: {info.get('version')}")
            print(f"嵌入模型: {info.get('embedding_model')}")
        else:
            print(f"❌ 获取服务信息失败: {response.status_code}")
    except Exception as e:
        print(f"⚠️ 获取服务信息异常: {e}")
    
    # 3. 测试添加记忆
    print("\n3️⃣ 测试添加记忆...")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    memory_data = {
        "user_id": TEST_USER_ID,
        "messages": [
            {"role": "user", "content": "我喜欢喝咖啡，特别是拿铁"},
            {"role": "assistant", "content": "了解了，您喜欢喝拿铁咖啡"}
        ],
        "metadata": {"category": "preference"}
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/memories/add",
            headers=headers,
            json=memory_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ 记忆添加成功")
            print(f"记忆ID: {result.get('memory_id')}")
            print(f"内容: {result.get('content')}")
            memory_id = result.get('memory_id')
        else:
            print(f"❌ 添加记忆失败: {response.status_code}")
            print(f"错误: {response.text}")
            return
    except Exception as e:
        print(f"❌ 添加记忆异常: {e}")
        return
    
    # 4. 测试搜索记忆
    print("\n4️⃣ 测试搜索记忆...")
    search_data = {
        "user_id": TEST_USER_ID,
        "query": "咖啡",
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/memories/search",
            headers=headers,
            json=search_data,
            timeout=10
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 搜索成功，找到 {len(results)} 条记忆")
            for memory in results:
                print(f"  - {memory.get('content')} (分数: {memory.get('score')})")
        else:
            print(f"❌ 搜索记忆失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 搜索记忆异常: {e}")
    
    # 5. 测试聊天功能
    print("\n5️⃣ 测试聊天功能...")
    chat_data = {
        "user_id": TEST_USER_ID,
        "message": "你知道我喜欢喝什么吗？",
        "use_memory": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat",
            headers=headers,
            json=chat_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ 聊天功能正常")
            print(f"回复: {result.get('response')}")
        else:
            print(f"❌ 聊天功能失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 聊天功能异常: {e}")
    
    # 6. 测试获取用户记忆
    print("\n6️⃣ 测试获取用户记忆...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/users/{TEST_USER_ID}/memories",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取用户记忆成功，共 {result.get('count')} 条")
        else:
            print(f"❌ 获取用户记忆失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取用户记忆异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    
    print("\n💡 提示：")
    print("- 当前使用简单文本匹配（未安装sentence-transformers）")
    print("- 如需使用本地中文嵌入模型，请安装: pip install sentence-transformers")
    print("- 然后在.env中配置: EMBEDDING_PROVIDER=local_huggingface")

if __name__ == "__main__":
    test_service()