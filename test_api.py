#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的API测试版本，不依赖外部服务
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn

app = FastAPI(
    title="DeepSeek + Qdrant 记忆服务 (测试版)",
    description="基于 DeepSeek API 和 Qdrant 向量数据库的中文记忆系统",
    version="1.0.0"
)

# 自定义 Swagger UI 文档页面
app.docs_url = None

@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
async def custom_swagger_ui_html():
    """自定义 Swagger UI 页面"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>DeepSeek + Qdrant 记忆服务 - Swagger UI</title>
    </head>
    <body>
        <div id="swagger-ui">
        </div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
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

# 请求模型
class AddMemoryRequest(BaseModel):
    text: str
    user_id: str = "default_user"
    metadata: Optional[Dict] = None

class SearchMemoryRequest(BaseModel):
    query: str
    user_id: str = "default_user" 
    limit: int = 5

# API 端点
@app.post("/api/memories",
          summary="添加记忆",
          description="向系统中添加新的记忆内容")
async def add_memory(request: AddMemoryRequest):
    """添加新的记忆到系统中"""
    return {"success": True, "message": "记忆添加成功 (测试模式)", "result": "test-id-123"}

@app.post("/api/search",
          summary="搜索记忆",
          description="根据关键词搜索相关的记忆内容")  
async def search_memories(request: SearchMemoryRequest):
    """搜索相关记忆"""
    return {
        "success": True, 
        "memories": [
            {"id": "test-1", "memory": "测试记忆1", "score": 0.95},
            {"id": "test-2", "memory": "测试记忆2", "score": 0.88}
        ],
        "count": 2
    }

@app.get("/api/memories/{user_id}", 
         summary="获取用户所有记忆",
         description="根据用户ID获取该用户的所有记忆内容")
async def get_all_memories(user_id: str):
    """获取指定用户的所有记忆"""
    return {
        "success": True, 
        "memories": [
            {"id": "test-1", "memory": f"用户 {user_id} 的测试记忆1"},
            {"id": "test-2", "memory": f"用户 {user_id} 的测试记忆2"},
            {"id": "test-3", "memory": f"用户 {user_id} 的测试记忆3"}
        ],
        "count": 3
    }

@app.get("/api/all-memories", 
         summary="获取所有记忆（查询参数版本）",
         description="通过查询参数指定用户ID来获取所有记忆，便于在 Swagger UI 中测试")
async def get_all_memories_query(user_id: str = "demo_user"):
    """获取指定用户的所有记忆（查询参数版本）"""
    return {
        "success": True, 
        "user_id": user_id,
        "memories": [
            {"id": "query-test-1", "memory": f"查询参数版本 - 用户 {user_id} 的记忆1"},
            {"id": "query-test-2", "memory": f"查询参数版本 - 用户 {user_id} 的记忆2"}
        ],
        "count": 2
    }

@app.delete("/api/memories/{memory_id}",
            summary="删除记忆", 
            description="根据记忆ID删除指定的记忆")
async def delete_memory(memory_id: str):
    """删除指定的记忆"""
    return {"success": True, "message": "记忆删除成功 (测试模式)", "deleted_id": memory_id}

@app.get("/api/status",
         summary="系统状态",
         description="获取系统各组件的运行状态信息")
async def get_status():
    """获取系统状态信息"""
    return {
        "qdrant_status": True,
        "memory_system": True,
        "collection_name": "test_collection",
        "embedder_model": "test-model",
        "llm_model": "deepseek-chat",
        "mode": "test"
    }

if __name__ == "__main__":
    print("🧪 启动测试版 API 服务...")
    print("📝 Web 界面: http://localhost:9000")
    print("📖 API 文档: http://localhost:9000/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=9000,
        log_level="info"
    )