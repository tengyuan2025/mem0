#!/usr/bin/env python3
"""
手动下载完整的中文嵌入模型
"""

import os
from pathlib import Path

def download_chinese_model():
    """下载中文模型"""
    model_name = "shibing624/text2vec-base-chinese"
    
    print(f"🚀 开始下载中文模型: {model_name}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 设置缓存目录
        cache_dir = os.getenv("HF_HOME", "./data/huggingface")
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"📁 缓存目录: {cache_dir}")
        
        # 强制重新下载模型
        print(f"📥 正在下载模型...")
        model = SentenceTransformer(
            model_name,
            cache_folder=cache_dir,
            device='cpu'
        )
        
        print(f"✅ 模型下载成功!")
        
        # 测试模型
        print(f"🧪 测试模型...")
        test_text = "这是一个测试文本"
        embedding = model.encode(test_text)
        print(f"✅ 测试成功! 向量维度: {len(embedding)}")
        
        # 显示模型信息
        print(f"\n📋 模型信息:")
        print(f"  模型名称: {model_name}")
        print(f"  向量维度: {len(embedding)}")
        print(f"  缓存位置: {cache_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    download_chinese_model()