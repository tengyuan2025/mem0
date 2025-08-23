#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Qdrant + Ollama 嵌入模型配置
使用 Ollama 本地运行嵌入模型，完全离线
"""

import os
import sys
from mem0 import Memory

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# Ollama 嵌入模型配置
OLLAMA_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_ollama_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,  # nomic-embed-text 的维度
            # 如果使用其他模型，调整维度：
            # bge-m3: 1024
            # mxbai-embed-large: 1024
            # all-minilm: 384
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
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",  # Ollama 嵌入模型
            # 其他可用的 Ollama 嵌入模型：
            # "model": "bge-m3:latest",  # BAAI 中文嵌入模型（推荐）
            # "model": "mxbai-embed-large:latest",  # 另一个好的选择
            # "model": "all-minilm:latest",  # 轻量级选项
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

# 各种 Ollama 嵌入模型的配置
OLLAMA_MODELS = {
    "nomic-embed-text": {
        "name": "nomic-embed-text:latest",
        "dims": 768,
        "description": "Nomic 嵌入模型，多语言支持",
        "size": "274MB",
        "pull_command": "ollama pull nomic-embed-text"
    },
    "bge-m3": {
        "name": "bge-m3:latest",
        "dims": 1024,
        "description": "BAAI BGE-M3 中文嵌入模型（推荐）",
        "size": "1.2GB",
        "pull_command": "ollama pull bge-m3"
    },
    "mxbai-embed-large": {
        "name": "mxbai-embed-large:latest",
        "dims": 1024,
        "description": "MixedBread AI 嵌入模型",
        "size": "670MB",
        "pull_command": "ollama pull mxbai-embed-large"
    },
    "all-minilm": {
        "name": "all-minilm:latest",
        "dims": 384,
        "description": "轻量级嵌入模型",
        "size": "45MB",
        "pull_command": "ollama pull all-minilm"
    },
    "snowflake-arctic-embed": {
        "name": "snowflake-arctic-embed:latest", 
        "dims": 1024,
        "description": "Snowflake 嵌入模型",
        "size": "669MB",
        "pull_command": "ollama pull snowflake-arctic-embed"
    }
}

def check_ollama_service():
    """检查 Ollama 服务是否运行"""
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

def list_ollama_models():
    """列出已安装的 Ollama 模型"""
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        return []
    except:
        return []

def download_embedding_model(model_name="nomic-embed-text"):
    """下载 Ollama 嵌入模型"""
    model_info = OLLAMA_MODELS.get(model_name, OLLAMA_MODELS["nomic-embed-text"])
    
    print(f"📥 下载 Ollama 嵌入模型: {model_info['name']}")
    print(f"   描述: {model_info['description']}")
    print(f"   大小: {model_info['size']}")
    print(f"   维度: {model_info['dims']}")
    print(f"\n   执行命令: {model_info['pull_command']}")
    
    import subprocess
    try:
        result = subprocess.run(
            ["ollama", "pull", model_info['name'].replace(":latest", "")],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            print(f"✅ 模型下载成功！")
            return True
        else:
            print(f"❌ 下载失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏱️ 下载超时，请手动执行命令")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_ollama_embedding():
    """测试 Ollama 嵌入模型"""
    print("🧪 测试 Ollama 嵌入模型...")
    
    # 检查 Ollama 服务
    if not check_ollama_service():
        print("❌ Ollama 服务未运行")
        print("   请先启动 Ollama: ollama serve")
        return False
    
    # 检查已安装的模型
    installed_models = list_ollama_models()
    print(f"📋 已安装的模型: {installed_models}")
    
    # 找到可用的嵌入模型
    available_embed_model = None
    for model in installed_models:
        for key, info in OLLAMA_MODELS.items():
            if info['name'] in model or key in model:
                available_embed_model = (key, info)
                break
        if available_embed_model:
            break
    
    if not available_embed_model:
        print("❌ 未找到嵌入模型，开始下载...")
        # 优先下载中文模型
        if download_embedding_model("bge-m3"):
            available_embed_model = ("bge-m3", OLLAMA_MODELS["bge-m3"])
        elif download_embedding_model("nomic-embed-text"):
            available_embed_model = ("nomic-embed-text", OLLAMA_MODELS["nomic-embed-text"])
        else:
            print("❌ 无法下载嵌入模型")
            return False
    
    # 使用找到的模型配置
    model_key, model_info = available_embed_model
    print(f"\n✅ 使用嵌入模型: {model_info['name']}")
    
    # 更新配置
    config = OLLAMA_CONFIG.copy()
    config["embedder"]["config"]["model"] = model_info["name"]
    config["vector_store"]["config"]["embedding_model_dims"] = model_info["dims"]
    
    # 测试初始化
    try:
        print("🔄 初始化记忆系统...")
        m = Memory.from_config(config)
        
        # 测试添加记忆
        test_text = "这是一个测试记忆，用于验证 Ollama 嵌入模型"
        result = m.add(test_text, user_id="test_user")
        print(f"✅ 添加记忆成功")
        
        # 测试搜索
        results = m.search("测试", user_id="test_user", limit=1)
        print(f"✅ 搜索成功，找到 {len(results['results'])} 条记忆")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def setup_ollama_embedding():
    """设置 Ollama 嵌入模型的完整流程"""
    print("🚀 设置 Ollama 嵌入模型")
    print("=" * 50)
    
    # 1. 检查 Ollama 服务
    if not check_ollama_service():
        print("\n❌ Ollama 服务未运行")
        print("🔧 请执行以下步骤：")
        print("   1. 安装 Ollama: brew install ollama")
        print("   2. 启动服务: ollama serve")
        return False
    
    print("✅ Ollama 服务正常")
    
    # 2. 列出可用模型
    print("\n📋 可用的嵌入模型：")
    for key, info in OLLAMA_MODELS.items():
        print(f"   • {key}: {info['description']} ({info['size']})")
    
    # 3. 推荐配置
    print("\n💡 推荐配置：")
    print("   1. bge-m3 - 中文语义理解最佳")
    print("   2. nomic-embed-text - 多语言支持好")
    print("   3. mxbai-embed-large - 平衡选择")
    
    # 4. 测试配置
    print("\n" + "=" * 50)
    return test_ollama_embedding()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ollama 嵌入模型配置')
    parser.add_argument('--download', '-d', 
                       choices=list(OLLAMA_MODELS.keys()),
                       help='下载指定的嵌入模型')
    parser.add_argument('--test', '-t', action='store_true',
                       help='测试 Ollama 嵌入配置')
    parser.add_argument('--setup', '-s', action='store_true',
                       help='完整设置流程')
    
    args = parser.parse_args()
    
    if args.download:
        download_embedding_model(args.download)
    elif args.test:
        test_ollama_embedding()
    elif args.setup:
        setup_ollama_embedding()
    else:
        # 默认执行设置流程
        success = setup_ollama_embedding()
        
        if success:
            print("\n✅ Ollama 嵌入模型配置成功！")
            print("💡 现在可以修改 deepseek_web_service.py 使用 Ollama 配置")
        else:
            print("\n❌ 配置失败，请按提示操作")