"""
Mem0 自托管服务主应用
支持国内LLM服务和本地向量数据库
"""

from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import os
import sys
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
    user_id: str = Field(..., description="用户ID")
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
        vector_db_type = os.getenv("MEM0_VECTOR_STORE_PROVIDER", "chroma")
        
        if vector_db_type == "chroma":
            import chromadb
            from chromadb.config import Settings
            
            # 检查是否使用持久化存储
            if os.getenv("MEM0_VECTOR_STORE_TYPE") == "persistent":
                persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
                os.makedirs(persist_dir, exist_ok=True)
                self.vector_db = chromadb.PersistentClient(path=persist_dir)
            else:
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
        logger.info(f"开始初始化Embedding客户端: {embedding_provider}")
        
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
                    memory_summary = await self._generate_memory_summary(
                        user_id=user_id,
                        user_messages=contents,
                        all_conversation=all_conversation,
                        historical_content=historical_content
                    )
                    
                    if not memory_summary:
                        logger.info(f"用户 {user_id} 没有需要记忆的内容")
                        continue
                    
                    # 生成向量嵌入
                    embedding = await self._generate_embedding(memory_summary)
                    
                    # 生成记忆ID
                    memory_id = hashlib.md5(
                        f"{user_id}_{memory_summary}_{datetime.utcnow().isoformat()}".encode()
                    ).hexdigest()
                    
                    # 准备元数据
                    user_metadata = (metadata or {}).copy()
                    user_metadata.update({
                        "user_id": user_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "content": memory_summary
                    })
                    
                    # 存储到向量数据库
                    if os.getenv("VECTOR_DB") == "chroma":
                        self.collection.add(
                            ids=[memory_id],
                            embeddings=[embedding],
                            metadatas=[user_metadata]
                        )
                    
                    # 同时存储到MySQL数据库（如果启用）
                    if os.getenv("ENABLE_MYSQL", "false").lower() == "true":
                        try:
                            # 获取该用户的session_id
                            session_id = user_session_ids.get(user_id)
                            await self.mysql_handler.insert_memory(
                                memory_id=memory_id,
                                user_id=user_id,
                                content=memory_summary,
                                metadata=user_metadata,
                                session_id=session_id
                            )
                            logger.info(f"用户 {user_id} 记忆已同步到MySQL: {memory_id}")
                        except Exception as e:
                            logger.error(f"用户 {user_id} 同步记忆到MySQL失败，但向量数据库已保存: {e}")
                    
                    results.append({
                        "user_id": user_id,
                        "memory_id": memory_id,
                        "status": "success",
                        "content": memory_summary,
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
    
    async def update_memory(self, memory_id: str, content: str = None, metadata: Dict = None,
                           event: str = None, knowledge: str = None, skill: str = None, 
                           session_id: int = None) -> Dict:
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
                                     all_conversation: List[Dict], historical_content: List[str]) -> str:
        """从时间、事件、技能、知识维度生成记忆总结"""
        try:
            llm_provider = os.getenv("LLM_PROVIDER", "dashscope")
            
            # 构建历史上下文
            context_text = ""
            if historical_content:
                context_text = f"用户 {user_id} 的历史记忆：\n" + "\n".join(historical_content[-10:]) + "\n\n"
            
            # 构建完整对话上下文
            conversation_text = "完整对话记录：\n"
            for msg in all_conversation:
                role_label = f"用户{msg['user_id']}" if msg['role'] == 'user' else f"助手{msg['user_id']}"
                conversation_text += f"{role_label}: {msg['content']}\n"
            
            # 用户在本次对话中的发言
            user_content = f"\n用户 {user_id} 在本次对话中说的话：\n" + "\n".join(user_messages)
            
            # 构建提示词
            prompt = f"""请基于完整对话上下文，为用户 {user_id} 生成记忆总结。

{context_text}{conversation_text}
{user_content}

请从以下维度进行分析总结：
1. 时间：相关的时间信息或时间背景
2. 事件：用户描述或经历的具体事件
3. 技能：用户展示出的技能、能力或专长
4. 知识：用户分享的知识、观点或见解

要求：
- 生成一段200字以内的总结
- 重点关注有价值的信息
- 如果本次对话没有值得记忆的内容，请返回空字符串
- 总结要自然流畅，不要机械地按维度分段

记忆总结："""
            
            if llm_provider == "dashscope":
                from dashscope import Generation
                
                response = Generation.call(
                    model=self.llm_model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    result_format='message'
                )
                
                if response.status_code == 200:
                    summary = response.output.choices[0]['message']['content'].strip()
                    # 如果返回空或无意义内容，返回None
                    if not summary or len(summary) < 10 or "没有值得记忆" in summary:
                        return None
                    return summary
                else:
                    logger.error(f"LLM记忆总结生成失败: {response}")
                    return None
            
            elif llm_provider == "deepseek":
                # DeepSeek 记忆总结
                try:
                    response = self.llm_client.chat.completions.create(
                        model=self.llm_model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    if response.choices and len(response.choices) > 0:
                        summary = response.choices[0].message.content.strip()
                        # 如果返回空或无意义内容，返回None
                        if not summary or len(summary) < 10 or "没有值得记忆" in summary:
                            return None
                        return summary
                    else:
                        logger.error(f"DeepSeek记忆总结生成失败: 没有返回内容")
                        return None
                        
                except Exception as e:
                    logger.error(f"DeepSeek记忆总结生成异常: {e}")
                    return None
            
            # 其他LLM提供商的实现可以在这里添加
            else:
                logger.warning(f"不支持的LLM提供商: {llm_provider}")
                # 简单的fallback逻辑
                if user_messages:
                    return f"用户在会话中的内容: {' '.join(user_messages[:2])}"
                return None
                
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
        "vector_db": os.getenv("VECTOR_DB", "chroma")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 9000)),
        reload=os.getenv("DEBUG_MODE", "false").lower() == "true"
    )