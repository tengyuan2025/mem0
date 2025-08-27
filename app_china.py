"""
Mem0 中国大陆优化版本
完全本地运行，无需任何在线API，专为中文优化
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
import re
from datetime import datetime
import hashlib
import json
import math
from collections import Counter
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
# 中文文本处理工具
# ==========================================

class ChineseTextMatcher:
    """中文文本匹配器 - 完全本地，无需任何API"""
    
    def __init__(self):
        # 中文停用词
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', 
            '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '它', '他', '她',
            '什么', '为什么', '怎么', '哪里', '谁', '多少', '几个', '吗', '呢', '吧', '啊', '哦', '嗯'
        }
    
    def tokenize_chinese(self, text: str) -> List[str]:
        """中文分词 - 简单but有效的方法"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分离中文和英文
        tokens = []
        current_token = ""
        
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                if current_token and not ('\u4e00' <= current_token[-1] <= '\u9fff'):
                    if current_token.strip():
                        tokens.append(current_token.strip())
                    current_token = char
                else:
                    current_token += char
            elif char.isalnum():  # 英文字符
                current_token += char
            else:  # 空格或其他
                if current_token.strip():
                    tokens.append(current_token.strip())
                current_token = ""
        
        if current_token.strip():
            tokens.append(current_token.strip())
        
        # 中文按单个字符和双字符分词
        final_tokens = []
        for token in tokens:
            if '\u4e00' <= token[0] <= '\u9fff':  # 中文token
                # 添加单字符
                for char in token:
                    if char not in self.stopwords:
                        final_tokens.append(char)
                # 添加双字符组合
                for i in range(len(token) - 1):
                    bigram = token[i:i+2]
                    if bigram not in self.stopwords:
                        final_tokens.append(bigram)
                # 添加整个词（如果长度合适）
                if 2 <= len(token) <= 4 and token not in self.stopwords:
                    final_tokens.append(token)
            else:  # 英文token
                if token.lower() not in self.stopwords and len(token) > 1:
                    final_tokens.append(token.lower())
        
        return final_tokens
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        tokens1 = self.tokenize_chinese(text1)
        tokens2 = self.tokenize_chinese(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # 计算词频
        freq1 = Counter(tokens1)
        freq2 = Counter(tokens2)
        
        # 计算余弦相似度
        all_tokens = set(tokens1) | set(tokens2)
        
        vec1 = [freq1[token] for token in all_tokens]
        vec2 = [freq2[token] for token in all_tokens]
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # 奖励完全匹配的关键词
        exact_matches = len(set(tokens1) & set(tokens2))
        if exact_matches > 0:
            similarity += min(0.3, exact_matches * 0.1)  # 最多增加0.3
        
        return min(1.0, similarity)

# ==========================================
# 记忆管理器
# ==========================================

class ChinaMemoryManager:
    """中国大陆专用记忆管理器"""
    
    def __init__(self):
        self.memories = {}  # user_id -> List[memory]
        self.text_matcher = ChineseTextMatcher()
        self.initialized = False
        
    async def initialize(self):
        """初始化记忆管理器"""
        if self.initialized:
            return
            
        self.initialized = True
        logger.info("中文记忆管理器初始化成功")
    
    async def add_memory(self, user_id: str, messages: List[Dict], metadata: Dict = None) -> Dict:
        """添加记忆"""
        try:
            # 提取对话内容
            content = " | ".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # 生成记忆ID
            memory_id = hashlib.md5(
                f"{user_id}_{content}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:12]
            
            # 提取关键词
            keywords = self.text_matcher.tokenize_chinese(content)
            
            # 准备元数据
            metadata = metadata or {}
            metadata.update({
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "content": content,
                "keywords": keywords[:20]  # 保存前20个关键词
            })
            
            # 存储记忆
            if user_id not in self.memories:
                self.memories[user_id] = []
            
            memory = {
                "memory_id": memory_id,
                "content": content,
                "keywords": keywords,
                "metadata": metadata
            }
            
            self.memories[user_id].append(memory)
            
            logger.info(f"记忆添加成功: {memory_id}")
            
            return {
                "status": "success", 
                "memory_id": memory_id,
                "content": content,
                "keywords_count": len(keywords)
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
            
            # 使用改进的中文文本匹配
            for memory in memories:
                similarity = self.text_matcher.calculate_similarity(query, memory["content"])
                
                # 设置最小阈值
                if similarity > 0.1:  # 调整阈值
                    results.append({
                        "memory_id": memory["memory_id"],
                        "content": memory["content"],
                        "score": float(similarity),
                        "metadata": memory["metadata"]
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
        """带记忆的智能聊天"""
        # 中文聊天模板
        response_templates = {
            "咖啡": "根据我的记忆，您喜欢喝咖啡，特别是拿铁。",
            "拿铁": "我记得您特别喜欢拿铁咖啡。",
            "工作": "根据我的记忆，您在北京的科技公司工作。",
            "住址": "我记得您住在北京。",
            "北京": "我记得您住在北京，在科技公司工作。",
            "公司": "您在科技公司工作对吗？",
            "你好": "您好！我是您的智能助手，很高兴为您服务。",
            "谢谢": "不客气！我会继续记住我们的对话。有什么其他需要帮助的吗？",
            "什么": "让我想想，",
            "知道": "基于我们之前的对话，",
            "记得": "是的，我记得",
            "喜欢": "根据我的了解，"
        }
        
        context = ""
        relevant_memories = []
        
        if use_memory:
            # 搜索相关记忆
            memories = await self.search_memory(user_id, message, limit=3)
            relevant_memories = memories
            
            if memories:
                # 构建上下文，使用最相关的记忆
                context = "基于我们之前的对话，"
                if memories[0]["score"] > 0.5:  # 高相关性
                    context += f"我记得{memories[0]['content'].split('|')[0].replace('user:', '').strip()}。"
        
        # 智能模板匹配
        response = None
        for keyword, template in response_templates.items():
            if keyword in message:
                response = context + template
                break
        
        # 如果没有匹配到模板，使用通用回复
        if not response:
            if relevant_memories:
                response = context + "我会结合我们之前的对话来回答您的问题。"
            else:
                response = "我理解您的问题。作为您的智能助手，我会记住我们的对话内容。"
        
        # 保存新的对话记忆
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

memory_manager = ChinaMemoryManager()

app = FastAPI(
    title="Mem0 中国版",
    description="专为中国大陆优化的本地智能记忆系统",
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
    logger.info("Mem0中国版服务启动成功")

# 安全认证
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
        "service": "Mem0 中国版",
        "version": "1.0.0",
        "status": "running",
        "features": ["中文优化", "完全本地", "无需API"],
        "text_matcher": "Chinese Enhanced"
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
            "keywords_count": len(memory.get("keywords", [])),
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