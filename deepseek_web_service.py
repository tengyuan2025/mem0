#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek + Qdrant Web 服务版本
提供 HTTP API 和简单的 Web 界面
"""

import os
import json
import subprocess
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from mem0 import Memory
# 移除自定义导入

def start_ollama_service():
    """启动 Ollama 服务"""
    try:
        # 检查 Ollama 是否已经在运行
        result = subprocess.run(["pgrep", "-f", "ollama"], capture_output=True)
        if result.returncode == 0:
            print("✅ Ollama 服务已在运行")
            return True
        
        print("🔄 启动 Ollama 服务...")
        # 在后台启动 Ollama
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待服务启动
        for i in range(10):
            time.sleep(1)
            try:
                response = requests.get("http://localhost:11434/api/version", timeout=2)
                if response.status_code == 200:
                    print("✅ Ollama 服务启动成功")
                    return True
            except:
                continue
        
        print("⚠️ Ollama 服务启动超时，请手动启动: ollama serve")
        return False
        
    except Exception as e:
        print(f"❌ 启动 Ollama 服务失败: {e}")
        return False

# 设置 DeepSeek API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-760dd8899ad54634802aafb839f8bda9"

# Qdrant + HuggingFace 配置
CONFIG = {
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
        "provider": "ollama",
        "config": {
            "model": "bge-m3",
        },
    },
}

# 初始化 FastAPI
app = FastAPI(
    title="DeepSeek + Qdrant 记忆服务",
    description="基于 DeepSeek API 和 Qdrant 向量数据库的中文记忆系统",
    version="1.0.0"
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

# 请求模型
class AddMemoryRequest(BaseModel):
    text: str
    user_id: str = "default_user"
    metadata: Optional[Dict] = None

class SearchMemoryRequest(BaseModel):
    query: str
    user_id: str = "default_user" 
    limit: int = 5

class DeleteMemoryRequest(BaseModel):
    memory_id: str


def enhance_memory_with_time(text: str) -> str:
    """
    增强记忆文本，将相对时间表达转换为具体时间
    
    Args:
        text: 原始记忆文本
        
    Returns:
        增强后的记忆文本
    """
    now = datetime.now()
    enhanced_text = text
    
    # 时间模式匹配和替换规则
    time_patterns = [
        # 今天相关
        (r'今天([上下]午|早上|晚上|中午)?', lambda m: f"今天{m.group(1) if m.group(1) else ''}({now.strftime('%Y年%m月%d日')})"),
        (r'今日([上下]午|早上|晚上|中午)?', lambda m: f"今日{m.group(1) if m.group(1) else ''}({now.strftime('%Y年%m月%d日')})"),
        
        # 昨天相关  
        (r'昨天([上下]午|早上|晚上|中午)?', lambda m: f"昨天{m.group(1) if m.group(1) else ''}({(now - timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        (r'昨日([上下]午|早上|晚上|中午)?', lambda m: f"昨日{m.group(1) if m.group(1) else ''}({(now - timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        
        # 明天相关
        (r'明天([上下]午|早上|晚上|中午)?', lambda m: f"明天{m.group(1) if m.group(1) else ''}({(now + timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        (r'明日([上下]午|早上|晚上|中午)?', lambda m: f"明日{m.group(1) if m.group(1) else ''}({(now + timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        
        # 前天、后天
        (r'前天([上下]午|早上|晚上|中午)?', lambda m: f"前天{m.group(1) if m.group(1) else ''}({(now - timedelta(days=2)).strftime('%Y年%m月%d日')})"),
        (r'后天([上下]午|早上|晚上|中午)?', lambda m: f"后天{m.group(1) if m.group(1) else ''}({(now + timedelta(days=2)).strftime('%Y年%m月%d日')})"),
        
        # 本周、上周、下周
        (r'本周', lambda m: f"本周({now.strftime('%Y年第%U周')})"),
        (r'这周', lambda m: f"这周({now.strftime('%Y年第%U周')})"),
        (r'上周', lambda m: f"上周({(now - timedelta(days=7)).strftime('%Y年第%U周')})"),
        (r'下周', lambda m: f"下周({(now + timedelta(days=7)).strftime('%Y年第%U周')})"),
        
        # 现在、刚才
        (r'现在', lambda m: f"现在({now.strftime('%Y年%m月%d日 %H:%M')})"),
        (r'刚才', lambda m: f"刚才({now.strftime('%Y年%m月%d日 %H:%M')})"),
        (r'刚刚', lambda m: f"刚刚({now.strftime('%Y年%m月%d日 %H:%M')})"),
    ]
    
    # 应用所有时间模式
    changes_made = []
    for pattern, replacement in time_patterns:
        matches = list(re.finditer(pattern, enhanced_text))
        if matches:
            for match in reversed(matches):  # 从后往前替换避免索引问题
                original = match.group(0)
                new_text = replacement(match)
                enhanced_text = enhanced_text[:match.start()] + new_text + enhanced_text[match.end():]
                changes_made.append(f"'{original}' → '{new_text}'")
    
    # 如果有改动，记录日志
    if changes_made:
        print(f"🕒 [TIME_ENHANCE] 时间增强处理:")
        for change in changes_made:
            print(f"   {change}")
        print(f"   原文本: {text}")
        print(f"   增强后: {enhanced_text}")
    else:
        print(f"🕒 [TIME_ENHANCE] 未检测到需要增强的时间表达")
        
    return enhanced_text


def check_qdrant_connection():
    """检查 Qdrant 连接"""
    try:
        # 尝试多个端点来检查 Qdrant 状态
        endpoints = [
            "http://localhost:6333",
            "http://localhost:6333/collections", 
            "http://localhost:6333/cluster"
        ]
        
        # 绕过代理设置
        proxies = {
            'http': None,
            'https': None
        }
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5, proxies=proxies)
                if response.status_code in [200, 404]:  # 404 也表示服务在运行
                    return True
            except:
                continue
        return False
    except:
        return False


@app.on_event("startup")
async def startup_event():
    """服务启动时初始化"""
    global memory_system
    
    print("🚀 启动 DeepSeek + Qdrant Web 服务...")
    
    # 检查 Qdrant 连接
    if check_qdrant_connection():
        print("✅ Qdrant 连接成功")
    else:
        print("❌ Qdrant 连接失败，请检查:")
        print("   1. 容器是否运行: docker ps | grep qdrant")
        print("   2. 端口是否开放: lsof -i :6333")
        print("   3. 重启容器: docker restart qdrant")
        print("⚠️  将继续启动服务，但记忆功能受限")
    
    # 启动 Ollama 服务
    start_ollama_service()
    
    # 初始化记忆系统
    try:
        # 临时禁用代理以避免内部请求失败
        old_http_proxy = os.environ.get('HTTP_PROXY')
        old_https_proxy = os.environ.get('HTTPS_PROXY')
        old_http_proxy_lower = os.environ.get('http_proxy')
        old_https_proxy_lower = os.environ.get('https_proxy')
        
        # 临时清除代理设置
        if old_http_proxy:
            del os.environ['HTTP_PROXY']
        if old_https_proxy:
            del os.environ['HTTPS_PROXY']
        if old_http_proxy_lower:
            del os.environ['http_proxy']
        if old_https_proxy_lower:
            del os.environ['https_proxy']
        
        try:
            memory_system = Memory.from_config(CONFIG)
            print("✅ 记忆系统初始化成功")
        finally:
            # 恢复代理设置
            if old_http_proxy:
                os.environ['HTTP_PROXY'] = old_http_proxy
            if old_https_proxy:
                os.environ['HTTPS_PROXY'] = old_https_proxy
            if old_http_proxy_lower:
                os.environ['http_proxy'] = old_http_proxy_lower
            if old_https_proxy_lower:
                os.environ['https_proxy'] = old_https_proxy_lower
                
    except Exception as e:
        print(f"❌ 记忆系统初始化失败: {e}")
        print("⚠️  服务将继续运行，但记忆功能不可用")
        # 不抛出异常，允许 Web 服务启动


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DeepSeek + Qdrant 记忆系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .form-group { margin: 10px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; }
            .memory-item { margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 4px; }
            .score { color: #666; font-size: 0.9em; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 DeepSeek + Qdrant 记忆系统</h1>
                <p>基于 DeepSeek API 和 Qdrant 向量数据库的中文记忆系统</p>
            </div>
            
            <div class="section">
                <h3>💾 添加记忆</h3>
                <div class="form-group">
                    <label>记忆内容:</label>
                    <textarea id="addText" rows="3" placeholder="输入要记住的内容..."></textarea>
                </div>
                <div class="form-group">
                    <label>用户ID:</label>
                    <input type="text" id="addUserId" value="demo_user" placeholder="用户标识">
                </div>
                <button onclick="addMemory()">添加记忆</button>
                <div id="addResult" class="result" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h3>🔍 搜索记忆</h3>
                <div class="form-group">
                    <label>搜索关键词:</label>
                    <input type="text" id="searchQuery" placeholder="输入搜索关键词...">
                </div>
                <div class="form-group">
                    <label>用户ID:</label>
                    <input type="text" id="searchUserId" value="demo_user" placeholder="用户标识">
                </div>
                <div class="form-group">
                    <label>结果数量:</label>
                    <input type="number" id="searchLimit" value="5" min="1" max="20">
                </div>
                <button onclick="searchMemories()">搜索记忆</button>
                <div id="searchResult" class="result" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h3>📚 所有记忆</h3>
                <div class="form-group">
                    <label>用户ID:</label>
                    <input type="text" id="listUserId" value="demo_user" placeholder="用户标识">
                </div>
                <button onclick="listMemories()">获取所有记忆</button>
                <div id="listResult" class="result" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h3>📊 系统状态</h3>
                <button onclick="getStatus()">检查系统状态</button>
                <div id="statusResult" class="result" style="display:none;"></div>
            </div>
        </div>
        
        <script>
            async function addMemory() {
                const text = document.getElementById('addText').value;
                const userId = document.getElementById('addUserId').value;
                const resultDiv = document.getElementById('addResult');
                
                if (!text.trim()) {
                    showResult(resultDiv, '请输入记忆内容', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/memories', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: text, user_id: userId})
                    });
                    
                    const data = await response.json();
                    if (response.ok) {
                        showResult(resultDiv, '✅ 记忆添加成功！', 'success');
                        document.getElementById('addText').value = '';
                    } else {
                        showResult(resultDiv, '❌ 添加失败: ' + data.detail, 'error');
                    }
                } catch (error) {
                    showResult(resultDiv, '❌ 网络错误: ' + error, 'error');
                }
            }
            
            async function searchMemories() {
                const query = document.getElementById('searchQuery').value;
                const userId = document.getElementById('searchUserId').value;
                const limit = document.getElementById('searchLimit').value;
                const resultDiv = document.getElementById('searchResult');
                
                if (!query.trim()) {
                    showResult(resultDiv, '请输入搜索关键词', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query: query, user_id: userId, limit: parseInt(limit)})
                    });
                    
                    const data = await response.json();
                    if (response.ok) {
                        displayMemories(resultDiv, data.memories, '🔍 搜索结果');
                    } else {
                        showResult(resultDiv, '❌ 搜索失败: ' + data.detail, 'error');
                    }
                } catch (error) {
                    showResult(resultDiv, '❌ 网络错误: ' + error, 'error');
                }
            }
            
            async function listMemories() {
                const userId = document.getElementById('listUserId').value;
                const resultDiv = document.getElementById('listResult');
                
                try {
                    const response = await fetch(`/api/memories/${userId}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        displayMemories(resultDiv, data.memories, '📚 所有记忆');
                    } else {
                        showResult(resultDiv, '❌ 获取失败: ' + data.detail, 'error');
                    }
                } catch (error) {
                    showResult(resultDiv, '❌ 网络错误: ' + error, 'error');
                }
            }
            
            async function getStatus() {
                const resultDiv = document.getElementById('statusResult');
                
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    let html = '<h4>系统状态:</h4>';
                    html += `<p>Qdrant: ${data.qdrant_status ? '✅ 正常' : '❌ 异常'}</p>`;
                    html += `<p>记忆系统: ${data.memory_system ? '✅ 正常' : '❌ 异常'}</p>`;
                    html += `<p>集合名称: ${data.collection_name}</p>`;
                    html += `<p>嵌入模型: ${data.embedder_model}</p>`;
                    
                    resultDiv.innerHTML = html;
                    resultDiv.style.display = 'block';
                } catch (error) {
                    showResult(resultDiv, '❌ 获取状态失败: ' + error, 'error');
                }
            }
            
            function displayMemories(div, memories, title) {
                if (memories.length === 0) {
                    showResult(div, title + ': 暂无记忆', 'success');
                    return;
                }
                
                let html = `<h4>${title} (${memories.length} 条):</h4>`;
                memories.forEach((mem, index) => {
                    html += `<div class="memory-item">
                        <strong>${index + 1}.</strong> ${mem.memory}
                        ${mem.score ? `<div class="score">相关度: ${mem.score.toFixed(4)}</div>` : ''}
                        <div class="score">ID: ${mem.id.substring(0, 12)}...</div>
                    </div>`;
                });
                
                div.innerHTML = html;
                div.style.display = 'block';
            }
            
            function showResult(div, message, type) {
                div.innerHTML = `<span class="${type}">${message}</span>`;
                div.style.display = 'block';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/memories",
          summary="添加记忆",
          description="向系统中添加新的记忆内容")
async def add_memory(request: AddMemoryRequest):
    """
    添加新的记忆到系统中
    
    Args:
        request: 包含记忆文本、用户ID和元数据的请求对象
        
    Returns:
        添加结果信息
    """
    print(f"🔍 [ADD_MEMORY] 收到请求:")
    print(f"   文本: '{request.text}'")
    print(f"   用户ID: '{request.user_id}'")
    print(f"   元数据: {request.metadata}")
    
    if not memory_system:
        print("❌ [ADD_MEMORY] 记忆系统未初始化")
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
        
    try:
        # 时间增强处理
        enhanced_text = enhance_memory_with_time(request.text)
        
        print("🔄 [ADD_MEMORY] 开始调用 memory_system.add()...")
        result = memory_system.add(
            enhanced_text, 
            user_id=request.user_id,
            metadata=request.metadata
        )
        print(f"✅ [ADD_MEMORY] memory_system.add() 返回结果:")
        print(f"   结果类型: {type(result)}")
        print(f"   结果内容: {result}")
        
        # 验证是否真的保存成功 - 立即查询
        print("🔍 [ADD_MEMORY] 验证保存结果 - 立即查询...")
        try:
            verification = memory_system.get_all(user_id=request.user_id)
            print(f"   验证查询结果: {verification}")
        except Exception as ve:
            print(f"   验证查询失败: {ve}")
        
        return {
            "success": True, 
            "message": "记忆添加成功", 
            "result": result,
            "original_text": request.text,
            "enhanced_text": enhanced_text,
            "time_enhanced": enhanced_text != request.text
        }
    except Exception as e:
        print(f"❌ [ADD_MEMORY] 添加记忆失败: {e}")
        print(f"   异常类型: {type(e)}")
        import traceback
        print(f"   堆栈跟踪: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search",
          summary="搜索记忆",
          description="根据关键词搜索相关的记忆内容")  
async def search_memories(request: SearchMemoryRequest):
    """
    搜索相关记忆
    
    Args:
        request: 包含搜索查询、用户ID和结果限制的请求对象
        
    Returns:
        匹配的记忆列表，按相关度排序
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
        
    try:
        results = memory_system.search(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit
        )
        return {"success": True, "memories": results["results"], "count": len(results["results"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories/{user_id}", 
         summary="获取用户所有记忆",
         description="根据用户ID获取该用户的所有记忆内容")
async def get_all_memories(user_id: str):
    """
    获取指定用户的所有记忆
    
    Args:
        user_id: 用户标识符
        
    Returns:
        所有记忆的列表
    """
    print(f"🔍 [GET_ALL] 收到查询请求:")
    print(f"   用户ID: '{user_id}'")
    
    if not memory_system:
        print("❌ [GET_ALL] 记忆系统未初始化")
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
        
    try:
        print("🔄 [GET_ALL] 开始调用 memory_system.get_all()...")
        results = memory_system.get_all(user_id=user_id)
        print(f"✅ [GET_ALL] memory_system.get_all() 返回结果:")
        print(f"   结果类型: {type(results)}")
        print(f"   结果内容: {results}")
        
        if isinstance(results, dict) and "results" in results:
            memories = results["results"]
            print(f"   记忆数量: {len(memories)}")
            for i, mem in enumerate(memories[:3]):  # 只显示前3条
                print(f"   记忆{i+1}: {mem}")
        else:
            print(f"   ⚠️ 结果格式异常")
            
        return {"success": True, "memories": results["results"], "count": len(results["results"])}
    except Exception as e:
        print(f"❌ [GET_ALL] 查询记忆失败: {e}")
        print(f"   异常类型: {type(e)}")
        import traceback
        print(f"   堆栈跟踪: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/all-memories", 
         summary="获取记忆",
         description="获取指定用户的记忆数据，默认返回default_user的数据")
async def get_all_memories_query(user_id: str = "default_user"):
    """
    获取指定用户的记忆数据
    
    Args:
        user_id: 用户标识符，默认为default_user
        
    Returns:
        指定用户的记忆列表
    """
    print(f"🔍 [GET_ALL_QUERY] 收到查询请求:")
    print(f"   用户ID: '{user_id}'")
    
    if not memory_system:
        print("❌ [GET_ALL_QUERY] 记忆系统未初始化")
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
        
    try:
        print("🔄 [GET_ALL_QUERY] 开始调用 memory_system.get_all()...")
        results = memory_system.get_all(user_id=user_id)
        print(f"✅ [GET_ALL_QUERY] memory_system.get_all() 返回结果:")
        print(f"   结果类型: {type(results)}")
        print(f"   结果内容: {results}")
        
        if isinstance(results, dict) and "results" in results:
            memories = results["results"]
            print(f"   记忆数量: {len(memories)}")
        else:
            print(f"   ⚠️ 结果格式异常")
            
        return {"success": True, "user_id": user_id, "memories": results["results"], "count": len(results["results"])}
    except Exception as e:
        print(f"❌ [GET_ALL_QUERY] 查询记忆失败: {e}")
        print(f"   异常类型: {type(e)}")
        import traceback
        print(f"   堆栈跟踪: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/all-users-memories", 
         summary="获取所有用户的记忆",
         description="通过查询多个常见用户ID来获取尽可能多的用户记忆数据")
async def get_all_users_memories():
    """
    获取所有用户的记忆数据（通过查询多个常见用户ID）
    
    Returns:
        所有找到的用户记忆数据
    """
    print(f"🔍 [GET_ALL_USERS] 收到查询所有用户记忆请求")
    
    if not memory_system:
        print("❌ [GET_ALL_USERS] 记忆系统未初始化")
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
        
    try:
        # 常见的用户ID列表
        common_user_ids = [
            "default_user", "demo_user", "test_user", "user1", "user2", 
            "admin", "guest", "张三", "李四", "王五"
        ]
        
        all_memories = []
        user_counts = {}
        
        for user_id in common_user_ids:
            try:
                results = memory_system.get_all(user_id=user_id)
                if results and "results" in results and len(results["results"]) > 0:
                    user_counts[user_id] = len(results["results"])
                    for memory in results["results"]:
                        memory["source_user_id"] = user_id  # 添加来源用户标识
                    all_memories.extend(results["results"])
                    print(f"   ✅ 用户 '{user_id}': 找到 {len(results['results'])} 条记忆")
                else:
                    print(f"   ⭕ 用户 '{user_id}': 无记忆数据")
            except Exception as e:
                print(f"   ❌ 查询用户 '{user_id}' 失败: {e}")
                continue
        
        print(f"✅ [GET_ALL_USERS] 总计找到记忆:")
        print(f"   总记忆数: {len(all_memories)}")
        print(f"   涉及用户: {list(user_counts.keys())}")
        print(f"   各用户计数: {user_counts}")
            
        return {
            "success": True, 
            "memories": all_memories, 
            "total_count": len(all_memories),
            "user_counts": user_counts,
            "searched_users": common_user_ids
        }
        
    except Exception as e:
        print(f"❌ [GET_ALL_USERS] 查询所有用户记忆失败: {e}")
        import traceback
        print(f"   堆栈跟踪: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/memories/{memory_id}",
            summary="删除记忆", 
            description="根据记忆ID删除指定的记忆")
async def delete_memory(memory_id: str):
    """
    删除指定的记忆
    
    Args:
        memory_id: 要删除的记忆的唯一标识符
        
    Returns:
        删除操作的结果
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")
        
    try:
        memory_system.delete(memory_id=memory_id)
        return {"success": True, "message": "记忆删除成功", "deleted_id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status",
         summary="系统状态",
         description="获取系统各组件的运行状态信息")
async def get_status():
    """
    获取系统状态信息
    
    Returns:
        包含各组件状态的详细信息
    """
    return {
        "qdrant_status": check_qdrant_connection(),
        "memory_system": memory_system is not None,
        "collection_name": CONFIG["vector_store"]["config"]["collection_name"],
        "embedder_model": CONFIG["embedder"]["config"]["model"],
        "llm_model": CONFIG["llm"]["config"]["model"],
        "embedder_provider": CONFIG["embedder"]["provider"],
        "vector_store_provider": CONFIG["vector_store"]["provider"]
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🌐 启动 DeepSeek + Qdrant Web 服务...")
    print("📝 Web 界面: http://localhost:9000")
    print("📖 API 文档: http://localhost:9000/docs")
    print("🔧 Qdrant UI: http://localhost:6333/dashboard")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=9000,
        log_level="info"
    )