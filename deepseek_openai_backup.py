#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Qdrant + OpenAI 嵌入备用配置
当 HuggingFace 模型无法下载时的备用方案
"""

import os
import sys
from mem0 import Memory

# 设置 API Keys
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"
# 需要用户设置 OpenAI API Key
# os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

# 备用配置：使用 OpenAI 嵌入模型
BACKUP_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_backup_memories",
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
            "model": "text-embedding-3-small",  # 更便宜的嵌入模型
        },
    },
}

def test_backup_config():
    """测试备用配置"""
    try:
        print("🧪 测试备用配置...")
        
        # 检查 OpenAI API Key
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 请设置 OPENAI_API_KEY 环境变量")
            print("   export OPENAI_API_KEY='your-openai-api-key'")
            return False
        
        # 初始化记忆系统
        m = Memory.from_config(BACKUP_CONFIG)
        
        # 测试添加和搜索
        test_text = "这是一个测试记忆，用于验证备用配置是否正常工作"
        result = m.add(test_text, user_id="test_user")
        print(f"✅ 添加记忆成功: {result}")
        
        # 测试搜索
        results = m.search("测试", user_id="test_user", limit=1)
        print(f"✅ 搜索成功，找到 {len(results['results'])} 条记忆")
        
        return True
        
    except Exception as e:
        print(f"❌ 备用配置测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔄 DeepSeek + OpenAI 嵌入备用配置测试")
    print("=" * 50)
    
    success = test_backup_config()
    
    if success:
        print("\n✅ 备用配置工作正常！")
        print("💡 可以修改 deepseek_web_service.py 使用此配置")
    else:
        print("\n❌ 备用配置失败")
        print("🔧 请检查 OpenAI API Key 设置")