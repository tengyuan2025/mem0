#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mem0 中文本地部署配置
优化中文语义理解和存储
"""

from mem0 import Memory
import sys
import os

# 中文优化配置
CHINESE_OPTIMIZED_CONFIG = {
    "vector_store": {
        "provider": "faiss",  # 或使用 "chroma", "qdrant"
        "config": {
            "collection_name": "chinese_memories",
            "path": "./chinese_faiss_index",
            # 使用更大的维度以更好地捕捉中文语义
            "embedding_model_dims": 1024,  # 对应 bge-large-zh 模型
            "distance_strategy": "cosine",  # 余弦相似度更适合中文
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            # 推荐的中文模型（按优先级排序）
            "model": "qwen2.5:14b",  # 最佳中文支持
            # 备选模型：
            # "model": "qwen2.5:32b",  # 更强但更慢
            # "model": "qwen2:72b",     # 最强但需要大内存
            # "model": "yi:34b",        # Yi 系列也很好
            # "model": "deepseek-v2:16b", # DeepSeek 中文不错
            "temperature": 0.7,
            "max_tokens": 3000,
            "ollama_base_url": "http://localhost:11434",
            # 添加中文特定的生成参数
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
    },
    "embedder": {
        "provider": "ollama", 
        "config": {
            # 中文嵌入模型选择
            "model": "bge-m3:latest",  # BAAI 的中文嵌入模型，效果最好
            # 备选：
            # "model": "nomic-embed-text:latest",  # 多语言支持
            # "model": "snowflake-arctic-embed:latest",  # 多语言，维度更高
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

# 使用 HuggingFace 中文嵌入模型的替代配置
HUGGINGFACE_CHINESE_CONFIG = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "chinese_memories_hf",
            "path": "./chinese_hf_index",
            "embedding_model_dims": 1024,  # BAAI/bge-large-zh-v1.5 的维度
            "distance_strategy": "cosine",
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5:14b",
            "temperature": 0.7,
            "max_tokens": 3000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            # 使用 BAAI 的中文嵌入模型
            "model": "BAAI/bge-large-zh-v1.5",
            # 备选中文嵌入模型：
            # "model": "BAAI/bge-base-zh-v1.5",  # 768维，速度更快
            # "model": "shibing624/text2vec-base-chinese",  # 另一个好选择
        },
    },
}


class ChineseMemoryChat:
    """中文记忆对话系统"""
    
    def __init__(self, user_id="默认用户", use_huggingface=False):
        """
        初始化中文记忆对话系统
        
        Args:
            user_id: 用户标识
            use_huggingface: 是否使用 HuggingFace 嵌入模型
        """
        self.user_id = user_id
        
        # 选择配置
        if use_huggingface:
            print("使用 HuggingFace 中文嵌入模型...")
            config = HUGGINGFACE_CHINESE_CONFIG
        else:
            print("使用 Ollama 中文模型...")
            config = CHINESE_OPTIMIZED_CONFIG
        
        # 初始化记忆系统
        try:
            self.memory = Memory.from_config(config)
            print(f"✓ 中文记忆系统初始化成功")
            print(f"✓ 用户: {user_id}")
            print(f"✓ LLM模型: {config['llm']['config']['model']}")
            print(f"✓ 嵌入模型: {config['embedder']['config']['model']}")
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            sys.exit(1)
        
        self._print_help()
    
    def _print_help(self):
        """打印帮助信息"""
        print("\n" + "="*50)
        print("中文记忆对话系统")
        print("="*50)
        print("命令：")
        print("  /记忆 或 /m    - 查看所有记忆")
        print("  /搜索 <关键词> - 搜索相关记忆")
        print("  /清除 或 /c    - 清除所有记忆")
        print("  /帮助 或 /h    - 显示帮助")
        print("  /退出 或 /q    - 退出程序")
        print("="*50 + "\n")
    
    def add_memory(self, text):
        """添加记忆"""
        try:
            result = self.memory.add(text, user_id=self.user_id)
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
                print(f"\n找到 {len(results['results'])} 条相关记忆：")
                print("-" * 40)
                for i, mem in enumerate(results["results"], 1):
                    score = mem.get('score', 0)
                    memory_text = mem['memory']
                    print(f"{i}. {memory_text}")
                    print(f"   相关度: {score:.3f}")
                    print()
            else:
                print("未找到相关记忆")
            
            return results
        except Exception as e:
            print(f"✗ 搜索失败: {e}")
            return None
    
    def show_all_memories(self):
        """显示所有记忆"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            
            if memories["results"]:
                print(f"\n共有 {len(memories['results'])} 条记忆：")
                print("-" * 40)
                for i, mem in enumerate(memories["results"], 1):
                    print(f"{i}. {mem['memory']}")
                    print(f"   ID: {mem['id'][:8]}...")
                    if 'created_at' in mem:
                        print(f"   时间: {mem['created_at']}")
                    print()
            else:
                print("暂无记忆")
            
            return memories
        except Exception as e:
            print(f"✗ 获取记忆失败: {e}")
            return None
    
    def clear_memories(self):
        """清除所有记忆"""
        try:
            memories = self.memory.get_all(user_id=self.user_id)
            count = len(memories["results"])
            
            if count == 0:
                print("没有需要清除的记忆")
                return
            
            confirm = input(f"确定要清除 {count} 条记忆吗？(y/n): ")
            if confirm.lower() in ['y', 'yes', '是', '确定']:
                for mem in memories["results"]:
                    self.memory.delete(memory_id=mem['id'])
                print(f"✓ 已清除 {count} 条记忆")
            else:
                print("取消清除")
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
        
        # 清除记忆
        elif text in ['/清除', '/c', '/clear']:
            self.clear_memories()
        
        # 搜索记忆
        elif text.startswith('/搜索') or text.startswith('/search'):
            query = text.replace('/搜索', '').replace('/search', '').strip()
            if query:
                self.search_memories(query)
            else:
                print("请提供搜索关键词")
        
        # 普通对话，添加到记忆
        elif text and not text.startswith('/'):
            # 先搜索相关记忆
            print("\n相关记忆：")
            self.search_memories(text, limit=3)
            
            # 添加新记忆
            self.add_memory(text)
        
        return True
    
    def run(self):
        """运行对话循环"""
        print("开始对话（输入 /帮助 查看命令）")
        
        while True:
            try:
                user_input = input("\n你: ").strip()
                if not self.process_command(user_input):
                    print("\n再见！")
                    break
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"错误: {e}")


def download_models():
    """下载推荐的中文模型"""
    print("正在检查和下载中文模型...")
    
    models_to_download = [
        "qwen2.5:14b",      # 主要 LLM
        "bge-m3:latest",    # 中文嵌入模型
    ]
    
    for model in models_to_download:
        print(f"下载模型: {model}")
        os.system(f"ollama pull {model}")
    
    print("✓ 模型下载完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mem0 中文记忆对话系统')
    parser.add_argument('--user', '-u', default='默认用户', help='用户ID')
    parser.add_argument('--huggingface', '-hf', action='store_true', 
                       help='使用 HuggingFace 嵌入模型')
    parser.add_argument('--download', '-d', action='store_true',
                       help='下载推荐的中文模型')
    
    args = parser.parse_args()
    
    if args.download:
        download_models()
        return
    
    # 检查 Ollama 是否运行
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            raise Exception("Ollama 服务未响应")
    except:
        print("✗ Ollama 服务未运行")
        print("请先启动 Ollama: ollama serve")
        sys.exit(1)
    
    # 启动对话系统
    chat = ChineseMemoryChat(
        user_id=args.user,
        use_huggingface=args.huggingface
    )
    chat.run()


if __name__ == "__main__":
    main()