#!/usr/bin/env python3
"""
Mem0 Memory API 客户端示例
演示如何使用 API 进行记忆操作
"""
import asyncio
import json
import requests
import time
from typing import Dict, Any, List


class Mem0APIClient:
    """Mem0 Memory API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def health_check(self) -> Dict[str, Any]:
        """检查 API 健康状态"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def create_memory(self, messages: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """创建记忆"""
        data = {
            "messages": messages,
            "user_id": user_id,
            **kwargs
        }
        response = self.session.post(f"{self.base_url}/memories", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """获取记忆"""
        response = self.session.get(f"{self.base_url}/memories/{memory_id}")
        response.raise_for_status()
        return response.json()
    
    def search_memories(self, query: str, user_id: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """搜索记忆"""
        data = {
            "query": query,
            "user_id": user_id,
            "limit": limit,
            **kwargs
        }
        response = self.session.post(f"{self.base_url}/memories/search", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_all_memories(self, user_id: str, limit: int = 100, **kwargs) -> Dict[str, Any]:
        """获取所有记忆"""
        data = {
            "user_id": user_id,
            "limit": limit,
            **kwargs
        }
        response = self.session.post(f"{self.base_url}/memories/all", json=data)
        response.raise_for_status()
        return response.json()
    
    def update_memory(self, memory_id: str, data: str) -> Dict[str, Any]:
        """更新记忆"""
        payload = {"data": data}
        response = self.session.put(f"{self.base_url}/memories/{memory_id}", json=payload)
        response.raise_for_status()
        return response.json()
    
    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """删除记忆"""
        response = self.session.delete(f"{self.base_url}/memories/{memory_id}")
        response.raise_for_status()
        return response.json()
    
    def delete_all_memories(self, user_id: str) -> Dict[str, Any]:
        """删除所有记忆"""
        data = {"user_id": user_id}
        response = self.session.delete(f"{self.base_url}/memories", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_memory_history(self, memory_id: str) -> Dict[str, Any]:
        """获取记忆历史"""
        response = self.session.get(f"{self.base_url}/memories/{memory_id}/history")
        response.raise_for_status()
        return response.json()


def print_section(title: str):
    """打印节标题"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")


def print_json(data: Dict[str, Any]):
    """美化打印 JSON 数据"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def demo_basic_operations():
    """演示基础操作"""
    client = Mem0APIClient()
    user_id = "demo-user-123"
    
    try:
        print_section("健康检查")
        health = client.health_check()
        print_json(health)
        
        print_section("创建记忆")
        # 创建一些示例记忆
        memories_to_create = [
            "我喜欢吃披萨，尤其是意大利辣香肠披萨",
            "我的生日是 3月15日",
            "我住在北京，工作是软件工程师",
            "我最喜欢的颜色是蓝色",
            "我有一只名叫 Max 的金毛犬"
        ]
        
        created_memories = []
        for message in memories_to_create:
            result = client.create_memory(message, user_id)
            print(f"创建记忆: {message}")
            if result["results"]:
                memory_id = result["results"][0]["id"]
                created_memories.append(memory_id)
                print(f"记忆 ID: {memory_id}")
            time.sleep(1)  # 避免请求过快
        
        print(f"\n成功创建 {len(created_memories)} 条记忆")
        
        print_section("获取记忆")
        if created_memories:
            memory_id = created_memories[0]
            memory = client.get_memory(memory_id)
            print(f"获取记忆 {memory_id}:")
            print_json(memory)
        
        print_section("搜索记忆")
        search_queries = [
            "食物偏好",
            "个人信息",
            "宠物",
            "颜色喜好"
        ]
        
        for query in search_queries:
            print(f"\n搜索查询: {query}")
            results = client.search_memories(query, user_id, limit=3)
            print(f"找到 {len(results['results'])} 条相关记忆:")
            for result in results["results"]:
                print(f"- {result['memory']} (相似度: {result.get('score', 'N/A')})")
        
        print_section("获取所有记忆")
        all_memories = client.get_all_memories(user_id, limit=10)
        print(f"用户 {user_id} 共有 {len(all_memories['results'])} 条记忆:")
        for memory in all_memories["results"]:
            print(f"- {memory['memory']}")
        
        print_section("更新记忆")
        if created_memories:
            memory_id = created_memories[0]
            original_memory = client.get_memory(memory_id)
            print(f"原记忆: {original_memory['memory']}")
            
            updated_result = client.update_memory(memory_id, "我超级喜欢吃各种口味的披萨，包括意大利辣香肠、玛格丽特和夏威夷披萨")
            print_json(updated_result)
            
            updated_memory = client.get_memory(memory_id)
            print(f"更新后记忆: {updated_memory['memory']}")
        
        print_section("记忆历史")
        if created_memories:
            memory_id = created_memories[0]
            history = client.get_memory_history(memory_id)
            print(f"记忆 {memory_id} 的历史:")
            print_json(history)
        
        print_section("删除特定记忆")
        if len(created_memories) > 1:
            memory_id = created_memories[-1]
            result = client.delete_memory(memory_id)
            print(f"删除记忆 {memory_id}:")
            print_json(result)
            
            # 验证删除
            try:
                client.get_memory(memory_id)
                print("错误: 记忆仍然存在")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print("确认: 记忆已成功删除")
                else:
                    raise
        
        print_section("删除所有记忆")
        delete_all_result = client.delete_all_memories(user_id)
        print_json(delete_all_result)
        
        # 验证所有记忆已删除
        remaining_memories = client.get_all_memories(user_id)
        print(f"剩余记忆数量: {len(remaining_memories['results'])}")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        raise


def demo_advanced_features():
    """演示高级功能"""
    client = Mem0APIClient()
    user_id = "demo-advanced-user"
    
    try:
        print_section("高级功能演示")
        
        print("1. 创建带元数据的记忆")
        result = client.create_memory(
            "我在 2024年1月加入了这家公司，职位是高级软件工程师",
            user_id,
            metadata={"category": "work", "importance": "high"},
            infer=True
        )
        print_json(result)
        
        print("\n2. 使用过滤器搜索")
        search_result = client.search_memories(
            "工作",
            user_id,
            filters={"category": "work"},
            threshold=0.5
        )
        print_json(search_result)
        
        print("\n3. 程序记忆（需要 agent_id）")
        try:
            procedural_result = client.create_memory(
                [
                    {"role": "user", "content": "如何制作咖啡？"},
                    {"role": "assistant", "content": "首先准备咖啡豆和热水，然后按照以下步骤..."}
                ],
                user_id="procedural-user",
                agent_id="coffee-assistant", 
                memory_type="procedural_memory"
            )
            print_json(procedural_result)
        except Exception as e:
            print(f"程序记忆创建失败: {e}")
        
        # 清理
        client.delete_all_memories(user_id)
        
    except Exception as e:
        print(f"高级功能演示出现错误: {e}")


def main():
    """主函数"""
    print("Mem0 Memory API 客户端演示")
    print("确保 API 服务器正在运行 (http://localhost:8000)")
    
    try:
        print("\n开始基础操作演示...")
        demo_basic_operations()
        
        print("\n开始高级功能演示...")
        demo_advanced_features()
        
        print_section("演示完成")
        print("所有演示已成功完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到 API 服务器")
        print("请确保服务器正在运行: python tests/apis/run_api_server.py")
    except Exception as e:
        print(f"演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()