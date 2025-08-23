#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Qdrant + 中文优化配置
高性能向量存储 + DeepSeek API + 中文嵌入模型
"""

import os
import sys
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# 方案1: Qdrant + HuggingFace 中文嵌入（推荐）
QDRANT_HUGGINGFACE_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_chinese_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,  # BAAI/bge-large-zh-v1.5
            "on_disk": True,  # 持久化存储
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",  # 最佳中文嵌入模型
        },
    },
}

# 方案2: Qdrant + OpenAI 嵌入
QDRANT_OPENAI_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_openai_memories",
            "host": "localhost", 
            "port": 6333,
            "embedding_model_dims": 1536,  # OpenAI text-embedding-3-small
            "on_disk": True,
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9,
        },
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
        },
    },
}

# 方案3: Qdrant + Ollama 嵌入
QDRANT_OLLAMA_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_ollama_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,  # bge-m3
            "on_disk": True,
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9,
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "bge-m3:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}


class DeepSeekQdrantMemory:
    """DeepSeek + Qdrant 中文记忆系统"""
    
    def __init__(self, config_type="huggingface", user_id="默认用户"):
        """
        初始化 DeepSeek + Qdrant 中文记忆系统
        
        Args:
            config_type: "huggingface", "openai", "ollama"  
            user_id: 用户标识
        """
        self.user_id = user_id
        
        # 选择配置
        configs = {
            "huggingface": QDRANT_HUGGINGFACE_CONFIG,
            "openai": QDRANT_OPENAI_CONFIG,
            "ollama": QDRANT_OLLAMA_CONFIG,
        }
        
        if config_type not in configs:
            raise ValueError(f"配置类型必须是: {list(configs.keys())}")
        
        config = configs[config_type]
        
        try:
            self.memory = Memory.from_config(config)
            print(f"✅ DeepSeek + Qdrant 中文记忆系统初始化成功")
            print(f"✅ 用户: {user_id}")
            print(f"✅ LLM: DeepSeek API")
            print(f"✅ 向量存储: Qdrant (localhost:6333)")
            print(f"✅ 嵌入模型: {config_type}")
            print(f"✅ 集合名称: {config['vector_store']['config']['collection_name']}")
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            
            # 提供详细的错误排查建议
            if "Connection refused" in str(e) or "connection" in str(e).lower():
                print("\n🔧 Qdrant 连接失败，请检查:")
                print("   1. Qdrant 服务是否运行: docker ps | grep qdrant")
                print("   2. 启动 Qdrant: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
                print("   3. 检查端口是否被占用: lsof -i :6333")
            elif "OPENAI_API_KEY" in str(e) and config_type == "openai":
                print("提示: OpenAI 嵌入需要设置 OPENAI_API_KEY 环境变量")
            elif "ollama" in str(e).lower() and config_type == "ollama":
                print("提示: Ollama 嵌入需要先运行 'ollama serve' 并下载模型")
            sys.exit(1)
        
        self._print_help()
    
    def _print_help(self):
        """打印帮助信息"""
        print("\n" + "="*70)
        print("🚀 DeepSeek + Qdrant 高性能中文记忆系统")
        print("="*70)
        print("🌟 特点:")
        print("  • LLM: DeepSeek API (强大的中文理解和生成)")
        print("  • 向量存储: Qdrant (高性能、可扩展)")
        print("  • 嵌入: 中文优化的嵌入模型")
        print("  • 持久化: 数据自动保存到磁盘")
        print()
        print("📝 命令:")
        print("  💾 /添加 <文本>        - 添加新记忆")
        print("  🔍 /搜索 <关键词>      - 搜索相关记忆")
        print("  🤖 /分析 <文本>        - DeepSeek 分析并记忆")
        print("  💬 /对话 <消息>        - 基于记忆的智能对话")
        print("  📚 /记忆 或 /m         - 查看所有记忆") 
        print("  📊 /统计 或 /s         - 显示记忆统计")
        print("  🔧 /集合              - 显示 Qdrant 集合信息")
        print("  🗑️  /清除 或 /c        - 清除所有记忆")
        print("  ❓ /帮助 或 /h         - 显示帮助")
        print("  👋 /退出 或 /q         - 退出程序")
        print("="*70 + "\n")
    
    def add_memory(self, text, metadata=None):
        """添加记忆"""
        try:
            result = self.memory.add(text, user_id=self.user_id, metadata=metadata)
            print(f"✅ 记忆已保存到 Qdrant")
            return result
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None
    
    def search_memories(self, query, limit=5):
        """搜索相关记忆"""
        try:
            results = self.memory.search(
                query=query,
                user_id=self.user_id,
                limit=limit
            )
            
            if results["results"]:
                print(f"\n🔍 在 Qdrant 中找到 {len(results['results'])} 条相关记忆：")
                print("-" * 60)
                for i, mem in enumerate(results["results"], 1):
                    score = mem.get('score', 0)
                    memory_text = mem['memory']
                    print(f"{i}. {memory_text}")
                    print(f"   💯 相关度: {score:.4f}")
                    if 'metadata' in mem and mem['metadata']:
                        print(f"   🏷️  标签: {mem['metadata']}")
                    print()
            else:
                print("❌ 未找到相关记忆")
            
            return results
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return None
    
    def show_all_memories(self):
        """显示所有记忆"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            
            if memories["results"]:
                print(f"\n📚 Qdrant 中共有 {len(memories['results'])} 条记忆：")
                print("-" * 60)
                for i, mem in enumerate(memories["results"], 1):
                    print(f"{i}. {mem['memory']}")
                    print(f"   🆔 ID: {mem['id'][:16]}...")
                    if 'metadata' in mem and mem['metadata']:
                        print(f"   🏷️  标签: {mem['metadata']}")
                    print()
            else:
                print("📭 Qdrant 中暂无记忆")
            
            return memories
        except Exception as e:
            print(f"❌ 获取记忆失败: {e}")
            return None
    
    def show_statistics(self):
        """显示统计信息"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            total = len(memories["results"])
            
            # 按类型统计
            types = {}
            for mem in memories["results"]:
                mem_type = "普通"
                if 'metadata' in mem and mem['metadata'] and 'type' in mem['metadata']:
                    mem_type = mem['metadata']['type']
                types[mem_type] = types.get(mem_type, 0) + 1
            
            print(f"\n📊 Qdrant 记忆统计:")
            print(f"   总计: {total} 条记忆")
            print(f"   向量数据库: Qdrant")
            print(f"   集合名称: {self.memory.vector_store.collection_name}")
            print(f"   类型分布:")
            for t, count in types.items():
                print(f"     • {t}: {count} 条")
            
        except Exception as e:
            print(f"❌ 统计失败: {e}")
    
    def show_collection_info(self):
        """显示 Qdrant 集合信息"""
        try:
            # 尝试获取集合信息
            collection_name = self.memory.vector_store.collection_name
            print(f"\n🔧 Qdrant 集合信息:")
            print(f"   集合名称: {collection_name}")
            print(f"   服务器: localhost:6333")
            print(f"   向量维度: {self.memory.vector_store.embedding_model_dims}")
            
            # 获取记忆数量
            memories = self.memory.get_all(user_id=self.user_id)
            print(f"   当前记忆数量: {len(memories['results'])}")
            
        except Exception as e:
            print(f"❌ 获取集合信息失败: {e}")
    
    def clear_memories(self):
        """清除所有记忆"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            count = len(memories["results"])
            
            if count == 0:
                print("📭 Qdrant 中没有需要清除的记忆")
                return
            
            confirm = input(f"⚠️  确定要从 Qdrant 中清除 {count} 条记忆吗？(y/n): ")
            if confirm.lower() in ['y', 'yes', '是', '确定']:
                for mem in memories["results"]:
                    self.memory.delete(memory_id=mem['id'])
                print(f"✅ 已从 Qdrant 清除 {count} 条记忆")
            else:
                print("❌ 取消清除")
        except Exception as e:
            print(f"❌ 清除失败: {e}")
    
    def process_command(self, text):
        """处理命令"""
        text = text.strip()
        
        # 退出
        if text in ['/退出', '/q', '/exit', '/quit']:
            return False
        
        # 帮助
        elif text in ['/帮助', '/h', '/help']:
            self._print_help()
        
        # 显示记忆
        elif text in ['/记忆', '/m', '/memories']:
            self.show_all_memories()
        
        # 统计
        elif text in ['/统计', '/s', '/stats']:
            self.show_statistics()
        
        # 集合信息
        elif text in ['/集合', '/collection', '/info']:
            self.show_collection_info()
        
        # 清除记忆
        elif text in ['/清除', '/c', '/clear']:
            self.clear_memories()
        
        # 添加记忆
        elif text.startswith('/添加') or text.startswith('/add'):
            content = text.replace('/添加', '').replace('/add', '').strip()
            if content:
                self.add_memory(content, metadata={"type": "手动添加"})
            else:
                print("❌ 请提供要添加的记忆内容")
        
        # 搜索记忆
        elif text.startswith('/搜索') or text.startswith('/search'):
            query = text.replace('/搜索', '').replace('/search', '').strip()
            if query:
                self.search_memories(query)
            else:
                print("❌ 请提供搜索关键词")
        
        # 分析
        elif text.startswith('/分析') or text.startswith('/analyze'):
            content = text.replace('/分析', '').replace('/analyze', '').strip()
            if content:
                print("🤖 DeepSeek 分析中...")
                self.add_memory(content, metadata={"type": "分析"})
                self.search_memories(content, limit=3)
            else:
                print("❌ 请提供要分析的文本")
        
        # 对话
        elif text.startswith('/对话') or text.startswith('/chat'):
            message = text.replace('/对话', '').replace('/chat', '').strip()
            if message:
                print("💬 基于 Qdrant 记忆进行对话...")
                self.search_memories(message, limit=3)
                self.add_memory(f"用户问题: {message}", metadata={"type": "对话"})
            else:
                print("❌ 请提供对话内容")
        
        # 普通记忆添加
        elif text and not text.startswith('/'):
            print("🔍 在 Qdrant 中搜索相关记忆...")
            self.search_memories(text, limit=3)
            self.add_memory(text)
        
        return True
    
    def run(self):
        """运行交互循环"""
        print("🚀 启动 DeepSeek + Qdrant 中文记忆系统（输入 /帮助 查看命令）")
        
        while True:
            try:
                user_input = input("\n💭 你: ").strip()
                if not self.process_command(user_input):
                    print("\n👋 再见！")
                    break
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


def check_qdrant_connection():
    """检查 Qdrant 连接"""
    try:
        import requests
        response = requests.get("http://localhost:6333/collections", timeout=3)
        if response.status_code == 200:
            print("✅ Qdrant 服务运行正常")
            collections = response.json().get('result', {}).get('collections', [])
            if collections:
                print(f"   现有集合: {[c['name'] for c in collections]}")
            else:
                print("   暂无集合")
            return True
        else:
            print(f"❌ Qdrant 响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Qdrant (localhost:6333)")
        print("🔧 请先启动 Qdrant 服务:")
        print("   docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant")
        return False
    except Exception as e:
        print(f"❌ 检查 Qdrant 连接失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek + Qdrant 中文记忆系统')
    parser.add_argument('--config', '-c',
                       choices=['huggingface', 'openai', 'ollama'],
                       default='huggingface',
                       help='嵌入模型配置 (默认: huggingface)')
    parser.add_argument('--user', '-u', default='默认用户', help='用户ID')
    parser.add_argument('--check', action='store_true', help='检查 Qdrant 连接')
    
    args = parser.parse_args()
    
    if args.check:
        check_qdrant_connection()
        return
    
    # 检查 DeepSeek API Key
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    
    # 检查 Qdrant 连接
    print("🔍 检查 Qdrant 连接...")
    if not check_qdrant_connection():
        sys.exit(1)
    
    # 启动记忆系统
    try:
        system = DeepSeekQdrantMemory(
            config_type=args.config,
            user_id=args.user
        )
        system.run()
    except KeyboardInterrupt:
        print("\n👋 再见！")


if __name__ == "__main__":
    main()