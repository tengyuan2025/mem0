#!/usr/bin/env python3
"""
测试Mem0环境是否正确配置
"""
import sys
import os

def test_basic_imports():
    """测试基础导入"""
    print("🧪 测试基础导入...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI导入失败: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn导入失败: {e}")
        return False
    
    return True

def test_qdrant_connection():
    """测试Qdrant连接"""
    print("🔗 测试Qdrant连接...")
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        
        # 测试连接
        collections = client.get_collections()
        print(f"✅ Qdrant连接成功: {len(collections.collections)} 个集合")
        return True
        
    except ImportError as e:
        print(f"❌ Qdrant客户端导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ Qdrant连接失败: {e}")
        return False

def test_ai_models():
    """测试AI模型导入（不下载）"""
    print("🤖 测试AI模型导入...")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ sentence-transformers 导入成功")
        print("💡 中文模型BAAI/bge-large-zh-v1.5将在首次使用时下载")
        return True
        
    except ImportError as e:
        print(f"❌ sentence-transformers导入失败: {e}")
        return False

def test_mem0_core():
    """测试Mem0核心模块"""
    print("🧠 测试Mem0核心模块...")
    
    sys.path.insert(0, os.getcwd())
    
    try:
        from mem0.configs.llms.doubao import DoubaoConfig
        print("✅ DoubaoConfig导入成功")
        
        from mem0.embeddings.configs import EmbedderConfig
        print("✅ EmbedderConfig导入成功") 
        
        return True
        
    except ImportError as e:
        print(f"❌ Mem0模块导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Mem0环境测试开始")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_qdrant_connection, 
        test_ai_models,
        test_mem0_core
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 环境配置完成！可以启动Mem0服务")
    else:
        print("⚠️ 部分测试失败，请检查配置")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)