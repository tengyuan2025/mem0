"""
Mem0 最小化本地测试版本
支持本地中文嵌入模型，无需复杂依赖
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
from datetime import datetime
import hashlib
import json
import asyncio
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")

# ==========================================
# 数据模型
# ==========================================

class MemoryAddRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    messages: List[Dict[str, str]] = Field(..., description="对话消息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

class MemorySearchRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="搜索查询")
    limit: Optional[int] = Field(default=10, description="返回数量限制")

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., description="用户消息")
    use_memory: bool = Field(default=True, description="是否使用记忆")

# ==========================================
# 简化的记忆管理器
# ==========================================

class SimpleMemoryManager:
    """简化的记忆管理器 - 使用内存存储"""
    
    def __init__(self):
        self.memories = {}  # user_id -> List[memory]
        self.embedding_model = None
        self.initialized = False
        
    async def initialize(self):
        """初始化记忆管理器"""
        if self.initialized:
            return
            
        try:
            # 尝试初始化本地嵌入模型
            embedding_provider = os.getenv("EMBEDDING_PROVIDER", "none")
            
            if embedding_provider in ["local_huggingface", "sentence_transformers"]:
                try:
                    from sentence_transformers import SentenceTransformer
                    model_name = os.getenv("HF_EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
                    logger.info(f"正在加载本地嵌入模型: {model_name}")
                    self.embedding_model = SentenceTransformer(model_name)
                    logger.info("本地嵌入模型加载成功")
                except ImportError:
                    logger.warning("sentence-transformers未安装，使用简单文本匹配")
                    self.embedding_model = None
                except Exception as e:
                    logger.warning(f"加载嵌入模型失败: {e}，使用简单文本匹配")
                    self.embedding_model = None
            else:
                logger.info("未配置本地嵌入模型，使用简单文本匹配")
                self.embedding_model = None
                
            self.initialized = True
            logger.info("记忆管理器初始化成功")
            
        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")
            raise
    
    async def add_memory(self, user_id: str, messages: List[Dict], metadata: Dict = None) -> Dict:
        """添加记忆"""
        try:
            # 提取对话内容
            content = " | ".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # 生成记忆ID
            memory_id = hashlib.md5(
                f"{user_id}_{content}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:12]
            
            # 生成embedding（如果有模型）
            embedding = None
            if self.embedding_model:
                try:
                    embeddings = self.embedding_model.encode([content])
                    embedding = embeddings[0].tolist()
                except Exception as e:
                    logger.warning(f"生成embedding失败: {e}")
            
            # 准备元数据
            metadata = metadata or {}
            metadata.update({
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "content": content
            })
            
            # 存储记忆
            if user_id not in self.memories:
                self.memories[user_id] = []
            
            memory = {
                "memory_id": memory_id,
                "content": content,
                "embedding": embedding,
                "metadata": metadata
            }
            
            self.memories[user_id].append(memory)
            
            logger.info(f"记忆添加成功: {memory_id}")
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "content": content
            }
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def search_memory(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """搜索记忆"""
        try:
            memories = self.memories.get(user_id, [])
            if not memories:
                return []
            
            results = []
            
            if self.embedding_model:
                # 使用向量相似度搜索
                try:
                    query_embedding = self.embedding_model.encode([query])[0]
                    
                    for memory in memories:
                        if memory["embedding"] is not None:
                            # 计算余弦相似度
                            similarity = self._cosine_similarity(query_embedding, memory["embedding"])
                            results.append({
                                "memory_id": memory["memory_id"],
                                "content": memory["content"],
                                "score": float(similarity),
                                "metadata": memory["metadata"]
                            })
                    
                    # 按相似度排序
                    results.sort(key=lambda x: x["score"], reverse=True)
                    
                except Exception as e:
                    logger.warning(f"向量搜索失败，使用文本匹配: {e}")
                    results = []
            
            # 如果向量搜索失败或没有embedding模型，使用简单文本匹配
            if not results:
                for memory in memories:
                    if query.lower() in memory["content"].lower():
                        results.append({
                            "memory_id": memory["memory_id"],
                            "content": memory["content"],
                            "score": 0.8,  # 固定分数
                            "metadata": memory["metadata"]
                        })
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _cosine_similarity(self, vec1, vec2):
        """计算余弦相似度"""
        import numpy as np
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    async def delete_memory(self, memory_id: str = None, user_id: str = None) -> Dict:
        """删除记忆"""
        try:
            if user_id and user_id in self.memories:
                if memory_id:
                    # 删除特定记忆
                    self.memories[user_id] = [
                        m for m in self.memories[user_id] 
                        if m["memory_id"] != memory_id
                    ]
                else:
                    # 删除用户所有记忆
                    del self.memories[user_id]
                    
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def chat_with_memory(self, user_id: str, message: str, use_memory: bool = True) -> str:
        """带记忆的简单聊天"""
        response_templates = {
            "咖啡": "根据您的记忆，您喜欢喝咖啡，特别是拿铁。",
            "工作": "根据您的记忆，您在北京的科技公司工作。",
            "住址": "根据您的记忆，您住在北京。",
            "你好": "您好！我是您的智能助手，很高兴为您服务。",
            "谢谢": "不客气！有什么其他需要帮助的吗？"
        }
        
        context = ""
        if use_memory:
            # 搜索相关记忆
            memories = await self.search_memory(user_id, message, limit=3)
            if memories:
                context = "基于您之前的对话记忆，"
        
        # 简单的模板匹配回复
        for keyword, template in response_templates.items():
            if keyword in message:
                response = context + template
                break
        else:
            response = context + "我理解您的问题。作为本地版本，我会记住我们的对话内容。"
        
        # 保存对话记忆
        await self.add_memory(
            user_id=user_id,
            messages=[
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
        )
        
        return response

# ==========================================
# FastAPI应用
# ==========================================

memory_manager = SimpleMemoryManager()

app = FastAPI(
    title="Mem0 本地版本",
    description="支持本地中文嵌入模型的记忆系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await memory_manager.initialize()
    logger.info("Mem0本地服务启动成功")

# 安全认证（简化版）
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != os.getenv("API_SECRET_KEY", "your-secret-key-change-this"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效的API密钥")
    return token

# ==========================================
# API端点
# ==========================================

@app.get("/")
async def root():
    return {
        "service": "Mem0 本地版本",
        "version": "1.0.0",
        "status": "running",
        "embedding_model": "local" if memory_manager.embedding_model else "text_matching"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/memories/add")
async def add_memory(request: MemoryAddRequest, token: str = Depends(verify_token)):
    return await memory_manager.add_memory(
        user_id=request.user_id,
        messages=request.messages,
        metadata=request.metadata
    )

@app.post("/api/v1/memories/search")
async def search_memory(request: MemorySearchRequest, token: str = Depends(verify_token)):
    return await memory_manager.search_memory(
        user_id=request.user_id,
        query=request.query,
        limit=request.limit
    )

@app.post("/api/v1/chat")
async def chat(request: ChatRequest, token: str = Depends(verify_token)):
    response = await memory_manager.chat_with_memory(
        user_id=request.user_id,
        message=request.message,
        use_memory=request.use_memory
    )
    return {"response": response}

@app.get("/api/v1/users/{user_id}/memories")
async def get_user_memories(user_id: str, limit: int = 100, token: str = Depends(verify_token)):
    memories = memory_manager.memories.get(user_id, [])[:limit]
    formatted_memories = [
        {
            "memory_id": memory["memory_id"],
            "content": memory["content"],
            "metadata": memory["metadata"]
        }
        for memory in memories
    ]
    return {"memories": formatted_memories, "count": len(formatted_memories)}

@app.post("/api/v1/memories/delete")
async def delete_memory(request: dict, token: str = Depends(verify_token)):
    return await memory_manager.delete_memory(
        memory_id=request.get("memory_id"),
        user_id=request.get("user_id")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")