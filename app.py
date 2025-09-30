"""
Mem0 自托管服务主应用
支持国内LLM服务和本地向量数据库
"""

# 首先修复SQLite版本问题（ChromaDB需要）
import sys
try:
    import sqlite3
    if sqlite3.sqlite_version < "3.35.0":
        try:
            import pysqlite3.dbapi2 as sqlite3
            sys.modules['sqlite3'] = sqlite3
            print(f"✅ 使用pysqlite3-binary，SQLite版本: {sqlite3.sqlite_version}")
        except ImportError:
            print(f"⚠️ SQLite版本过低 ({sqlite3.sqlite_version})，ChromaDB可能无法工作")
except Exception as e:
    print(f"⚠️ SQLite检查失败: {e}")

from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import os
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager
from loguru import logger
from dotenv import load_dotenv
import hashlib
import json
from mysql_handler import MySQLHandler

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.add(sys.stdout, level=log_level)
if os.getenv("LOG_FILE_PATH"):
    logger.add(
        os.getenv("LOG_FILE_PATH"),
        rotation=f"{os.getenv('LOG_MAX_SIZE', 100)} MB",
        retention=int(os.getenv("LOG_BACKUP_COUNT", 10)),
        level=log_level
    )

# ==========================================
# 数据模型
# ==========================================

class MessageItem(BaseModel):
    """单条消息"""
    user_id: Union[str, int] = Field(..., description="用户ID", example=1)
    content: str = Field(..., description="消息内容", example="今天可太热了")
    role: str = Field(..., description="角色: user/assistant", example="user")
    session_id: Optional[Union[str, int]] = Field(None, description="会话ID", example=123456)
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "user_id": 1,
                    "content": "今天可太热了",
                    "role": "user"
                },
                {
                    "user_id": 2,
                    "content": "是啊 都快40度了吧",
                    "role": "user"
                },
                {
                    "user_id": 3,
                    "content": "北京今天的最高温度是34度哦",
                    "role": "assistant"
                }
            ]
        }

class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    user_id: Optional[str] = Field(default=None, description="用户ID（可选，不传时搜索所有用户）")
    query: str = Field(..., description="搜索查询")
    limit: Optional[int] = Field(default=10, description="返回数量限制")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")

class MemoryUpdateRequest(BaseModel):
    """更新记忆请求"""
    memory_id: str = Field(..., description="记忆ID")
    content: Optional[str] = Field(default=None, description="新内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="新元数据")
    session_id: Optional[int] = Field(default=None, description="会话ID")

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
        self.mysql_handler = MySQLHandler()
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
            
            # 初始化MySQL处理器（可选）
            if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                await self.mysql_handler.initialize()
                logger.info("MySQL处理器已启用")
            else:
                logger.info("MySQL处理器已禁用")
            
            self.initialized = True
            logger.info("记忆管理器初始化成功")
            
        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")
            raise
    
    async def _init_vector_db(self):
        """初始化向量数据库"""
        vector_db_type = os.getenv("MEM0_VECTOR_STORE_PROVIDER", "qdrant")
        
        if vector_db_type == "qdrant":
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # 检查是否连接到远程服务器还是使用本地
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
            
            # 优先使用本地文件存储（持久化）
            qdrant_path = os.getenv("QDRANT_PATH", "./data/qdrant")
            
            if qdrant_host == "localhost" and not self._check_qdrant_server():
                # 使用本地文件存储（持久化）
                os.makedirs(qdrant_path, exist_ok=True)
                self.vector_db = QdrantClient(path=qdrant_path)
                logger.info(f"使用 Qdrant 本地持久化存储: {qdrant_path}")
            else:
                # 连接到服务器
                self.vector_db = QdrantClient(
                    host=qdrant_host,
                    port=qdrant_port
                )
                logger.info(f"连接到 Qdrant 服务器: {qdrant_host}:{qdrant_port}")
            
            # 集合配置
            collection_name = os.getenv("QDRANT_COLLECTION", "mem0_memories")
            dimension = 1024  # bge-large-zh-v1.5 模型维度
            
            # 检查集合是否存在
            try:
                collection_info = self.vector_db.get_collection(collection_name)
                logger.info(f"使用现有 Qdrant 集合: {collection_name}")
            except Exception:
                # 创建集合
                self.vector_db.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
                )
                logger.info(f"创建新 Qdrant 集合: {collection_name}")
            
            # 存储集合名称
            self.collection_name = collection_name
            self.vector_db_type = "qdrant"
            
        elif vector_db_type == "chroma":
            import chromadb
            from chromadb.config import Settings
            
            # ChromaDB 配置
            persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
            os.makedirs(persist_directory, exist_ok=True)
            
            # 创建 ChromaDB 客户端（持久化模式）
            self.vector_db = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"使用 ChromaDB 本地持久化存储: {persist_directory}")
            
            # 集合配置
            collection_name = os.getenv("CHROMA_COLLECTION", "mem0_memories")
            
            # 获取或创建集合
            try:
                self.collection = self.vector_db.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"使用 ChromaDB 集合: {collection_name}")
            except Exception as e:
                logger.error(f"创建 ChromaDB 集合失败: {e}")
                raise
            
            # 存储集合名称
            self.collection_name = collection_name
            self.vector_db_type = "chroma"
            
        else:
            raise ValueError(f"不支持的向量数据库类型: {vector_db_type}")
            
        logger.info(f"向量数据库初始化成功: {vector_db_type}")
    
    def _check_qdrant_server(self):
        """检查Qdrant服务器是否可用"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 6333))
            sock.close()
            return result == 0
        except:
            return False
    
    async def _init_llm_client(self):
        """初始化LLM客户端"""
        llm_provider = os.getenv("MEM0_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "dashscope"))
        
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
            
        elif llm_provider == "doubao":
            # 豆包/火山引擎 API
            from openai import OpenAI
            self.llm_client = OpenAI(
                api_key=os.getenv("DOUBAO_API_KEY", os.getenv("ARK_API_KEY")),
                base_url=os.getenv("DOUBAO_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
            )
            self.llm_model = os.getenv("MEM0_LLM_MODEL", "doubao-pro-32k")
            
        logger.info(f"LLM客户端初始化成功: {llm_provider}")
    
    async def _init_embedding_client(self):
        """初始化本地Embedding客户端"""
        logger.info("开始初始化本地Embedding客户端")
        
        # 只支持本地SentenceTransformers模型
        from sentence_transformers import SentenceTransformer
        
        # 获取模型名称
        self.embedding_model = os.getenv("MEM0_EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        
        # 候选模型列表（按优先级排序）
        candidate_models = [
            self.embedding_model,  # 用户指定的模型
            "shibing624/text2vec-base-chinese",  # 中文模型
            "paraphrase-multilingual-MiniLM-L12-v2",  # 多语言模型
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 完整路径
            "all-MiniLM-L6-v2",  # 更小的模型
        ]
        
        # 设置缓存目录
        cache_dir = os.getenv("HF_HOME", "./data/huggingface") 
        os.makedirs(cache_dir, exist_ok=True)
        
        # 尝试加载模型
        model_loaded = False
        for model_name in candidate_models:
            try:
                logger.info(f"尝试加载模型: {model_name}")
                
                # 先尝试离线模式加载
                try:
                    self.embedding_client = SentenceTransformer(
                        model_name, 
                        cache_folder=cache_dir,
                        device='cpu',
                        local_files_only=True  # 强制使用本地文件
                    )
                    self.embedding_model = model_name
                    logger.info(f"✅ 离线模式成功加载模型: {model_name}")
                    model_loaded = True
                    break
                except Exception as e1:
                    logger.debug(f"离线模式失败 {model_name}: {e1}")
                    
                    # 如果离线失败，尝试在线模式（仅对简单模型名）
                    if "/" not in model_name or model_name.startswith("sentence-transformers/"):
                        try:
                            self.embedding_client = SentenceTransformer(
                                model_name, 
                                cache_folder=cache_dir,
                                device='cpu'
                            )
                            self.embedding_model = model_name
                            logger.info(f"✅ 在线模式成功加载模型: {model_name}")
                            model_loaded = True
                            break
                        except Exception as e2:
                            logger.debug(f"在线模式也失败 {model_name}: {e2}")
                            continue
                    
            except Exception as e:
                logger.debug(f"加载模型失败 {model_name}: {e}")
                continue
        
        if not model_loaded:
            # 如果所有模型都无法加载，直接抛出异常
            error_msg = f"❌ 无法加载任何嵌入模型，尝试的模型: {candidate_models}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"本地Embedding客户端初始化完成: {self.embedding_model}")
    
    async def add_memory(self, messages: List[MessageItem], metadata: Dict = None) -> Dict:
        """为每个用户单独添加记忆"""
        try:
            # 收集所有用户和对话内容
            user_messages = {}  # 每个用户说的话
            user_session_ids = {}  # 每个用户的session_id
            all_conversation = []  # 完整对话记录
            user_ids = set()  # 所有参与者ID
            
            for message in messages:
                # 转换user_id为字符串
                user_id_str = str(message.user_id)
                
                # 记录完整对话
                all_conversation.append({
                    "user_id": user_id_str,
                    "role": message.role,
                    "content": message.content
                })
                
                # 只为role=user的用户生成记忆
                if message.role == "user":
                    if user_id_str not in user_messages:
                        user_messages[user_id_str] = []
                        user_ids.add(user_id_str)
                        # 记录该用户的session_id
                        if message.session_id:
                            user_session_ids[user_id_str] = message.session_id
                    user_messages[user_id_str].append(message.content)
            
            if not user_messages:
                logger.info("没有找到需要记忆的用户消息")
                return {"status": "no_memory", "message": "没有用户消息需要记忆"}
            
            results = []
            
            # 为每个用户生成记忆
            for user_id, contents in user_messages.items():
                try:
                    # 获取该用户的历史记忆内容（用于上下文）
                    historical_content = await self._get_user_historical_content(user_id)
                    
                    # 生成该用户的记忆总结（传入完整对话上下文）
                    memory_dimensions = await self._generate_memory_summary(
                        user_id=user_id,
                        user_messages=contents,
                        all_conversation=all_conversation,
                        historical_content=historical_content
                    )
                    
                    if not memory_dimensions or not any(memory_dimensions.values()):
                        logger.info(f"用户 {user_id} 没有需要记忆的内容")
                        continue
                    
                    # 组合所有有效维度形成完整记忆内容
                    memory_parts = []
                    if memory_dimensions.get('event'):
                        memory_parts.append(memory_dimensions['event'])
                    if memory_dimensions.get('preference'):
                        memory_parts.append(memory_dimensions['preference'])
                    if memory_dimensions.get('knowledge'):
                        memory_parts.append(memory_dimensions['knowledge'])
                    if memory_dimensions.get('skill'):
                        memory_parts.append(memory_dimensions['skill'])
                    if memory_dimensions.get('time'):
                        memory_parts.append(memory_dimensions['time'])
                    
                    memory_content = '，'.join(memory_parts)
                    
                    if not memory_content:
                        logger.info(f"用户 {user_id} 没有需要记忆的内容")
                        continue
                    
                    # 生成向量嵌入
                    embedding = await self._generate_embedding(memory_content)
                    
                    # 生成记忆ID
                    memory_id = hashlib.md5(
                        f"{user_id}_{memory_content}_{datetime.utcnow().isoformat()}".encode()
                    ).hexdigest()
                    
                    # 准备元数据 - 存储原始的messages数据
                    metadata_to_store = {
                        "original_messages": [
                            {
                                "user_id": str(msg.user_id),
                                "content": msg.content,
                                "role": msg.role,
                                "session_id": msg.session_id
                            } for msg in messages
                        ]
                    }
                    # 如果用户传入了metadata参数，也保存
                    if metadata:
                        metadata_to_store.update(metadata)
                    
                    # 存储到向量数据库
                    if hasattr(self, 'vector_db_type') and self.vector_db_type == "chroma":
                        # ChromaDB 存储
                        self.collection.add(
                            ids=[memory_id],
                            embeddings=[embedding],
                            metadatas=[{
                                "user_id": user_id,
                                "content": memory_content,
                                "created_at": datetime.utcnow().isoformat(),
                                "session_id": user_session_ids.get(user_id, "")
                            }],
                            documents=[memory_content]
                        )
                    else:
                        # Qdrant 存储
                        from qdrant_client.models import PointStruct
                        
                        point = PointStruct(
                            id=memory_id,
                            vector=embedding,
                            payload={
                                "user_id": user_id,
                                "content": memory_content,
                                "created_at": datetime.utcnow().isoformat(),
                                "session_id": user_session_ids.get(user_id, "")
                            }
                        )
                        self.vector_db.upsert(
                            collection_name=self.collection_name,
                            points=[point]
                        )
                    
                    # 同时存储到MySQL数据库（如果启用）
                    if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                        try:
                            # 获取该用户的session_id
                            session_id = user_session_ids.get(user_id)
                            await self.mysql_handler.insert_memory(
                                memory_id=memory_id,
                                user_id=user_id,
                                content=memory_content,
                                event=memory_dimensions.get('event'),
                                time=memory_dimensions.get('time'),
                                knowledge=memory_dimensions.get('knowledge'),
                                skill=memory_dimensions.get('skill'),
                                preference=memory_dimensions.get('preference'),
                                metadata=metadata_to_store,
                                session_id=session_id
                            )
                            logger.info(f"用户 {user_id} 记忆已同步到MySQL: {memory_id}")
                        except Exception as e:
                            logger.error(f"用户 {user_id} 同步记忆到MySQL失败，但向量数据库已保存: {e}")
                    
                    results.append({
                        "user_id": user_id,
                        "memory_id": memory_id,
                        "status": "success",
                        "content": memory_content,
                        "session_id": user_session_ids.get(user_id)
                    })
                    
                    logger.info(f"用户 {user_id} 记忆添加成功: {memory_id}")
                    
                except Exception as e:
                    logger.error(f"为用户 {user_id} 添加记忆失败: {e}")
                    results.append({
                        "user_id": user_id,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def search_memory(self, user_id: str = None, query: str = None, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """搜索记忆 - user_id可选，不传时搜索所有用户的记忆"""
        try:
            # 生成查询的embedding
            query_embedding = await self._generate_embedding(query)
            
            # 从向量数据库搜索
            memories = []
            
            if hasattr(self, 'vector_db_type') and self.vector_db_type == "chroma":
                # ChromaDB 搜索
                where_clause = {}
                if user_id:
                    where_clause["user_id"] = user_id
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where_clause if where_clause else None
                )
                
                if results and results['ids'] and len(results['ids'][0]) > 0:
                    for i in range(len(results['ids'][0])):
                        memories.append({
                            "id": results['ids'][0][i],
                            "content": results['metadatas'][0][i].get('content', ''),
                            "user_id": results['metadatas'][0][i].get('user_id', ''),
                            "created_at": results['metadatas'][0][i].get('created_at', ''),
                            "session_id": results['metadatas'][0][i].get('session_id', ''),
                            "score": 1 - results['distances'][0][i] if results['distances'] else 0
                        })
            else:
                # Qdrant 搜索
                from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            filter_conditions = []
            
            # 只有当user_id不为空时才添加user_id过滤条件
            if user_id:
                filter_conditions.append(
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                )
            
            if filters:
                for key, value in filters.items():
                    if key != "user_id":
                        filter_conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
            
            # 执行搜索
            if filter_conditions:
                # 有过滤条件时使用过滤器
                search_result = self.vector_db.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    query_filter=Filter(must=filter_conditions),
                    limit=limit,
                    with_payload=True
                )
            else:
                # 没有过滤条件时不使用过滤器
                search_result = self.vector_db.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    with_payload=True
                )
            
            # 格式化结果
            for point in search_result:
                memories.append({
                    "memory_id": point.id,
                    "content": point.payload.get("content", ""),
                    "score": point.score,
                    "metadata": {
                        "user_id": point.payload.get("user_id", ""),
                        "created_at": point.payload.get("created_at", ""),
                        "session_id": point.payload.get("session_id", "")
                    }
                })
            
            logger.info(f"搜索记忆成功，找到 {len(memories)} 条记录")
            
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_memory(self, memory_id: str, content: str = None, metadata: Dict = None,
                           event: str = None, knowledge: str = None, skill: str = None, 
                           session_id: int = None) -> Dict:
        """更新记忆"""
        try:
            # 如果有新内容，重新生成embedding
            if content:
                embedding = await self._generate_embedding(content)
                
                vector_db_type = getattr(self, 'vector_db_type', os.getenv("MEM0_VECTOR_STORE_PROVIDER", "qdrant"))
                if vector_db_type == "chroma":
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
                elif vector_db_type == "qdrant":
                    from qdrant_client.models import PointStruct
                    
                    # 获取原有的点数据
                    search_result = self.vector_db.retrieve(
                        collection_name=self.collection_name,
                        ids=[memory_id]
                    )
                    
                    if not search_result:
                        raise HTTPException(status_code=404, detail="记忆不存在")
                    
                    old_payload = search_result[0].payload
                    
                    # 更新payload
                    new_payload = old_payload.copy()
                    new_payload["content"] = content
                    new_payload["updated_at"] = datetime.utcnow().isoformat()
                    if metadata:
                        new_payload.update(metadata)
                    
                    # 更新点
                    self.vector_db.upsert(
                        collection_name=self.collection_name,
                        points=[PointStruct(
                            id=memory_id,
                            vector=embedding,
                            payload=new_payload
                        )]
                    )
            
            # 同时更新MySQL数据库（如果启用）
            if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                try:
                    await self.mysql_handler.update_memory(
                        memory_id=memory_id,
                        content=content,
                        metadata=metadata,
                        session_id=session_id
                    )
                    logger.info(f"MySQL记忆已同步更新: {memory_id}")
                except Exception as e:
                    logger.error(f"同步更新MySQL记忆失败，但向量数据库已更新: {e}")
            
            logger.info(f"记忆更新成功: {memory_id}")
            
            return {"status": "success", "memory_id": memory_id}
            
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_memory(self, memory_id: str = None, user_id: str = None) -> Dict:
        """删除记忆"""
        try:
            vector_db_type = getattr(self, 'vector_db_type', os.getenv("MEM0_VECTOR_STORE_PROVIDER", "qdrant"))
            if vector_db_type == "chroma":
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
            elif vector_db_type == "qdrant":
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                if memory_id:
                    # 删除特定记忆
                    self.vector_db.delete(
                        collection_name=self.collection_name,
                        points_selector=[memory_id]
                    )
                    logger.info(f"记忆删除成功: {memory_id}")
                elif user_id:
                    # 删除用户的所有记忆
                    self.vector_db.delete(
                        collection_name=self.collection_name,
                        points_selector=Filter(
                            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                        )
                    )
                    logger.info(f"用户 {user_id} 的所有记忆删除成功")
                else:
                    raise HTTPException(status_code=400, detail="必须提供 memory_id 或 user_id")
            elif vector_db_type == "milvus":
                if memory_id:
                    # 删除特定记忆
                    delete_expr = f'id == "{memory_id}"'
                    self.vector_db.delete(
                        collection_name=self.collection_name,
                        filter=delete_expr
                    )
                    logger.info(f"记忆删除成功: {memory_id}")
                elif user_id:
                    # 删除用户的所有记忆
                    delete_expr = f'user_id == "{user_id}"'
                    self.vector_db.delete(
                        collection_name=self.collection_name,
                        filter=delete_expr
                    )
                    logger.info(f"用户 {user_id} 的所有记忆删除成功")
                else:
                    raise HTTPException(status_code=400, detail="必须提供 memory_id 或 user_id")
            
            # 同时从MySQL删除（如果启用）
            if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                try:
                    await self.mysql_handler.delete_memory(
                        memory_id=memory_id,
                        user_id=user_id
                    )
                    logger.info(f"MySQL记忆已同步删除")
                except Exception as e:
                    logger.error(f"从MySQL删除记忆失败，但向量数据库已删除: {e}")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def clear_all_data(self) -> Dict:
        """清除所有数据（向量数据库和MySQL）"""
        try:
            results = {
                "vector_db": {"status": "skipped"},
                "mysql": {"status": "skipped"}
            }
            
            # 清除向量数据库
            try:
                vector_db_type = getattr(self, 'vector_db_type', os.getenv("MEM0_VECTOR_STORE_PROVIDER", "qdrant"))
                collection_name = self.collection_name
                
                if vector_db_type == "chroma":
                    # ChromaDB 清除
                    # 获取所有数据进行计数
                    all_data = self.collection.get()
                    count_before = len(all_data["ids"]) if all_data["ids"] else 0
                    
                    if count_before > 0:
                        # 删除所有数据
                        self.collection.delete(ids=all_data["ids"])
                    
                    logger.info(f"ChromaDB 向量数据库清除成功: 删除了 {count_before} 条记录")
                    results["vector_db"] = {
                        "status": "success",
                        "deleted_count": count_before
                    }
                elif vector_db_type == "qdrant":
                    # Qdrant 清除
                    # 获取数据数量（用于统计）
                    collection_info = self.vector_db.get_collection(collection_name)
                    count_before = collection_info.points_count if collection_info else 0
                    
                    if count_before > 0:
                        # 删除集合中的所有数据
                        self.vector_db.delete_collection(collection_name)
                        
                        # 重新创建集合
                        from qdrant_client.models import Distance, VectorParams
                        self.vector_db.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                        )
                    
                    
                    logger.info(f"Qdrant 向量数据库清除成功: 删除了 {count_before} 条记录")
                    results["vector_db"] = {
                        "status": "success",
                        "deleted_count": count_before
                    }
            except Exception as e:
                logger.error(f"清除向量数据库失败: {e}")
                results["vector_db"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # 清除MySQL数据库
            if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                try:
                    # 清除MySQL中的所有记忆
                    deleted_count = await self.mysql_handler.clear_all_memories()
                    logger.info(f"MySQL数据库清除成功: 删除了 {deleted_count} 条记录")
                    results["mysql"] = {
                        "status": "success",
                        "deleted_count": deleted_count
                    }
                except Exception as e:
                    logger.error(f"清除MySQL数据库失败: {e}")
                    results["mysql"] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"清除所有数据失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _extract_memory(self, messages: List[Dict]) -> Dict[str, str]:
        """从对话中提取记忆，返回5个维度的结构化信息"""
        # 构建提取记忆的prompt
        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        prompt = f"""
请从以下对话中为当前用户提取记忆，按以下5个维度分析：

1. 事件：当前用户发生了什么具体事情
2. 时间：与当前用户相关的时间信息  
3. 技能：当前用户展示的技能或能力
4. 知识：当前用户分享的知识或专业信息
5. 偏好：当前用户表达的喜好或倾向

重要要求：
- 只提取当前用户自己说的话中的事实，不要混淆其他用户的行为
- 如果当前用户只是询问或评论其他用户的行为，请明确区分："用户询问了其他用户关于X的情况"
- 如果是推测的信息，必须使用"用户可能"或"用户也许"等表述
- 每个维度最多一句话，简洁准确
- 没有相关信息的维度输出"无"
- 用中文回答

对话记录（role=user为当前用户，role=context为其他用户的消息）：
{conversation}

请按照以下格式输出：
事件：[当前用户的事件信息或"无"]
时间：[时间信息或"无"] 
技能：[技能信息或"无"]
知识：[知识信息或"无"]
偏好：[偏好信息或"无"]
        """
        
        # 调用LLM提取记忆
        memory_response = await self._call_llm(prompt)
        
        # 解析LLM响应，提取各个维度
        dimensions = {
            'event': None,
            'time': None,
            'skill': None,
            'knowledge': None,
            'preference': None
        }
        
        lines = memory_response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('事件：'):
                value = line.replace('事件：', '').strip()
                if value and value != '无':
                    dimensions['event'] = value
            elif line.startswith('时间：'):
                value = line.replace('时间：', '').strip()
                if value and value != '无':
                    dimensions['time'] = value
            elif line.startswith('技能：'):
                value = line.replace('技能：', '').strip()
                if value and value != '无':
                    dimensions['skill'] = value
            elif line.startswith('知识：'):
                value = line.replace('知识：', '').strip()
                if value and value != '无':
                    dimensions['knowledge'] = value
            elif line.startswith('偏好：'):
                value = line.replace('偏好：', '').strip()
                if value and value != '无':
                    dimensions['preference'] = value
        
        return dimensions
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """使用本地模型生成文本的embedding"""
        try:
            # 使用本地 SentenceTransformers 模型
            embeddings = self.embedding_client.encode([text], convert_to_tensor=False)
            return embeddings[0].tolist()
        except Exception as e:
            logger.error(f"生成embedding失败: {e}")
            raise RuntimeError(f"无法生成embedding: {e}")
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        provider = os.getenv("MEM0_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "dashscope"))
        
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
                
        elif provider == "deepseek" or provider == "moonshot" or provider == "doubao":
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
    
    async def _get_user_historical_content(self, user_id: str) -> List[str]:
        """获取用户的历史记忆内容"""
        try:
            if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                # 从MySQL获取最近的记忆
                memories = await self.mysql_handler.get_user_memories(user_id, limit=20)
                return [memory.get('content', '') for memory in memories if memory.get('content')]
            else:
                # 从向量数据库获取
                results = self.collection.get(
                    where={"user_id": user_id},
                    limit=20,
                    include=['metadatas']
                )
                return [meta.get('content', '') for meta in results.get('metadatas', []) if meta.get('content')]
        except Exception as e:
            logger.error(f"获取用户 {user_id} 历史内容失败: {e}")
            return []
    
    async def _generate_memory_summary(self, user_id: str, user_messages: List[str], 
                                     all_conversation: List[Dict], historical_content: List[str]) -> Dict[str, str]:
        """从5个维度生成记忆总结，返回结构化数据"""
        try:
            # 为当前用户创建单独的对话记录用于记忆提取
            user_specific_conversation = []
            for msg in all_conversation:
                if msg["user_id"] == user_id:
                    # 只包含该用户自己的消息
                    user_specific_conversation.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                else:
                    # 其他用户的消息作为上下文，但标明是其他用户说的
                    user_specific_conversation.append({
                        "role": "context",
                        "content": f"其他用户(ID:{msg['user_id']})说: {msg['content']}"
                    })
            
            # 使用用户特定的对话记录进行记忆提取
            return await self._extract_memory(user_specific_conversation)
                
        except Exception as e:
            logger.error(f"生成记忆总结失败: {e}")
            return None

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
    if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
        await memory_manager.mysql_handler.close()
    logger.info("Mem0服务正在关闭")

# 创建FastAPI应用（禁用默认文档，使用自定义本地文档）
app = FastAPI(
    title="Mem0 自托管服务",
    description="支持国内LLM服务的智能记忆系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # 禁用默认的docs
    redoc_url=None  # 禁用默认的redoc
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("CORS_ORIGINS", '["*"]')),
    allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
    allow_methods=json.loads(os.getenv("CORS_ALLOW_METHODS", '["*"]')),
    allow_headers=json.loads(os.getenv("CORS_ALLOW_HEADERS", '["*"]')),
)

# 挂载静态文件目录（用于本地加载Swagger和ReDoc资源）
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ 已挂载本地静态资源目录: /static")
    
    # 自定义Swagger UI文档路由（使用本地资源）
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=app.title + " - Swagger UI",
            swagger_js_url="/static/swagger/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger/swagger-ui.css",
            swagger_favicon_url="/static/swagger/favicon-32x32.png",
        )
    
    # 自定义ReDoc文档路由（使用本地资源）
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=app.title + " - ReDoc",
            redoc_js_url="/static/redoc/redoc.standalone.js",
            redoc_favicon_url="/static/swagger/favicon-32x32.png",
        )
    
    logger.info("✅ 已配置本地化API文档页面: /docs 和 /redoc")
else:
    # 如果没有本地资源，使用默认CDN
    app.docs_url = "/docs"
    app.redoc_url = "/redoc"
    logger.warning("⚠️ 未找到本地静态资源目录，使用CDN加载文档资源")

# 安全认证
security = HTTPBearer()

async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = None):
    """验证API密钥（可选）"""
    # 如果没有设置API_SECRET_KEY或设置为空，则跳过验证
    api_key = os.getenv("API_SECRET_KEY", "").strip()
    if not api_key:
        return None
    
    # 如果设置了API_SECRET_KEY但没有提供credentials，则报错
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要API密钥"
        )
    
    # 验证token
    token = credentials.credentials
    if token != api_key:
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
        "vector_db": os.getenv("MEM0_VECTOR_STORE_PROVIDER", "qdrant")
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/memories/add")
async def add_memory(
    messages: List[MessageItem] = Body(
        ...,
        example=[
            {
                "user_id": 1,
                "content": "今天可太热了",
                "role": "user",
                "session_id": 123456
            },
            {
                "user_id": 2,
                "content": "是啊 都快40度了吧",
                "role": "user",
                "session_id": 123456
            },
            {
                "user_id": 3,
                "content": "北京今天的最高温度是34度哦",
                "role": "assistant",
                "session_id": 123456
            },
            {
                "user_id": 1,
                "content": "我最怕热了，冷一点还行",
                "role": "assistant",
                "session_id": 123456
            }
        ],
        description="消息数组，包含多个用户的对话内容"
    )
):
    """
    添加记忆 - 接收消息数组，为每个user生成记忆
    
    - 支持多用户对话场景
    - 只为 role='user' 的消息生成记忆
    - role='assistant' 的消息作为上下文但不生成记忆
    - 每个用户会根据完整对话上下文生成独立的记忆总结
    """
    return await memory_manager.add_memory(messages=messages)

@app.post("/api/v1/memories/search")
async def search_memory(
    request: MemorySearchRequest
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
    request: MemoryUpdateRequest
):
    """更新记忆"""
    return await memory_manager.update_memory(
        memory_id=request.memory_id,
        content=request.content,
        metadata=request.metadata,
        session_id=request.session_id
    )

@app.post("/api/v1/memories/delete")
async def delete_memory(
    request: MemoryDeleteRequest
):
    """删除记忆"""
    return await memory_manager.delete_memory(
        memory_id=request.memory_id,
        user_id=request.user_id
    )

@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest
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
    limit: int = 100
):
    """获取用户的所有记忆"""
    memories = await memory_manager.search_memory(
        user_id=user_id,
        query="",  # 空查询返回所有
        limit=limit
    )
    
    return {"memories": memories, "count": len(memories)}

@app.get("/api/v1/mysql/memories")
async def get_mysql_memories(
    user_id: Optional[str] = None,
    session_id: Optional[Union[str, int]] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    从MySQL获取记忆数据
    
    - user_id: 可选，用户ID筛选
    - session_id: 可选，会话ID筛选  
    - 如果都不传则查询所有记忆
    - 支持分页查询
    """
    if os.getenv("ENABLE_MYSQL", "false").lower() != "true":
        raise HTTPException(status_code=503, detail="MySQL未启用")
    try:
        memories = await memory_manager.mysql_handler.get_memories_with_filters(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        return {
            "memories": memories, 
            "count": len(memories),
            "filters": {
                "user_id": user_id,
                "session_id": session_id
            }
        }
    except Exception as e:
        logger.error(f"从MySQL获取记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mysql/memories/{memory_id}")
async def get_mysql_memory(
    memory_id: str
):
    """从MySQL获取单个记忆"""
    if os.getenv("ENABLE_MYSQL", "false").lower() != "true":
        raise HTTPException(status_code=503, detail="MySQL未启用")
    try:
        memory = await memory_manager.mysql_handler.get_memory(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")
        return {"memory": memory}
    except Exception as e:
        logger.error(f"从MySQL获取记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mysql/users/{user_id}/memories/search")
async def search_mysql_memories_by_time(
    user_id: str,
    start_time: str,
    end_time: str
):
    """按时间范围搜索MySQL中的记忆"""
    if os.getenv("ENABLE_MYSQL", "false").lower() != "true":
        raise HTTPException(status_code=503, detail="MySQL未启用")
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        
        memories = await memory_manager.mysql_handler.search_memories_by_time(
            user_id=user_id,
            start_time=start_dt,
            end_time=end_dt
        )
        return {"memories": memories, "count": len(memories)}
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误，请使用ISO格式如：2023-01-01T00:00:00")
    except Exception as e:
        logger.error(f"按时间搜索MySQL记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/memories/clear-all")
async def clear_all_data(
    token: str = Depends(verify_token)
):
    """清除所有数据（向量数据库和MySQL）- 危险操作"""
    logger.warning("收到清除所有数据的请求")
    
    try:
        results = await memory_manager.clear_all_data()
        
        # 记录操作结果
        if results["vector_db"]["status"] == "success":
            logger.info(f"向量数据库清除成功: {results['vector_db']['deleted_count']} 条记录")
        if results["mysql"]["status"] == "success":
            logger.info(f"MySQL数据库清除成功: {results['mysql']['deleted_count']} 条记录")
            
        return {
            "status": "success",
            "message": "所有数据已清除",
            "details": results
        }
    except Exception as e:
        logger.error(f"清除所有数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 9000)),
        reload=os.getenv("DEBUG_MODE", "false").lower() == "true"
    )