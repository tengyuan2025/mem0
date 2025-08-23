#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Qdrant Web 服务版本（备用配置）
当 HuggingFace 模型无法下载时使用 OpenAI 嵌入
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from mem0 import Memory

# 设置 API Keys
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# 主配置（HuggingFace）
PRIMARY_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_web_memories",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,
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
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-large-zh-v1.5",
        },
    },
}

# 备用配置（OpenAI）
BACKUP_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "deepseek_web_memories_backup",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1536,  # OpenAI 嵌入维度
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
            "model": "text-embedding-3-small",
        },
    },
}

# 初始化 FastAPI
app = FastAPI(
    title="DeepSeek + Qdrant 记忆服务 (备用版本)",
    description="基于 DeepSeek API 和 Qdrant 向量数据库的中文记忆系统，支持多种嵌入模型",
    version="1.0.1"
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 自定义 Swagger UI 文档页面（使用本地资源）
app.docs_url = None  # 禁用默认文档页面

@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
async def custom_swagger_ui_html():
    """自定义 Swagger UI 页面，使用本地资源"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="/static/swagger-ui/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>DeepSeek + Qdrant 记忆服务 - Swagger UI</title>
    </head>
    <body>
        <div id="swagger-ui">
        </div>
        <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            layout: "StandaloneLayout",
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            tryItOutEnabled: true,
            displayRequestDuration: true,
            docExpansion: "list",
            filter: true,
            showRequestHeaders: true
        })
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# 初始化记忆系统
memory_system = None
current_config = None

# 请求模型
class AddMemoryRequest(BaseModel):
    text: str
    user_id: str = "default_user"
    metadata: Optional[Dict] = None

class SearchMemoryRequest(BaseModel):
    query: str
    user_id: str = "default_user" 
    limit: int = 5

def check_qdrant_connection():
    """检查 Qdrant 连接"""
    try:
        endpoints = [
            "http://localhost:6333",
            "http://localhost:6333/collections", 
            "http://localhost:6333/cluster"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code in [200, 404]:
                    return True
            except:
                continue
        return False
    except:
        return False

def initialize_memory_system():
    """智能初始化记忆系统，优先使用 HuggingFace，失败时使用 OpenAI"""
    global memory_system, current_config
    
    print("🚀 智能初始化记忆系统...")
    
    # 首先尝试主配置（HuggingFace）
    print("🔄 尝试主配置 (HuggingFace)...")
    try:
        # 设置 HuggingFace 镜像
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        memory_system = Memory.from_config(PRIMARY_CONFIG)
        current_config = PRIMARY_CONFIG
        print("✅ 主配置初始化成功 (HuggingFace 嵌入)")
        return True
        
    except Exception as e:
        print(f"❌ 主配置失败: {str(e)[:100]}...")
        
        # 尝试备用配置（OpenAI）
        print("🔄 尝试备用配置 (OpenAI)...")
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  未设置 OPENAI_API_KEY，请设置后使用备用配置")
            print("   export OPENAI_API_KEY='your-openai-api-key'")
            return False
        
        try:
            memory_system = Memory.from_config(BACKUP_CONFIG)
            current_config = BACKUP_CONFIG
            print("✅ 备用配置初始化成功 (OpenAI 嵌入)")
            return True
            
        except Exception as e2:
            print(f"❌ 备用配置也失败: {str(e2)[:100]}...")
            return False

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化"""
    print("🌐 启动 DeepSeek + Qdrant Web 服务 (智能版)...")
    print("📝 Web 界面: http://localhost:9000")
    print("📖 API 文档: http://localhost:9000/docs")
    print("🔧 Qdrant UI: http://localhost:6333/dashboard")
    
    # 等待 Qdrant 启动并检查连接
    import time
    max_retries = 30
    for i in range(max_retries):
        if check_qdrant_connection():
            print("✅ Qdrant 连接成功")
            break
        print(f"⏳ 等待 Qdrant 启动... ({i+1}/{max_retries})")
        time.sleep(1)
    else:
        print("❌ Qdrant 连接超时")
    
    # 智能初始化记忆系统
    if not initialize_memory_system():
        print("⚠️  记忆系统初始化失败，服务将继续运行但功能受限")

# API 端点
@app.get("/")
async def root():
    """主页面"""
    config_info = "未初始化"
    if current_config:
        embedder = current_config["embedder"]["provider"]
        model = current_config["embedder"]["config"]["model"]
        config_info = f"{embedder}: {model}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DeepSeek + Qdrant 记忆系统 (智能版)</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .status {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 DeepSeek + Qdrant 记忆系统</h1>
            <p>智能版本 - 自动选择最佳嵌入模型配置</p>
            
            <div class="status">
                <h3>📊 当前状态</h3>
                <p><strong>记忆系统:</strong> {'✅ 正常' if memory_system else '❌ 异常'}</p>
                <p><strong>嵌入配置:</strong> {config_info}</p>
                <p><strong>LLM:</strong> DeepSeek API</p>
                <p><strong>向量存储:</strong> Qdrant</p>
            </div>
            
            <h3>🔗 快速链接</h3>
            <ul>
                <li><a href="/docs">📖 API 文档 (Swagger UI)</a></li>
                <li><a href="http://localhost:6333/dashboard" target="_blank">🔧 Qdrant 管理界面</a></li>
                <li><a href="/api/status">📊 系统状态 API</a></li>
            </ul>
            
            <h3>💡 使用建议</h3>
            <ul>
                <li>主配置使用 HuggingFace 中文嵌入模型，效果最佳</li>
                <li>备用配置使用 OpenAI 嵌入模型，需要 API Key</li>
                <li>系统会自动选择可用的配置</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/memories")
async def add_memory(request: AddMemoryRequest):
    """添加记忆"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
    
    try:
        result = memory_system.add(
            request.text, 
            user_id=request.user_id,
            metadata=request.metadata
        )
        return {"success": True, "message": "记忆添加成功", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")  
async def search_memories(request: SearchMemoryRequest):
    """搜索记忆"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
    
    try:
        results = memory_system.search(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit
        )
        return {"success": True, "memories": results["results"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories/{user_id}")
async def get_all_memories(user_id: str):
    """获取所有记忆"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
    
    try:
        results = memory_system.get_all(user_id=user_id)
        return {"success": True, "memories": results["results"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆"""
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
    
    try:
        memory_system.delete(memory_id=memory_id)
        return {"success": True, "message": "记忆删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    config_info = {}
    if current_config:
        config_info = {
            "embedder_provider": current_config["embedder"]["provider"],
            "embedder_model": current_config["embedder"]["config"]["model"],
            "collection_name": current_config["vector_store"]["config"]["collection_name"],
            "embedding_dims": current_config["vector_store"]["config"]["embedding_model_dims"]
        }
    
    return {
        "qdrant_status": check_qdrant_connection(),
        "memory_system": memory_system is not None,
        "llm_model": "deepseek-chat",
        **config_info
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🌐 启动 DeepSeek + Qdrant Web 服务 (智能版)...")
    print("📝 Web 界面: http://localhost:9000")
    print("📖 API 文档: http://localhost:9000/docs")
    print("🔧 Qdrant UI: http://localhost:6333/dashboard")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=9000,
        log_level="info"
    )