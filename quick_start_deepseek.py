#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Mem0 快速开始示例
最简单的中文记忆系统
"""

import os
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# 简化配置（使用 HuggingFace 中文嵌入）
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "collection_name": "quick_start",
            "path": "./quick_start_index",
            "embedding_model_dims": 1024,
            "distance_strategy": "cosine",
        },
    },
    "llm": {
        "provider": "deepseek", 
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",
        },
    },
}

def main():
    print("🚀 DeepSeek + Mem0 中文记忆系统快速开始")
    print("=" * 50)
    
    try:
        # 初始化记忆系统
        print("📝 正在初始化记忆系统...")
        m = Memory.from_config(config)
        print("✅ 初始化成功！\n")
        
        # 添加一些中文记忆
        print("💾 添加中文记忆...")
        memories_to_add = [
            "我最喜欢的编程语言是Python，特别适合做数据分析和AI开发",
            "我住在北京，是一名人工智能工程师，主要研究自然语言处理",
            "我的兴趣爱好包括阅读技术书籍、跑步和摄影",
            "我正在学习大语言模型的应用开发，对RAG技术很感兴趣",
            "我喜欢在周末去咖啡店工作，那里的环境很适合思考"
        ]
        
        user_id = "demo_user"
        
        for i, memory in enumerate(memories_to_add, 1):
            result = m.add(memory, user_id=user_id)
            print(f"  {i}. ✓ {memory}")
        
        print(f"\n✅ 成功添加 {len(memories_to_add)} 条记忆\n")
        
        # 演示搜索功能
        print("🔍 演示搜索功能:")
        search_queries = [
            "编程",
            "北京工作", 
            "周末爱好",
            "人工智能"
        ]
        
        for query in search_queries:
            print(f"\n🔍 搜索关键词: '{query}'")
            results = m.search(query, user_id=user_id, limit=2)
            
            if results["results"]:
                for j, result in enumerate(results["results"], 1):
                    score = result['score']
                    memory = result['memory']
                    print(f"  {j}. {memory}")
                    print(f"     💯 相关度: {score:.3f}")
            else:
                print("  ❌ 未找到相关记忆")
        
        # 显示所有记忆
        print(f"\n📚 所有记忆:")
        all_memories = m.get_all(user_id=user_id)
        for i, mem in enumerate(all_memories["results"], 1):
            print(f"  {i}. {mem['memory']}")
        
        print(f"\n🎉 演示完成！共管理了 {len(all_memories['results'])} 条记忆")
        print("\n💡 提示:")
        print("  • 记忆数据存储在本地 './quick_start_index/' 目录")
        print("  • 只有DeepSeek API调用会产生费用，向量存储完全免费")
        print("  • 中文语义搜索由 BAAI/bge-large-zh-v1.5 模型提供")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        
        # 提供错误排查建议
        if "No module named" in str(e):
            print("\n🔧 解决建议:")
            print("   pip install mem0ai[vector_stores]")
            print("   pip install sentence-transformers")
        elif "DEEPSEEK_API_KEY" in str(e):
            print("\n🔧 解决建议:")
            print("   请确认 DeepSeek API Key 已正确设置")
        elif "huggingface" in str(e).lower():
            print("\n🔧 解决建议:")
            print("   首次使用需要下载嵌入模型，请确保网络连接正常")
            print("   可以设置镜像: export HF_ENDPOINT=https://hf-mirror.com")

if __name__ == "__main__":
    main()