#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Qdrant 快速开始示例
高性能向量存储 + 中文优化嵌入
"""

import os
import sys
import requests
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# Qdrant + HuggingFace 中文嵌入配置
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "quickstart_chinese",
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
            "max_tokens": 2000,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",  # 专业中文嵌入模型
        },
    },
}


def check_qdrant():
    """检查 Qdrant 服务状态"""
    try:
        response = requests.get("http://localhost:6333/health", timeout=3)
        if response.status_code == 200:
            print("✅ Qdrant 服务运行正常")
            return True
        else:
            print(f"❌ Qdrant 响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Qdrant 服务")
        print("\n🔧 请先启动 Qdrant:")
        print("   docker run -d --name qdrant \\")
        print("     -p 6333:6333 -p 6334:6334 \\")
        print("     -v $(pwd)/qdrant_storage:/qdrant/storage:z \\")
        print("     qdrant/qdrant")
        return False
    except Exception as e:
        print(f"❌ 检查 Qdrant 失败: {e}")
        return False


def main():
    print("🚀 DeepSeek + Qdrant 中文记忆系统快速开始")
    print("=" * 60)
    
    # 1. 检查 Qdrant 连接
    print("🔍 检查 Qdrant 服务...")
    if not check_qdrant():
        sys.exit(1)
    
    try:
        # 2. 初始化记忆系统
        print("\n📝 正在初始化 Qdrant 记忆系统...")
        print("   • 向量存储: Qdrant (localhost:6333)")  
        print("   • LLM: DeepSeek API")
        print("   • 嵌入: BAAI/bge-large-zh-v1.5")
        
        m = Memory.from_config(config)
        print("✅ 记忆系统初始化成功！")
        
        # 3. 添加中文记忆样本
        print("\n💾 添加中文记忆到 Qdrant...")
        chinese_memories = [
            "我是一名人工智能工程师，专注于大语言模型和RAG技术的研发",
            "我最擅长使用Python进行AI开发，特别喜欢FastAPI、LangChain和Streamlit",
            "我住在深圳，经常参加AI技术交流会和开源项目贡献",
            "我的研究兴趣包括知识图谱、向量数据库和多模态AI应用",
            "我喜欢在周末阅读最新的AI论文，特别关注Transformer架构的发展",
            "我正在开发一个基于RAG的智能问答系统，用于企业知识管理",
            "我对DeepSeek、Qwen等中文大模型的性能表现很感兴趣",
            "我经常使用Qdrant作为向量数据库，因为它的性能和可扩展性都很优秀"
        ]
        
        user_id = "ai_engineer_demo"
        
        for i, memory in enumerate(chinese_memories, 1):
            result = m.add(memory, user_id=user_id)
            print(f"  {i}. ✓ {memory}")
        
        print(f"\n✅ 成功在 Qdrant 中存储了 {len(chinese_memories)} 条中文记忆")
        
        # 4. 演示语义搜索
        print(f"\n🔍 演示 Qdrant 中文语义搜索:")
        search_tests = [
            ("Python开发", "搜索编程相关内容"),
            ("深圳工作", "搜索地理位置信息"),
            ("AI研究", "搜索研究兴趣"),
            ("向量数据库", "搜索技术栈信息"),
            ("论文阅读", "搜索学习习惯"),
        ]
        
        for query, description in search_tests:
            print(f"\n📋 {description}: '{query}'")
            results = m.search(query, user_id=user_id, limit=2)
            
            if results["results"]:
                for j, result in enumerate(results["results"], 1):
                    score = result['score']
                    memory = result['memory']
                    print(f"   {j}. {memory}")
                    print(f"      💯 相关度: {score:.4f}")
            else:
                print("   ❌ 未找到相关记忆")
        
        # 5. 显示 Qdrant 集合信息
        print(f"\n📊 Qdrant 集合信息:")
        try:
            response = requests.get("http://localhost:6333/collections")
            if response.status_code == 200:
                collections = response.json().get('result', {}).get('collections', [])
                for collection in collections:
                    if collection['name'] == config['vector_store']['config']['collection_name']:
                        print(f"   集合名称: {collection['name']}")
                        
                        # 获取详细信息
                        detail_response = requests.get(f"http://localhost:6333/collections/{collection['name']}")
                        if detail_response.status_code == 200:
                            details = detail_response.json()['result']
                            print(f"   向量数量: {details.get('points_count', 'N/A')}")
                            print(f"   向量维度: {details.get('config', {}).get('params', {}).get('vectors', {}).get('size', 'N/A')}")
                            print(f"   状态: {details.get('status', 'N/A')}")
        except:
            pass
        
        # 6. 性能测试
        print(f"\n⚡ 简单性能测试:")
        import time
        
        # 测试搜索延迟
        start_time = time.time()
        test_queries = ["AI", "Python", "深圳", "研究", "开发"]
        for query in test_queries:
            m.search(query, user_id=user_id, limit=3)
        search_time = time.time() - start_time
        
        print(f"   执行 {len(test_queries)} 次搜索平均延迟: {search_time/len(test_queries)*1000:.1f}ms")
        
        # 7. 总结
        print(f"\n🎉 快速开始演示完成！")
        print(f"📈 统计信息:")
        all_memories = m.get_all(user_id=user_id)
        print(f"   • 总记忆数量: {len(all_memories['results'])}")
        print(f"   • 向量存储: Qdrant (高性能)")
        print(f"   • 数据持久化: 启用")
        print(f"   • 中文语义理解: 优秀")
        
        print(f"\n💡 下一步:")
        print(f"   • 运行交互版本: python deepseek_qdrant_config.py")
        print(f"   • 查看 Qdrant Web UI: http://localhost:6333/dashboard")
        print(f"   • 数据存储位置: ./qdrant_storage/")
        
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        
        # 错误排查建议
        if "No module named" in str(e):
            print("\n🔧 依赖安装:")
            print("   pip install mem0ai[vector_stores]")
            print("   pip install sentence-transformers")
            print("   pip install qdrant-client")
        elif "connection" in str(e).lower():
            print("\n🔧 Qdrant 连接问题:")
            print("   1. 确认 Qdrant 服务正在运行")
            print("   2. 检查端口 6333 是否可访问")
            print("   3. 查看 Docker 容器状态: docker ps | grep qdrant")
        elif "huggingface" in str(e).lower() or "transformers" in str(e).lower():
            print("\n🔧 嵌入模型问题:")
            print("   1. 首次使用需要下载模型，请等待")
            print("   2. 设置国内镜像: export HF_ENDPOINT=https://hf-mirror.com")
            print("   3. 检查网络连接")
        
        sys.exit(1)


if __name__ == "__main__":
    main()