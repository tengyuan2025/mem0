"""
聊天记忆API接口

提供RESTful API风格的接口来管理聊天与记忆的关联
可以轻松集成到xiaozhi-esp32-server或其他Web框架中
"""

import logging
from typing import Any, Dict, List, Optional

from mem0.memory.chat_memory_manager import ChatMemoryManager
from mem0.configs.base import MemoryConfig
from mem0.configs.mysql import MySQLConfig

logger = logging.getLogger(__name__)


class ChatMemoryAPI:
    """聊天记忆API类"""
    
    def __init__(self, mysql_config: Optional[Dict[str, Any]] = None):
        """
        初始化API
        
        Args:
            mysql_config: MySQL配置字典，如果为None则使用默认xiaozhi配置
        """
        if mysql_config is None:
            mysql_config = MySQLConfig.for_xiaozhi_server().to_connection_dict()
        
        memory_config = MemoryConfig()
        self.manager = ChatMemoryManager(
            config=memory_config,
            mysql_config=mysql_config
        )
        logger.info("ChatMemoryAPI initialized")
    
    def create_memory_from_session(
        self,
        agent_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        memory_text: Optional[str] = None,
        auto_generate: bool = True
    ) -> Dict[str, Any]:
        """
        从聊天会话创建记忆
        
        Args:
            agent_id: Agent ID
            session_id: 会话ID
            user_id: 用户ID
            memory_text: 自定义记忆文本
            auto_generate: 是否自动生成记忆文本
            
        Returns:
            API响应格式的字典
        """
        try:
            result = self.manager.add_memory_from_chat_session(
                agent_id=agent_id,
                session_id=session_id,
                user_id=user_id,
                memory_text=memory_text,
                auto_generate=auto_generate
            )
            
            return {
                "success": True,
                "data": {
                    "memory_id": result["memory_id"],
                    "memory_text": result["memory_text"],
                    "linked_chat_count": result["linked_chat_count"],
                    "agent_id": result["agent_id"],
                    "session_id": result["session_id"]
                },
                "message": "Memory created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating memory from session: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create memory from session"
            }
    
    def get_session_memories(
        self,
        agent_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        获取会话关联的记忆
        
        Args:
            agent_id: Agent ID
            session_id: 会话ID
            
        Returns:
            包含记忆列表的API响应
        """
        try:
            memories = self.manager.get_memories_for_chat_session(agent_id, session_id)
            
            return {
                "success": True,
                "data": {
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "memories": [
                        {
                            "memory_id": mem["id"],
                            "text": mem["text"],
                            "created_at": mem["created_at"],
                            "updated_at": mem["updated_at"],
                            "vector_memory": mem.get("vector_memory"),
                            "score": mem.get("score")
                        }
                        for mem in memories
                    ],
                    "total_count": len(memories)
                },
                "message": "Session memories retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting session memories: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get session memories"
            }
    
    def search_agent_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        搜索Agent的记忆
        
        Args:
            agent_id: Agent ID
            query: 搜索查询
            limit: 结果限制数量
            
        Returns:
            搜索结果的API响应
        """
        try:
            results = self.manager.search_memories_for_agent(
                agent_id=agent_id,
                query=query,
                limit=limit
            )
            
            return {
                "success": True,
                "data": {
                    "agent_id": agent_id,
                    "query": query,
                    "results": [
                        {
                            "memory_id": result["id"],
                            "memory": result["memory"],
                            "score": result.get("score"),
                            "linked_chat_count": result["linked_chat_count"],
                            "chat_sessions": result["chat_sessions"],
                            "created_at": result.get("created_at"),
                            "updated_at": result.get("updated_at")
                        }
                        for result in results
                    ],
                    "total_count": len(results)
                },
                "message": "Memory search completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error searching agent memories: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search agent memories"
            }
    
    def update_memory(
        self,
        memory_id: str,
        new_text: str
    ) -> Dict[str, Any]:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            new_text: 新的记忆文本
            
        Returns:
            更新结果的API响应
        """
        try:
            result = self.manager.update_memory_and_sync(memory_id, new_text)
            
            return {
                "success": True,
                "data": {
                    "memory_id": memory_id,
                    "new_text": new_text
                },
                "message": "Memory updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update memory"
            }
    
    def delete_memory(
        self,
        memory_id: str
    ) -> Dict[str, Any]:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            删除结果的API响应
        """
        try:
            result = self.manager.delete_memory_and_unlink(memory_id)
            
            return {
                "success": True,
                "data": {
                    "memory_id": memory_id,
                    "unlinked_chat_count": result.get("unlinked_chat_count", 0)
                },
                "message": "Memory deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete memory"
            }
    
    def get_agent_summary(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        获取Agent记忆统计摘要
        
        Args:
            agent_id: Agent ID
            
        Returns:
            统计摘要的API响应
        """
        try:
            summary = self.manager.get_agent_memory_summary(agent_id)
            
            return {
                "success": True,
                "data": summary,
                "message": "Agent memory summary retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting agent summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get agent summary"
            }
    
    def link_existing_chat_to_memory(
        self,
        memory_id: str,
        agent_id: str,
        session_id: str,
        chat_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        将现有聊天记录关联到记忆
        
        Args:
            memory_id: 记忆ID
            agent_id: Agent ID
            session_id: 会话ID
            chat_ids: 具体的聊天记录ID列表，为None时关联整个会话
            
        Returns:
            关联结果的API响应
        """
        try:
            linked_count = self.manager.chat_storage.link_chat_to_memory(
                memory_id=memory_id,
                agent_id=agent_id,
                session_id=session_id,
                chat_ids=chat_ids
            )
            
            return {
                "success": True,
                "data": {
                    "memory_id": memory_id,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "linked_count": linked_count,
                    "chat_ids": chat_ids
                },
                "message": "Chat records linked to memory successfully"
            }
            
        except Exception as e:
            logger.error(f"Error linking chat to memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to link chat records to memory"
            }
    
    def get_memory_chat_records(
        self,
        memory_id: str
    ) -> Dict[str, Any]:
        """
        获取记忆关联的聊天记录
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            聊天记录的API响应
        """
        try:
            chat_records = self.manager.chat_storage.get_chat_records_by_memory(memory_id)
            
            return {
                "success": True,
                "data": {
                    "memory_id": memory_id,
                    "chat_records": [
                        {
                            "chat_id": record["id"],
                            "agent_id": record["agent_id"],
                            "session_id": record["session_id"],
                            "chat_type": record["chat_type"],
                            "content": record["content"],
                            "created_at": record["created_at"],
                            "mac_address": record.get("mac_address")
                        }
                        for record in chat_records
                    ],
                    "total_count": len(chat_records)
                },
                "message": "Memory chat records retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting memory chat records: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get memory chat records"
            }
    
    def close(self):
        """关闭API连接"""
        self.manager.close()
        logger.info("ChatMemoryAPI closed")
    
    def __del__(self):
        self.close()


# Flask/FastAPI 集成示例

def create_flask_routes(app, api_instance: ChatMemoryAPI):
    """为Flask应用创建路由"""
    try:
        from flask import request, jsonify
        
        @app.route('/api/memory/create-from-session', methods=['POST'])
        def create_memory_from_session():
            data = request.get_json()
            result = api_instance.create_memory_from_session(
                agent_id=data['agent_id'],
                session_id=data['session_id'],
                user_id=data.get('user_id'),
                memory_text=data.get('memory_text'),
                auto_generate=data.get('auto_generate', True)
            )
            return jsonify(result)
        
        @app.route('/api/memory/session/<agent_id>/<session_id>', methods=['GET'])
        def get_session_memories(agent_id, session_id):
            result = api_instance.get_session_memories(agent_id, session_id)
            return jsonify(result)
        
        @app.route('/api/memory/search/<agent_id>', methods=['GET'])
        def search_agent_memories(agent_id):
            query = request.args.get('query', '')
            limit = int(request.args.get('limit', 10))
            result = api_instance.search_agent_memories(agent_id, query, limit)
            return jsonify(result)
        
        @app.route('/api/memory/<memory_id>', methods=['PUT'])
        def update_memory(memory_id):
            data = request.get_json()
            result = api_instance.update_memory(memory_id, data['text'])
            return jsonify(result)
        
        @app.route('/api/memory/<memory_id>', methods=['DELETE'])
        def delete_memory(memory_id):
            result = api_instance.delete_memory(memory_id)
            return jsonify(result)
        
        @app.route('/api/memory/agent/<agent_id>/summary', methods=['GET'])
        def get_agent_summary(agent_id):
            result = api_instance.get_agent_summary(agent_id)
            return jsonify(result)
        
        logger.info("Flask routes created successfully")
        
    except ImportError:
        logger.warning("Flask not available, skipping Flask route creation")


def create_fastapi_routes(app, api_instance: ChatMemoryAPI):
    """为FastAPI应用创建路由"""
    try:
        from fastapi import Body
        from pydantic import BaseModel
        
        class CreateMemoryRequest(BaseModel):
            agent_id: str
            session_id: str
            user_id: Optional[str] = None
            memory_text: Optional[str] = None
            auto_generate: bool = True
        
        class UpdateMemoryRequest(BaseModel):
            text: str
        
        @app.post("/api/memory/create-from-session")
        async def create_memory_from_session(request: CreateMemoryRequest):
            return api_instance.create_memory_from_session(
                agent_id=request.agent_id,
                session_id=request.session_id,
                user_id=request.user_id,
                memory_text=request.memory_text,
                auto_generate=request.auto_generate
            )
        
        @app.get("/api/memory/session/{agent_id}/{session_id}")
        async def get_session_memories(agent_id: str, session_id: str):
            return api_instance.get_session_memories(agent_id, session_id)
        
        @app.get("/api/memory/search/{agent_id}")
        async def search_agent_memories(agent_id: str, query: str, limit: int = 10):
            return api_instance.search_agent_memories(agent_id, query, limit)
        
        @app.put("/api/memory/{memory_id}")
        async def update_memory(memory_id: str, request: UpdateMemoryRequest):
            return api_instance.update_memory(memory_id, request.text)
        
        @app.delete("/api/memory/{memory_id}")
        async def delete_memory(memory_id: str):
            return api_instance.delete_memory(memory_id)
        
        @app.get("/api/memory/agent/{agent_id}/summary")
        async def get_agent_summary(agent_id: str):
            return api_instance.get_agent_summary(agent_id)
        
        logger.info("FastAPI routes created successfully")
        
    except ImportError:
        logger.warning("FastAPI not available, skipping FastAPI route creation")