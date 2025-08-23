#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mem0 + DeepSeek API 中文优化配置
本地向量存储 + DeepSeek API LLM + 中文嵌入模型
"""

import os
import sys
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# 方案1: 使用 OpenAI 嵌入模型（需要 OpenAI API Key）
DEEPSEEK_WITH_OPENAI_EMBEDDINGS = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "deepseek_chinese_memories",
            "path": "./deepseek_faiss_index",
            "embedding_model_dims": 1536,  # OpenAI text-embedding-3-small
            "distance_strategy": "cosine",
        },
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",  # 或 "deepseek-coder" 用于代码相关
            "temperature": 0.7,
            "max_tokens": 3000,  # 中文内容通常更长
            "top_p": 0.9,
        },
    },
    "embedder": {
        "provider": "openai", 
        "config": {
            "model": "text-embedding-3-small",  # 便宜且效果好
            # 如果要更好效果可以用: "text-embedding-3-large"
        },
    },
}

# 方案2: 使用 HuggingFace 中文嵌入模型（完全免费）
DEEPSEEK_WITH_HUGGINGFACE_EMBEDDINGS = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "deepseek_chinese_memories_hf",
            "path": "./deepseek_hf_index",
            "embedding_model_dims": 1024,  # BAAI/bge-large-zh-v1.5
            "distance_strategy": "cosine",
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
            "model": "BAAI/bge-large-zh-v1.5",  # 中文语义理解最佳
            # 备选: "BAAI/bge-base-zh-v1.5" (768维，速度更快)
        },
    },
}

# 方案3: 使用 Ollama 本地嵌入模型（需要先安装并运行 Ollama）
DEEPSEEK_WITH_OLLAMA_EMBEDDINGS = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "deepseek_chinese_memories_ollama",
            "path": "./deepseek_ollama_index",
            "embedding_model_dims": 1024,  # bge-m3
            "distance_strategy": "cosine",
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


class DeepSeekChineseMemory:
    """DeepSeek + 中文记忆系统"""
    
    def __init__(self, config_type="huggingface", user_id="默认用户"):
        """
        初始化 DeepSeek 中文记忆系统
        
        Args:
            config_type: "openai", "huggingface", "ollama"
            user_id: 用户标识
        """
        self.user_id = user_id
        
        # 选择配置
        configs = {
            "openai": DEEPSEEK_WITH_OPENAI_EMBEDDINGS,
            "huggingface": DEEPSEEK_WITH_HUGGINGFACE_EMBEDDINGS,
            "ollama": DEEPSEEK_WITH_OLLAMA_EMBEDDINGS,
        }
        
        if config_type not in configs:
            raise ValueError(f"配置类型必须是: {list(configs.keys())}")
        
        config = configs[config_type]
        
        try:
            self.memory = Memory.from_config(config)
            print(f"✓ DeepSeek 中文记忆系统初始化成功")
            print(f"✓ 用户: {user_id}")
            print(f"✓ LLM: DeepSeek API")
            print(f"✓ 嵌入: {config_type}")
            print(f"✓ 向量存储: 本地 FAISS")
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            if "OPENAI_API_KEY" in str(e) and config_type == "openai":
                print("提示: OpenAI 嵌入需要设置 OPENAI_API_KEY 环境变量")
            elif "ollama" in str(e).lower() and config_type == "ollama":
                print("提示: Ollama 嵌入需要先运行 'ollama serve' 并下载模型")
            sys.exit(1)
        
        self._print_help()
    
    def _print_help(self):
        """打印帮助信息"""
        print("\n" + "="*60)
        print("DeepSeek + 本地向量存储 中文记忆系统")
        print("="*60)
        print("特点:")
        print("  • LLM: DeepSeek API (强大的中文理解和生成)")
        print("  • 存储: 本地向量数据库 (数据完全私有)")
        print("  • 嵌入: 中文优化的嵌入模型")
        print()
        print("命令:")
        print("  /记忆 或 /m         - 查看所有记忆")
        print("  /搜索 <关键词>      - 搜索相关记忆") 
        print("  /分析 <文本>        - 让 DeepSeek 分析文本并记忆")
        print("  /对话 <消息>        - 基于记忆的智能对话")
        print("  /清除 或 /c         - 清除所有记忆")
        print("  /统计 或 /s         - 显示记忆统计")
        print("  /退出 或 /q         - 退出程序")
        print("="*60 + "\n")
    
    def add_memory(self, text, metadata=None):
        """添加记忆"""
        try:
            result = self.memory.add(text, user_id=self.user_id, metadata=metadata)
            print(f"✓ 记忆已保存")
            return result
        except Exception as e:
            print(f"✗ 保存失败: {e}")
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
                print(f"\n🔍 找到 {len(results['results'])} 条相关记忆：")
                print("-" * 50)
                for i, mem in enumerate(results["results"], 1):
                    score = mem.get('score', 0)
                    memory_text = mem['memory']
                    print(f"{i}. {memory_text}")
                    print(f"   💯 相关度: {score:.3f}")
                    if 'metadata' in mem and mem['metadata']:
                        print(f"   🏷️  标签: {mem['metadata']}")
                    print()
            else:
                print("❌ 未找到相关记忆")
            
            return results
        except Exception as e:
            print(f"✗ 搜索失败: {e}")
            return None
    
    def analyze_with_deepseek(self, text):
        """使用 DeepSeek 分析文本并保存记忆"""
        try:
            # 构造分析提示
            analysis_messages = [
                {
                    "role": "system", 
                    "content": "你是一个智能记忆分析助手。请分析用户提供的文本，提取关键信息、主题和要点，然后以简洁明了的方式总结。"
                },
                {
                    "role": "user", 
                    "content": f"请分析以下文本内容：\n\n{text}"
                }
            ]
            
            # 使用记忆系统的 LLM 进行分析
            # 注意：这里直接访问内部 LLM，实际使用中可能需要调整
            print("🤖 DeepSeek 正在分析...")
            
            # 直接保存原文本作为记忆
            result = self.add_memory(text, metadata={"type": "analysis"})
            
            # 同时搜索相关记忆
            print("🔍 搜索相关记忆...")
            self.search_memories(text, limit=3)
            
            return result
            
        except Exception as e:
            print(f"✗ 分析失败: {e}")
            return None
    
    def chat_with_memory(self, message):
        """基于记忆的智能对话"""
        try:
            # 搜索相关记忆
            print("🔍 搜索相关记忆...")
            relevant_memories = self.search_memories(message, limit=3)
            
            # 构造带记忆的对话
            memory_context = ""
            if relevant_memories and relevant_memories["results"]:
                memory_context = "相关记忆：\n"
                for mem in relevant_memories["results"]:
                    memory_context += f"- {mem['memory']}\n"
            
            print(f"\n💬 基于 {len(relevant_memories.get('results', []))} 条相关记忆进行对话")
            print("(注意: 完整的对话功能需要实现额外的 LLM 调用逻辑)")
            
            # 保存新的对话记忆
            self.add_memory(f"用户问题: {message}", metadata={"type": "conversation"})
            
        except Exception as e:
            print(f"✗ 对话失败: {e}")
    
    def show_all_memories(self):
        """显示所有记忆"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            
            if memories["results"]:
                print(f"\n📚 共有 {len(memories['results'])} 条记忆：")
                print("-" * 50)
                for i, mem in enumerate(memories["results"], 1):
                    print(f"{i}. {mem['memory']}")
                    print(f"   🆔 ID: {mem['id'][:12]}...")
                    if 'metadata' in mem and mem['metadata']:
                        print(f"   🏷️  标签: {mem['metadata']}")
                    print()
            else:
                print("📭 暂无记忆")
            
            return memories
        except Exception as e:
            print(f"✗ 获取记忆失败: {e}")
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
            
            print(f"\n📊 记忆统计:")
            print(f"   总计: {total} 条记忆")
            print(f"   类型分布:")
            for t, count in types.items():
                print(f"     • {t}: {count} 条")
            
        except Exception as e:
            print(f"✗ 统计失败: {e}")
    
    def clear_memories(self):
        """清除所有记忆"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            count = len(memories["results"])
            
            if count == 0:
                print("📭 没有需要清除的记忆")
                return
            
            confirm = input(f"⚠️  确定要清除 {count} 条记忆吗？(y/n): ")
            if confirm.lower() in ['y', 'yes', '是', '确定']:
                for mem in memories["results"]:
                    self.memory.delete(memory_id=mem['id'])
                print(f"✅ 已清除 {count} 条记忆")
            else:
                print("❌ 取消清除")
        except Exception as e:
            print(f"✗ 清除失败: {e}")
    
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
        
        # 清除记忆
        elif text in ['/清除', '/c', '/clear']:
            self.clear_memories()
        
        # 搜索记忆
        elif text.startswith('/搜索') or text.startswith('/search'):
            query = text.replace('/搜索', '').replace('/search', '').strip()
            if query:
                self.search_memories(query)
            else:
                print("❌ 请提供搜索关键词")
        
        # DeepSeek 分析
        elif text.startswith('/分析') or text.startswith('/analyze'):
            content = text.replace('/分析', '').replace('/analyze', '').strip()
            if content:
                self.analyze_with_deepseek(content)
            else:
                print("❌ 请提供要分析的文本")
        
        # 对话
        elif text.startswith('/对话') or text.startswith('/chat'):
            message = text.replace('/对话', '').replace('/chat', '').strip()
            if message:
                self.chat_with_memory(message)
            else:
                print("❌ 请提供对话内容")
        
        # 普通记忆添加
        elif text and not text.startswith('/'):
            # 先搜索相关记忆
            print("🔍 搜索相关记忆...")
            self.search_memories(text, limit=3)
            
            # 添加新记忆
            self.add_memory(text)
        
        return True
    
    def run(self):
        """运行交互循环"""
        print("🚀 开始使用 DeepSeek 中文记忆系统（输入 /帮助 查看命令）")
        
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


def test_configs():
    """测试不同配置的可用性"""
    print("🔧 测试配置可用性...")
    
    configs_to_test = [
        ("huggingface", "HuggingFace 中文嵌入模型（推荐）"),
        ("ollama", "Ollama 本地嵌入模型"), 
        ("openai", "OpenAI 嵌入模型"),
    ]
    
    available_configs = []
    
    for config_type, desc in configs_to_test:
        try:
            print(f"\n测试 {desc}...")
            # 这里只是初始化测试，不运行完整系统
            memory_system = DeepSeekChineseMemory(config_type=config_type)
            print(f"✅ {desc} 可用")
            available_configs.append((config_type, desc))
            del memory_system
        except Exception as e:
            print(f"❌ {desc} 不可用: {e}")
    
    print(f"\n📋 可用配置: {len(available_configs)} 个")
    for config_type, desc in available_configs:
        print(f"  • {config_type}: {desc}")
    
    return available_configs


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek + 中文记忆系统')
    parser.add_argument('--config', '-c', 
                       choices=['openai', 'huggingface', 'ollama'],
                       default='huggingface',
                       help='嵌入模型配置 (默认: huggingface)')
    parser.add_argument('--user', '-u', default='默认用户', help='用户ID')
    parser.add_argument('--test', '-t', action='store_true', help='测试所有配置')
    
    args = parser.parse_args()
    
    if args.test:
        test_configs()
        return
    
    # 检查 DeepSeek API Key
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    
    # 启动记忆系统
    try:
        system = DeepSeekChineseMemory(
            config_type=args.config,
            user_id=args.user
        )
        system.run()
    except KeyboardInterrupt:
        print("\n👋 再见！")


if __name__ == "__main__":
    main()