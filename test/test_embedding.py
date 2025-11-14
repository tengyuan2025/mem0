#!/usr/bin/env python3
"""
测试Embedding模型加载
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_embedding():
    embedding_provider = os.getenv("MEM0_EMBEDDER_PROVIDER", "sentence_transformers")
    model_name = os.getenv("MEM0_EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    
    print(f"📋 配置信息:")
    print(f"  Provider: {embedding_provider}")
    print(f"  Model: {model_name}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 设置缓存目录
        cache_dir = os.getenv("HF_HOME", "./data/huggingface")
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"  Cache: {cache_dir}")
        print(f"\n🚀 尝试加载模型...")
        
        # 尝试加载模型
        model = SentenceTransformer(
            model_name, 
            cache_folder=cache_dir,
            device='cpu'
        )
        
        print(f"✅ 模型加载成功!")
        
        # 测试编码
        test_text = "这是一个测试文本"
        embedding = model.encode(test_text)
        print(f"✅ 编码测试成功! 向量维度: {len(embedding)}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        
        # 尝试回退模型
        print(f"\n🔄 尝试回退模型...")
        fallback_model = "paraphrase-multilingual-MiniLM-L12-v2"
        
        try:
            model = SentenceTransformer(
                fallback_model,
                cache_folder=cache_dir,
                device='cpu'
            )
            print(f"✅ 回退模型加载成功: {fallback_model}")
            
            # 测试编码
            test_text = "这是一个测试文本"
            embedding = model.encode(test_text)
            print(f"✅ 编码测试成功! 向量维度: {len(embedding)}")
            
        except Exception as e2:
            print(f"❌ 回退模型也失败: {e2}")

if __name__ == "__main__":
    test_embedding()