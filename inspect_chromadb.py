#!/usr/bin/env python3
"""
ChromaDB 数据结构检查脚本
用于查看向量数据库中存储的记忆数据结构
"""

import os
import sys
import json
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

def inspect_chromadb():
    """检查 ChromaDB 数据结构"""
    try:
        import chromadb
        
        # 连接到 ChromaDB
        chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
        if os.path.exists(chroma_persist_dir):
            client = chromadb.PersistentClient(path=chroma_persist_dir)
        else:
            print("❌ ChromaDB 持久化目录不存在:", chroma_persist_dir)
            return
        
        # 获取集合
        collection_name = os.getenv("CHROMA_COLLECTION", "mem0_memories")
        try:
            collection = client.get_collection(collection_name)
            print(f"✅ 成功连接到集合: {collection_name}")
        except Exception as e:
            print(f"❌ 集合不存在或无法访问: {collection_name}")
            print(f"   错误: {e}")
            print("\n📋 可用集合:")
            collections = client.list_collections()
            for col in collections:
                print(f"   - {col.name}")
            return
        
        # 获取集合信息
        print(f"\n📊 集合信息:")
        print(f"   集合名称: {collection.name}")
        
        # 获取数据总数
        count = collection.count()
        print(f"   数据总数: {count}")
        
        if count == 0:
            print("   ℹ️  集合为空，没有数据")
            return
        
        # 获取前几条数据来查看结构
        limit = min(3, count)  # 最多查看3条
        results = collection.get(limit=limit, include=['metadatas', 'documents'])
        
        print(f"\n📋 ChromaDB 数据结构 (显示前{limit}条):")
        print("=" * 60)
        
        for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            print(f"\n第 {i+1} 条记录:")
            print(f"🔑 ID: {doc_id}")
            
            if metadata:
                print("📄 元数据字段:")
                for key, value in metadata.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"   {key}: {value[:100]}...")
                    else:
                        print(f"   {key}: {value}")
            else:
                print("   无元数据")
        
        # 显示完整的数据结构说明
        print(f"\n📖 ChromaDB 存储结构说明:")
        print("=" * 60)
        print("ChromaDB 以文档为单位存储数据，每个文档包含:")
        print("1. 🔑 ID (string)          - 记忆的唯一标识符")
        print("2. 🔢 Embedding (vector)   - 文本的向量嵌入表示")  
        print("3. 📄 Metadata (dict)      - 包含以下字段:")
        
        if results['metadatas'] and len(results['metadatas']) > 0:
            # 从第一条记录中提取所有可能的字段
            sample_metadata = results['metadatas'][0]
            for key in sorted(sample_metadata.keys()):
                print(f"   - {key}")
        
        # 显示时间信息
        if results['metadatas']:
            created_times = []
            for meta in results['metadatas']:
                if 'created_at' in meta:
                    created_times.append(meta['created_at'])
            
            if created_times:
                print(f"\n⏰ 时间范围:")
                print(f"   最早记录: {min(created_times)}")
                print(f"   最新记录: {max(created_times)}")
        
    except ImportError:
        print("❌ ChromaDB 未安装，请先安装: pip install chromadb")
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

def show_metadata_fields():
    """显示代码中定义的元数据字段"""
    print(f"\n💡 根据代码分析，ChromaDB 中的 metadata 字段包括:")
    print("=" * 60)
    print("📦 基础字段 (自动添加):")
    print("   - user_id: 用户ID")
    print("   - created_at: 创建时间 (ISO格式)")
    print("   - content: 记忆内容")
    print()
    print("📦 可选字段 (来自用户输入的 metadata):")
    print("   - 任何用户在添加记忆时传入的自定义字段")
    print()
    print("🔍 向量嵌入:")
    print("   - embeddings: 数值向量数组 (用于相似性搜索)")

if __name__ == "__main__":
    print("🔍 ChromaDB 数据结构检查工具")
    print("=" * 60)
    
    # 先显示理论结构
    show_metadata_fields()
    
    # 再检查实际数据
    print(f"\n🔍 检查实际存储的数据:")
    print("=" * 60)
    inspect_chromadb()