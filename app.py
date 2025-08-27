"""
Mem0 自托管服务主应用
支持国内LLM服务和本地向量数据库
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager
from loguru import logger
from dotenv import load_dotenv
import hashlib
import json

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(sys.stdout, level=os.getenv("LOG_LEVEL", "INFO"))
if os.getenv("LOG_FILE_PATH"):
    logger.add(
        os.getenv("LOG_FILE_PATH"),
        rotation=f"{os.getenv('LOG_MAX_SIZE', 100)} MB",
        retention=int(os.getenv("LOG_BACKUP_COUNT", 10)),
        level=os.getenv("LOG_LEVEL", "INFO")
    )

# ==========================================
# 数据模型
# ==========================================

class MemoryAddRequest(BaseModel):
    """添加记忆请求"""
    user_id: str = Field(..., description="用户ID")
    messages: List[Dict[str, str]] = Field(..., description="对话消息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="搜索查询")
    limit: Optional[int] = Field(default=10, description="返回数量限制")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")

class MemoryUpdateRequest(BaseModel):
    """更新记忆请求"""
    memory_id: str = Field(..., description="记忆ID")
    content: Optional[str] = Field(default=None, description="新内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="新元数据")

class MemoryDeleteRequest(BaseModel):
    """删除记忆请求"""
    memory_id: Optional[str] = Field(default=None, description="记忆ID")
    user_id: Optional[str] = Field(default=None, description="用户ID（删除所有记忆）")

class ChatRequest(BaseModel):
    """聊天请求"""
    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., description="用户消息")
    use_memory: bool = Field(default=True, description="是否使用记忆")
    stream: bool = Field(default=False, description="是否流式返回")

# ==========================================
# 记忆管理器
# ==========================================

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self):
        self.vector_db = None
        self.llm_client = None
        self.embedding_client = None
        self.initialized = False
        
    async def initialize(self):
        """初始化记忆管理器"""
        if self.initialized:
            return
            
        try:
            # 初始化向量数据库
            await self._init_vector_db()
            
            # 初始化LLM客户端
            await self._init_llm_client()
            
            # 初始化Embedding客户端
            await self._init_embedding_client()
            
            self.initialized = True
            logger.info("记忆管理器初始化成功")
            
        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")
            raise
    
    async def _init_vector_db(self):
        """初始化向量数据库"""
        vector_db_type = os.getenv("VECTOR_DB", "chroma")
        
        if vector_db_type == "chroma":
            import chromadb
            from chromadb.config import Settings
            
            settings = Settings(
                chroma_server_host=os.getenv("CHROMA_HOST", "localhost"),
                chroma_server_http_port=int(os.getenv("CHROMA_PORT", 8001)),
                anonymized_telemetry=False
            )
            
            self.vector_db = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", "localhost"),
                port=int(os.getenv("CHROMA_PORT", 8001))
            )
            
            # 创建或获取集合
            collection_name = os.getenv("CHROMA_COLLECTION", "mem0_memories")
            try:
                self.collection = self.vector_db.get_collection(collection_name)
            except:
                self.collection = self.vector_db.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                
        elif vector_db_type == "qdrant":
            from qdrant_client import QdrantClient
            
            self.vector_db = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", 6333)),
                api_key=os.getenv("QDRANT_API_KEY")
            )
            
        elif vector_db_type == "faiss":
            import faiss
            import numpy as np
            
            # 初始化FAISS索引
            dimension = 1536  # 默认embedding维度
            self.vector_db = faiss.IndexFlatL2(dimension)
            self.faiss_metadata = {}  # 存储元数据
            
        logger.info(f"向量数据库初始化成功: {vector_db_type}")
    
    async def _init_llm_client(self):
        """初始化LLM客户端"""
        llm_provider = os.getenv("LLM_PROVIDER", "dashscope")
        
        if llm_provider == "dashscope":
            # 阿里云通义千问
            from dashscope import Generation
            self.llm_client = Generation
            self.llm_model = os.getenv("DASHSCOPE_MODEL", "qwen-max")
            
        elif llm_provider == "qianfan":
            # 百度文心一言
            import qianfan
            qianfan.AK(os.getenv("QIANFAN_AK"))
            qianfan.SK(os.getenv("QIANFAN_SK"))
            self.llm_client = qianfan.ChatCompletion()
            self.llm_model = os.getenv("QIANFAN_MODEL", "ERNIE-Bot-4")
            
        elif llm_provider == "zhipu":
            # 智谱AI
            from zhipuai import ZhipuAI
            self.llm_client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
            self.llm_model = os.getenv("ZHIPUAI_MODEL", "glm-4")
            
        elif llm_provider == "deepseek":
            # DeepSeek
            from openai import OpenAI
            self.llm_client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
            self.llm_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            
        elif llm_provider == "moonshot":
            # Moonshot AI
            from openai import OpenAI
            self.llm_client = OpenAI(
                api_key=os.getenv("MOONSHOT_API_KEY"),
                base_url="https://api.moonshot.cn/v1"
            )
            self.llm_model = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
            
        logger.info(f"LLM客户端初始化成功: {llm_provider}")
    
    async def _init_embedding_client(self):
        """初始化Embedding客户端"""
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "dashscope")
        
        if embedding_provider == "dashscope":
            # 阿里云通义千问 Embedding
            from dashscope import TextEmbedding
            self.embedding_client = TextEmbedding
            self.embedding_model = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3")
            
        elif embedding_provider == "qianfan":
            # 百度文心 Embedding
            import qianfan
            self.embedding_client = qianfan.Embedding()
            self.embedding_model = os.getenv("QIANFAN_EMBEDDING_MODEL", "Embedding-V1")
            
        elif embedding_provider == "zhipu":
            # 智谱AI Embedding
            from zhipuai import ZhipuAI
            self.embedding_client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
            self.embedding_model = os.getenv("ZHIPUAI_EMBEDDING_MODEL", "embedding-3")
            
        elif embedding_provider == "local_huggingface":
            # HuggingFace 本地模型
            from sentence_transformers import SentenceTransformer
            self.embedding_model = os.getenv("HF_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
            self.embedding_client = SentenceTransformer(self.embedding_model)
            
        elif embedding_provider == "sentence_transformers":
            # Sentence Transformers 本地模型
            from sentence_transformers import SentenceTransformer
            self.embedding_model = os.getenv("ST_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
            self.embedding_client = SentenceTransformer(self.embedding_model)
            
        elif embedding_provider == "local_openai":
            # 本地OpenAI兼容API (如Ollama)
            from openai import OpenAI
            self.embedding_client = OpenAI(
                base_url=os.getenv("LOCAL_EMBEDDING_URL", "http://localhost:11434/v1"),
                api_key="local"  # 本地不需要真实密钥
            )
            self.embedding_model = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")
            
        logger.info(f"Embedding客户端初始化成功: {embedding_provider}")
    
    async def add_memory(self, user_id: str, messages: List[Dict], metadata: Dict = None) -> Dict:
        """添加记忆"""
        try:
            # 从对话中提取记忆
            memory_content = await self._extract_memory(messages)
            
            if not memory_content:
                return {"status": "skipped", "message": "没有需要记忆的内容"}
            
            # 生成embedding
            embedding = await self._generate_embedding(memory_content)
            
            # 生成记忆ID
            memory_id = hashlib.md5(
                f"{user_id}_{memory_content}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            
            # 准备元数据
            metadata = metadata or {}
            metadata.update({
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "content": memory_content
            })
            
            # 存储到向量数据库
            if os.getenv("VECTOR_DB") == "chroma":
                self.collection.add(
                    ids=[memory_id],
                    embeddings=[embedding],
                    metadatas=[metadata]
                )
            
            logger.info(f"记忆添加成功: {memory_id}")
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "content": memory_content
            }
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def search_memory(self, user_id: str, query: str, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """搜索记忆"""
        try:
            # 生成查询的embedding
            query_embedding = await self._generate_embedding(query)
            
            # 从向量数据库搜索
            if os.getenv("VECTOR_DB") == "chroma":
                # 构建查询条件
                where = {"user_id": user_id}
                if filters:
                    where.update(filters)
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where
                )
                
                # 格式化结果
                memories = []
                if results["metadatas"]:
                    for i, metadata in enumerate(results["metadatas"][0]):
                        memories.append({
                            "memory_id": results["ids"][0][i],
                            "content": metadata.get("content", ""),
                            "score": 1 - results["distances"][0][i] if results["distances"] else 0,
                            "metadata": metadata
                        })
            
            logger.info(f"搜索记忆成功，找到 {len(memories)} 条记录")
            
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_memory(self, memory_id: str, content: str = None, metadata: Dict = None) -> Dict:
        """更新记忆"""
        try:
            # 如果有新内容，重新生成embedding
            if content:
                embedding = await self._generate_embedding(content)
                
                if os.getenv("VECTOR_DB") == "chroma":
                    # 获取原有的元数据
                    result = self.collection.get(ids=[memory_id])
                    if not result["ids"]:
                        raise HTTPException(status_code=404, detail="记忆不存在")
                    
                    old_metadata = result["metadatas"][0]
                    
                    # 更新元数据
                    new_metadata = old_metadata.copy()
                    new_metadata["content"] = content
                    new_metadata["updated_at"] = datetime.utcnow().isoformat()
                    if metadata:
                        new_metadata.update(metadata)
                    
                    # 删除旧的，添加新的
                    self.collection.delete(ids=[memory_id])
                    self.collection.add(
                        ids=[memory_id],
                        embeddings=[embedding],
                        metadatas=[new_metadata]
                    )
            
            logger.info(f"记忆更新成功: {memory_id}")
            
            return {"status": "success", "memory_id": memory_id}
            
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_memory(self, memory_id: str = None, user_id: str = None) -> Dict:
        """删除记忆"""
        try:
            if os.getenv("VECTOR_DB") == "chroma":
                if memory_id:
                    # 删除特定记忆
                    self.collection.delete(ids=[memory_id])
                    logger.info(f"记忆删除成功: {memory_id}")
                elif user_id:
                    # 删除用户的所有记忆
                    self.collection.delete(where={"user_id": user_id})
                    logger.info(f"用户 {user_id} 的所有记忆删除成功")
                else:
                    raise HTTPException(status_code=400, detail="必须提供 memory_id 或 user_id")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _extract_memory(self, messages: List[Dict]) -> str:
        """从对话中提取记忆"""
        # 构建提取记忆的prompt
        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        prompt = f"""
        请从以下对话中提取重要的信息作为长期记忆。
        只提取关键信息，如用户偏好、重要事实、个人信息等。
        如果没有值得记忆的内容，返回空字符串。
        
        对话：
        {conversation}
        
        提取的记忆（中文）：
        """
        
        # 调用LLM提取记忆
        memory = await self._call_llm(prompt)
        
        return memory.strip()
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本的embedding"""
        provider = os.getenv("EMBEDDING_PROVIDER", "dashscope")
        
        if provider == "dashscope":
            from dashscope import TextEmbedding
            
            response = TextEmbedding.call(
                model=self.embedding_model,
                input=text,
                api_key=os.getenv("DASHSCOPE_API_KEY")
            )
            
            if response.status_code == 200:
                return response.output["embeddings"][0]["embedding"]
            else:
                raise Exception(f"Embedding生成失败: {response}")
                
        elif provider == "qianfan":
            # 百度文心 Embedding
            response = self.embedding_client.do(model=self.embedding_model, texts=[text])
            return response["body"]["data"][0]["embedding"]
            
        elif provider == "zhipu":
            # 智谱AI Embedding
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
            
        elif provider in ["local_huggingface", "sentence_transformers"]:
            # 本地 Sentence Transformers 模型
            embeddings = self.embedding_client.encode([text], convert_to_tensor=False)
            return embeddings[0].tolist()
            
        elif provider == "local_openai":
            # 本地 OpenAI 兼容 API
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        
        return []
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        provider = os.getenv("LLM_PROVIDER", "dashscope")
        
        if provider == "dashscope":
            from dashscope import Generation
            
            response = Generation.call(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=os.getenv("DASHSCOPE_API_KEY")
            )
            
            if response.status_code == 200:
                return response.output.text
            else:
                raise Exception(f"LLM调用失败: {response}")
                
        elif provider == "deepseek" or provider == "moonshot":
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
            
        # 其他provider的实现...
        
        return ""
    
    async def chat_with_memory(self, user_id: str, message: str, use_memory: bool = True) -> str:
        """带记忆的聊天"""
        try:
            context = ""
            
            if use_memory:
                # 搜索相关记忆
                memories = await self.search_memory(user_id, message, limit=5)
                
                if memories:
                    context = "相关记忆：\n"
                    for memory in memories:
                        context += f"- {memory['content']}\n"
                    context += "\n"
            
            # 构建prompt
            prompt = f"""{context}用户: {message}
            
            请基于上述记忆（如果有）回答用户的问题。使用中文回答。
            
            助手："""
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 保存新的对话记忆
            await self.add_memory(
                user_id=user_id,
                messages=[
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response}
                ]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"聊天失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# FastAPI应用
# ==========================================

# 创建记忆管理器实例
memory_manager = MemoryManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await memory_manager.initialize()
    logger.info("Mem0服务启动成功")
    yield
    # 关闭时清理
    logger.info("Mem0服务正在关闭")

# 创建FastAPI应用
app = FastAPI(
    title="Mem0 自托管服务",
    description="支持国内LLM服务的智能记忆系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("CORS_ORIGINS", '["*"]')),
    allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
    allow_methods=json.loads(os.getenv("CORS_ALLOW_METHODS", '["*"]')),
    allow_headers=json.loads(os.getenv("CORS_ALLOW_HEADERS", '["*"]')),
)

# 安全认证
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证API密钥"""
    token = credentials.credentials
    if token != os.getenv("API_SECRET_KEY", "your-secret-key-change-this"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的API密钥"
        )
    return token

# ==========================================
# API端点
# ==========================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Mem0 自托管服务",
        "version": "1.0.0",
        "status": "running",
        "llm_provider": os.getenv("LLM_PROVIDER", "dashscope"),
        "vector_db": os.getenv("VECTOR_DB", "chroma")
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/memories/add")
async def add_memory(
    request: MemoryAddRequest,
    token: str = Depends(verify_token)
):
    """添加记忆"""
    return await memory_manager.add_memory(
        user_id=request.user_id,
        messages=request.messages,
        metadata=request.metadata
    )

@app.post("/api/v1/memories/search")
async def search_memory(
    request: MemorySearchRequest,
    token: str = Depends(verify_token)
):
    """搜索记忆"""
    return await memory_manager.search_memory(
        user_id=request.user_id,
        query=request.query,
        limit=request.limit,
        filters=request.filters
    )

@app.post("/api/v1/memories/update")
async def update_memory(
    request: MemoryUpdateRequest,
    token: str = Depends(verify_token)
):
    """更新记忆"""
    return await memory_manager.update_memory(
        memory_id=request.memory_id,
        content=request.content,
        metadata=request.metadata
    )

@app.post("/api/v1/memories/delete")
async def delete_memory(
    request: MemoryDeleteRequest,
    token: str = Depends(verify_token)
):
    """删除记忆"""
    return await memory_manager.delete_memory(
        memory_id=request.memory_id,
        user_id=request.user_id
    )

@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    token: str = Depends(verify_token)
):
    """带记忆的聊天"""
    response = await memory_manager.chat_with_memory(
        user_id=request.user_id,
        message=request.message,
        use_memory=request.use_memory
    )
    
    return {"response": response}

@app.get("/api/v1/users/{user_id}/memories")
async def get_user_memories(
    user_id: str,
    limit: int = 100,
    token: str = Depends(verify_token)
):
    """获取用户的所有记忆"""
    memories = await memory_manager.search_memory(
        user_id=user_id,
        query="",  # 空查询返回所有
        limit=limit
    )
    
    return {"memories": memories, "count": len(memories)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=os.getenv("DEBUG_MODE", "false").lower() == "true"
    )