#!/usr/bin/env python3
"""
简化版Mem0 API服务器
用于测试基础功能，无需完整的AI模型
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from qdrant_client import QdrantClient
from typing import List, Dict, Any, Optional
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.getcwd())

app = FastAPI(
    title="Mem0 API - 简化版",
    description="Mem0智能记忆系统 - 测试版本",
    version="1.0.0-test",
    docs_url=None,  # 禁用默认docs
    redoc_url=None  # 禁用默认redoc
)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化Qdrant客户端
qdrant_client = None

# 内存数据存储 (用于演示真实数据操作)
memory_storage = {
    # user_id: [{"id": "", "content": "", "created_at": "", "user_id": "", "agent_id": ""}]
}
memory_counter = 0

def init_qdrant():
    """初始化Qdrant连接"""
    global qdrant_client
    try:
        qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            timeout=10
        )
        collections = qdrant_client.get_collections()
        print(f"✅ Qdrant连接成功: {len(collections.collections)} 个集合")
        return True
    except Exception as e:
        print(f"❌ Qdrant连接失败: {e}")
        return False

# 数据模型
class Message(BaseModel):
    role: str
    content: str

class MemoryRequest(BaseModel):
    messages: List[Message]
    user_id: str
    agent_id: Optional[str] = None
    run_id: Optional[str] = None

class MemoryResponse(BaseModel):
    message: str
    status: str

class SearchRequest(BaseModel):
    query: str
    user_id: str
    agent_id: Optional[str] = None
    limit: Optional[int] = 10

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    user_id: str
    count: int

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    print("🚀 启动Mem0 API服务...")
    init_qdrant()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Mem0 API - 简化测试版",
        "version": "1.0.0-test",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    qdrant_status = "connected" if qdrant_client else "disconnected"
    
    return {
        "status": "healthy",
        "services": {
            "qdrant": qdrant_status,
            "api": "running"
        }
    }

@app.get("/v1/collections")
async def get_collections():
    """获取Qdrant集合列表"""
    if not qdrant_client:
        raise HTTPException(status_code=500, detail="Qdrant未连接")
    
    try:
        collections = qdrant_client.get_collections()
        return {
            "collections": [{"name": col.name} for col in collections.collections],
            "count": len(collections.collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集合失败: {str(e)}")

@app.post("/v1/memories/")
async def create_memory(request: MemoryRequest):
    """创建记忆 - 使用真实数据存储"""
    global memory_counter
    
    # 验证输入
    if not request.messages:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    if not request.user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    # 提取用户消息内容
    user_messages = [msg.content for msg in request.messages if msg.role == "user"]
    assistant_messages = [msg.content for msg in request.messages if msg.role == "assistant"]
    
    if not user_messages:
        raise HTTPException(status_code=400, detail="未找到用户消息")
    
    # 合并对话内容作为记忆
    conversation_content = []
    for msg in request.messages:
        conversation_content.append(f"[{msg.role}]: {msg.content}")
    
    full_content = " | ".join(conversation_content)
    
    # 创建记忆对象
    memory_counter += 1
    memory_id = f"mem_{memory_counter:06d}"
    
    from datetime import datetime
    memory_obj = {
        "id": memory_id,
        "content": full_content,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "user_id": request.user_id,
        "agent_id": request.agent_id,
        "run_id": request.run_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "message_count": len(request.messages)
    }
    
    # 存储到内存数据库
    if request.user_id not in memory_storage:
        memory_storage[request.user_id] = []
    
    memory_storage[request.user_id].append(memory_obj)
    
    # 返回成功响应
    return MemoryResponse(
        message=f"✅ 已成功创建记忆 {memory_id}，内容：{user_messages[0][:50]}{'...' if len(user_messages[0]) > 50 else ''}",
        status="success"
    )

@app.get("/v1/memories/")
async def get_memories(user_id: str, limit: int = 10):
    """获取用户记忆 - 使用真实数据"""
    
    if not user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    # 从内存存储获取该用户的记忆
    user_memories = memory_storage.get(user_id, [])
    
    # 按创建时间倒序排序，最新的在前
    sorted_memories = sorted(user_memories, key=lambda x: x["created_at"], reverse=True)
    
    # 限制返回数量
    limited_memories = sorted_memories[:limit]
    
    # 格式化返回数据，只返回API需要的字段
    formatted_memories = []
    for memory in limited_memories:
        formatted_memories.append({
            "id": memory["id"],
            "content": memory["content"],
            "created_at": memory["created_at"],
            "user_id": memory["user_id"],
            "agent_id": memory.get("agent_id"),
            "run_id": memory.get("run_id"),
            "message_count": memory.get("message_count", 0)
        })
    
    return {
        "memories": formatted_memories,
        "user_id": user_id,
        "count": len(formatted_memories),
        "total_stored": len(user_memories)
    }

@app.post("/v1/memories/search")
async def search_memories(request: SearchRequest):
    """根据关键词搜索记忆 - 使用真实数据"""
    
    if not request.query:
        raise HTTPException(status_code=400, detail="查询关键词不能为空")
    
    if not request.user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    # 获取用户的所有记忆
    user_memories = memory_storage.get(request.user_id, [])
    
    if not user_memories:
        return SearchResponse(
            results=[],
            query=request.query,
            user_id=request.user_id,
            count=0
        )
    
    # 实现简单的关键词搜索算法
    query_terms = request.query.lower().split()
    search_results = []
    
    for memory in user_memories:
        content_lower = memory["content"].lower()
        
        # 计算匹配得分
        match_score = 0
        matched_terms = 0
        
        for term in query_terms:
            if term in content_lower:
                matched_terms += 1
                # 完全匹配加分更高
                if term in content_lower:
                    match_score += content_lower.count(term) * 10
        
        # 如果有匹配的关键词，添加到结果中
        if matched_terms > 0:
            relevance_score = (matched_terms / len(query_terms)) * (match_score / len(content_lower)) * 100
            
            search_results.append({
                "id": memory["id"],
                "content": memory["content"],
                "created_at": memory["created_at"],
                "user_id": memory["user_id"],
                "agent_id": memory.get("agent_id"),
                "run_id": memory.get("run_id"),
                "message_count": memory.get("message_count", 0),
                "matched_terms": matched_terms,
                "total_terms": len(query_terms),
                "relevance_score": round(relevance_score, 2)
            })
    
    # 按相关性得分排序
    search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # 限制返回数量
    limited_results = search_results[:request.limit]
    
    return SearchResponse(
        results=limited_results,
        query=request.query,
        user_id=request.user_id,
        count=len(limited_results)
    )

@app.get("/v1/memories/search")
async def search_memories_get(user_id: str, query: str, limit: int = 10, agent_id: Optional[str] = None):
    """根据关键词搜索记忆 - GET方式"""
    
    # 转换为POST请求的数据结构
    search_request = SearchRequest(
        query=query,
        user_id=user_id,
        agent_id=agent_id,
        limit=limit
    )
    
    return await search_memories(search_request)

@app.get("/v1/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    total_memories = 0
    total_users = len(memory_storage)
    
    user_stats = {}
    for user_id, memories in memory_storage.items():
        user_stats[user_id] = len(memories)
        total_memories += len(memories)
    
    return {
        "total_users": total_users,
        "total_memories": total_memories,
        "memory_counter": memory_counter,
        "users": user_stats,
        "status": "active"
    }

@app.delete("/v1/system/clear")
async def clear_all_data():
    """清理所有数据 (仅用于测试)"""
    global memory_storage, memory_counter
    
    old_total = sum(len(memories) for memories in memory_storage.values())
    old_users = len(memory_storage)
    
    memory_storage.clear()
    memory_counter = 0
    
    return {
        "message": f"✅ 已清理所有数据",
        "cleared": {
            "users": old_users,
            "memories": old_total
        },
        "status": "success"
    }

@app.delete("/v1/memories/user/{user_id}")
async def delete_user_memories(user_id: str):
    """删除指定用户的所有记忆"""
    if user_id not in memory_storage:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有记忆数据")
    
    deleted_count = len(memory_storage[user_id])
    del memory_storage[user_id]
    
    return {
        "message": f"✅ 已删除用户 {user_id} 的 {deleted_count} 条记忆",
        "user_id": user_id,
        "deleted_count": deleted_count,
        "status": "success"
    }

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义API文档 - 使用国内CDN"""
    from fastapi.responses import HTMLResponse
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mem0 API 文档</title>
        <link rel="stylesheet" type="text/css" href="/static/swagger-ui.css" />
        <link rel="icon" type="image/png" href="/static/favicon-32x32.png" sizes="32x32" />
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}
            *, *:before, *:after {{
                box-sizing: inherit;
            }}
            body {{
                margin:0;
                background: #fafafa;
            }}
            .local-info {{
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(34,139,34,0.8);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 9999;
            }}
        </style>
    </head>
    <body>
        <div class="local-info">本地资源 🚀</div>
        <div id="swagger-ui"></div>
        <script src="/static/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "BaseLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc文档 - 使用国内CDN"""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Mem0 API 文档 (ReDoc)",
        redoc_js_url="https://cdn.bootcdn.net/ajax/libs/redoc/2.1.5/bundles/redoc.standalone.js"
    )

if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("PYTHONPATH", os.getcwd())
    
    print("🌐 启动Mem0 API服务 - 简化测试版")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python路径: {sys.path[0]}")
    
    # 启动服务
    uvicorn.run(
        "simple-api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )