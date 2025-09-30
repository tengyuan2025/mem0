#!/usr/bin/env python3
"""
测试中文嵌入模型加载和使用
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_chinese_model():
    model_name = os.getenv("MEM0_EMBEDDER_MODEL", "shibing624/text2vec-base-chinese")
    
    print(f"📋 测试中文模型: {model_name}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"🚀 正在加载模型...")
        
        # 加载模型
        model = SentenceTransformer(model_name, device='cpu')
        
        print(f"✅ 模型加载成功!")
        
        # 测试中文文本编码
        test_texts = [
            "今天天气很好",
            "我喜欢吃苹果",
            "人工智能技术发展迅速",
            "这是一个测试文本"
        ]
        
        print(f"\n🧪 测试文本编码...")
        for i, text in enumerate(test_texts):
            embedding = model.encode(text)
            print(f"  {i+1}. '{text}' -> 向量维度: {len(embedding)}")
        
        # 计算相似度测试
        print(f"\n🔍 测试语义相似度...")
        similarity_pairs = [
            ("今天天气很好", "今日气候不错"),
            ("我喜欢吃苹果", "我爱吃水果"),
            ("人工智能", "机器学习")
        ]
        
        for text1, text2 in similarity_pairs:
            emb1 = model.encode(text1)
            emb2 = model.encode(text2)
            
            # 计算余弦相似度
            import numpy as np
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f"  '{text1}' vs '{text2}': {similarity:.3f}")
        
        print(f"\n✅ 中文模型测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_chinese_model()