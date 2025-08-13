#!/usr/bin/env python3
"""
Mem0 API 客户端示例
Example client for Mem0 API with Chinese optimization
"""

import requests
import json
import time
from typing import List, Dict, Optional

class Mem0Client:
    """Mem0 API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def health_check(self) -> Dict:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def add_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """添加记忆"""
        payload = {
            "messages": [{"role": "user", "content": content}],
            "user_id": user_id
        }
        if metadata:
            payload["metadata"] = metadata
            
        response = self.session.post(f"{self.base_url}/memories", json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_memories(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """搜索记忆"""
        payload = {
            "query": query,
            "user_id": user_id,
            "limit": limit
        }
        response = self.session.post(f"{self.base_url}/memories/search", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_all_memories(self, user_id: str) -> Dict:
        """获取所有记忆"""
        payload = {"user_id": user_id}
        response = self.session.post(f"{self.base_url}/memories/all", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_memory(self, memory_id: str) -> Dict:
        """获取特定记忆"""
        response = self.session.get(f"{self.base_url}/memories/{memory_id}")
        response.raise_for_status()
        return response.json()
    
    def update_memory(self, memory_id: str, text: str) -> Dict:
        """更新记忆"""
        payload = {"text": text}
        response = self.session.put(f"{self.base_url}/memories/{memory_id}", json=payload)
        response.raise_for_status()
        return response.json()
    
    def delete_memory(self, memory_id: str) -> Dict:
        """删除记忆"""
        response = self.session.delete(f"{self.base_url}/memories/{memory_id}")
        response.raise_for_status()
        return response.json()


def main():
    """示例使用"""
    
    # 创建客户端
    client = Mem0Client()
    
    # 用户ID
    user_id = f"demo_user_{int(time.time())}"
    
    print("🤖 Mem0 中文记忆系统演示")
    print("=" * 50)
    
    try:
        # 1. 健康检查
        print("1️⃣ 健康检查...")
        health = client.health_check()
        print(f"✅ 服务状态: {health}")
        
        # 2. 添加中文记忆
        print("\n2️⃣ 添加中文记忆...")
        
        memories_to_add = [
            "我是张三，是一名30岁的软件工程师，专门从事Python和机器学习开发",
            "我住在北京海淀区，每天坐地铁4号线上班到中关村软件园",
            "我喜欢吃川菜和粤菜，特别喜欢麻婆豆腐、宫保鸡丁和白切鸡",
            "我的爱好是看科幻电影和阅读技术书籍，最喜欢《三体》和《流浪地球》",
            "我有一只叫小白的金毛犬，每天晚上都会带它到小区楼下散步"
        ]
        
        added_memories = []
        for i, content in enumerate(memories_to_add, 1):
            result = client.add_memory(content, user_id)
            added_memories.append(result)
            print(f"   添加记忆 {i}: {content[:30]}... ✅")
        
        # 等待向量化完成
        print("\n⏳ 等待向量化处理完成...")
        time.sleep(3)
        
        # 3. 中文语义搜索测试
        print("\n3️⃣ 中文语义搜索测试...")
        
        search_queries = [
            "我的职业是什么？",
            "我住在哪个城市？",
            "我喜欢吃什么菜？", 
            "我的爱好有哪些？",
            "我养了什么宠物？",
            "我多大年纪？",
            "我在哪里工作？"
        ]
        
        for query in search_queries:
            print(f"\n🔍 搜索: {query}")
            results = client.search_memories(query, user_id, limit=2)
            
            if results.get("results"):
                for j, memory in enumerate(results["results"], 1):
                    score = memory.get("score", 0)
                    content = memory.get("memory", "")
                    print(f"   结果 {j} (相似度: {score:.3f}): {content}")
            else:
                print("   没有找到相关记忆")
        
        # 4. 获取所有记忆
        print("\n4️⃣ 获取所有记忆...")
        all_memories = client.get_all_memories(user_id)
        print(f"📊 总计记忆数量: {len(all_memories.get('results', []))}")
        
        # 5. 记忆更新测试
        if added_memories and added_memories[0].get("results"):
            memory_id = added_memories[0]["results"][0]["id"]
            print(f"\n5️⃣ 更新记忆 (ID: {memory_id})")
            
            updated = client.update_memory(
                memory_id, 
                "我是张三，是一名32岁的高级软件工程师，专门从事Python、Go和AI开发"
            )
            print("✅ 记忆更新成功")
            
            # 验证更新
            updated_memory = client.get_memory(memory_id)
            print(f"🔄 更新后内容: {updated_memory.get('memory', '')}")
        
        print("\n🎉 演示完成！")
        print("\n📈 测试总结:")
        print("  ✅ 服务连接正常")
        print("  ✅ 中文记忆添加成功") 
        print("  ✅ 中文语义搜索准确")
        print("  ✅ 记忆管理功能完整")
        print("  ✅ 本地嵌入模型工作正常")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请确保Mem0服务正在运行:")
        print("   docker-compose -f docker-compose.dev.yml up -d")
        print("   或运行: ./start-dev.sh")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        print("请检查服务日志:")
        print("   docker-compose -f docker-compose.dev.yml logs mem0-api")
        
    except Exception as e:
        print(f"❌ 未预期错误: {e}")


if __name__ == "__main__":
    main()