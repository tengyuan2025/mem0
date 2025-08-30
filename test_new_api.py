#!/usr/bin/env python3
"""
测试新的API格式 - 直接传入消息数组
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_TOKEN = "your-secret-key-change-this"  # 需要与.env中的API_SECRET_KEY一致

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_weather_conversation():
    """测试天气对话场景"""
    
    # 按照新格式构建请求 - 直接是数组
    messages = [
        {
            "user_id": 1,
            "content": "今天可太热了",
            "role": "user"
        },
        {
            "user_id": 2,
            "content": "是啊 都快40度了吧",
            "role": "user"
        },
        {
            "user_id": 3,
            "content": "北京今天的最高温度是34度哦",
            "role": "assistant"
        },
        {
            "user_id": 1,
            "content": "那还好，我这边武汉感觉更热",
            "role": "user"
        },
        {
            "user_id": 2,
            "content": "我在深圳，湿度太高了，体感温度更难受",
            "role": "user"
        }
    ]
    
    print("🌡️  测试天气对话场景...")
    print(f"📤 发送 {len(messages)} 条消息")
    print(f"   - 用户1: 在武汉，觉得很热")
    print(f"   - 用户2: 在深圳，抱怨湿度高")
    print(f"   - 用户3(助手): 提供北京温度信息")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/memories/add",
            json=messages,  # 直接发送数组
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应内容:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("status") == "success":
                print("\n✅ 记忆添加成功!")
                
                # 显示每个用户的记忆
                for user_result in result.get("results", []):
                    print(f"\n👤 用户 {user_result['user_id']}:")
                    print(f"   状态: {user_result.get('status')}")
                    if user_result.get('memory_id'):
                        print(f"   记忆ID: {user_result['memory_id']}")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务已启动")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_tech_discussion():
    """测试技术讨论场景"""
    
    messages = [
        {
            "user_id": "alice",
            "content": "我最近在学习Docker，感觉容器化部署真的很方便",
            "role": "user"
        },
        {
            "user_id": "bob",
            "content": "确实，我们公司已经全面容器化了，用Kubernetes管理",
            "role": "user"
        },
        {
            "user_id": "assistant_01",
            "content": "Docker和Kubernetes是现代DevOps的核心技术栈。你们有使用CI/CD吗？",
            "role": "assistant"
        },
        {
            "user_id": "alice",
            "content": "我们用的是GitLab CI，配合Docker Registry很方便",
            "role": "user"
        },
        {
            "user_id": "bob",
            "content": "我们是Jenkins + Harbor，不过正在考虑迁移到GitHub Actions",
            "role": "user"
        }
    ]
    
    print("\n\n💻 测试技术讨论场景...")
    print(f"📤 发送 {len(messages)} 条消息")
    print(f"   - alice: 学习Docker，使用GitLab CI")
    print(f"   - bob: 使用K8s，Jenkins + Harbor")
    print(f"   - assistant: 询问CI/CD使用情况")
    
    try:
        response = requests.post(
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
                print("\n✅ 技术讨论记忆添加成功!")
                
                # 测试搜索Alice的记忆
                print("\n🔍 搜索alice的记忆...")
                search_response = requests.post(
                    f"{BASE_URL}/api/v1/memories/search",
                    json={
                        "user_id": "alice",
                        "query": "Docker GitLab CI/CD",
                        "limit": 5
                    },
                    headers=headers
                )
                
                if search_response.status_code == 200:
                    memories = search_response.json().get("memories", [])
                    print(f"找到 {len(memories)} 条相关记忆")
                    for mem in memories[:2]:
                        print(f"  - {mem.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_mixed_roles():
    """测试混合角色 - 只有user角色的消息会生成记忆"""
    
    messages = [
        {
            "user_id": "user_123",
            "content": "我想学习Python编程",
            "role": "user"
        },
        {
            "user_id": "ai_assistant",
            "content": "Python是很好的入门语言，建议从基础语法开始",
            "role": "assistant"
        },
        {
            "user_id": "user_456",
            "content": "我也想学，有推荐的教程吗？",
            "role": "user"
        },
        {
            "user_id": "system",
            "content": "系统提示：已记录学习需求",
            "role": "assistant"
        }
    ]
    
    print("\n\n🎭 测试混合角色场景...")
    print(f"📤 发送 {len(messages)} 条消息")
    print(f"   - 2个user角色（应生成记忆）")
    print(f"   - 2个assistant角色（不应生成记忆）")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/memories/add",
            json=messages,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应内容:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 统计生成的记忆数量
            successful_memories = [r for r in result.get("results", []) if r.get("status") == "success"]
            print(f"\n📊 生成了 {len(successful_memories)} 条记忆（预期：2条，仅user角色）")
            
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("       新API格式测试")
    print("=" * 60)
    
    # 测试1: 天气对话
    test_weather_conversation()
    
    # 测试2: 技术讨论
    test_tech_discussion()
    
    # 测试3: 混合角色
    test_mixed_roles()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("\n💡 说明：")
    print("- 新API直接接收消息数组")
    print("- 每个消息包含: user_id, content, role")
    print("- 只为role='user'的用户生成记忆")
    print("- 记忆总结会考虑完整对话上下文")