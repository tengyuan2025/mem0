import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from mem0.memory.mysql_memory import MySQLSyncMemory
from mem0.memory.chat_memory_storage import ChatMemoryStorage
from mem0.configs.base import MemoryConfig
from mem0.configs.mysql import MySQLConfig

logger = logging.getLogger(__name__)


class ChatMemoryManager(MySQLSyncMemory):
    """
    聊天记忆管理器 - 集成mem0记忆系统与xiaozhi聊天系统
    """
    
    def __init__(self, config=None, mysql_config=None):
        super().__init__(config, mysql_config)
        
        # 初始化聊天记忆存储
        self.chat_storage = ChatMemoryStorage(config=mysql_config)
        logger.info("ChatMemoryManager initialized with chat integration")
    
    def add_memory_from_chat_session(
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
            user_id: 用户ID (用于mem0记忆作用域)
            memory_text: 自定义记忆文本，如果为None且auto_generate=True则自动生成
            auto_generate: 是否自动从聊天内容生成记忆文本
            
        Returns:
            包含记忆信息和关联结果的字典
        """
        try:
            # 获取聊天会话内容
            chat_content = self.chat_storage.get_chat_session_content(agent_id, session_id)
            
            if not chat_content:
                raise ValueError(f"No chat content found for session {session_id}")
            
            # 如果没有提供记忆文本且需要自动生成
            if memory_text is None and auto_generate:
                # 使用mem0的LLM来生成记忆摘要
                memory_text = self._generate_memory_from_chat(chat_content)
            elif memory_text is None:
                # 直接使用聊天内容作为记忆
                memory_text = chat_content
            
            # 使用mem0添加记忆
            add_result = self.add(
                memory_text,
                user_id=user_id or agent_id,
                agent_id=agent_id,
                metadata={
                    "source": "chat_session",
                    "session_id": session_id,
                    "agent_id": agent_id
                }
            )
            
            if not add_result or not add_result.get("results"):
                raise ValueError("Failed to create memory in mem0")
            
            # 获取创建的记忆ID
            memory_id = add_result["results"][0]["id"]
            
            # 在chat memory表中创建对应记录
            self.chat_storage.add_memory(memory_id, memory_text)
            
            # 关联聊天记录
            linked_count = self.chat_storage.link_chat_to_memory(
                memory_id, agent_id, session_id
            )
            
            result = {
                "memory_id": memory_id,
                "memory_text": memory_text,
                "linked_chat_count": linked_count,
                "agent_id": agent_id,
                "session_id": session_id,
                "mem0_result": add_result
            }
            
            logger.info(f"Created memory {memory_id} from chat session {session_id}, linked {linked_count} chat records")
            return result
            
        except Exception as e:
            logger.error(f"Error creating memory from chat session: {e}")
            raise
    
    def _generate_memory_from_chat(self, chat_content: str) -> str:
        """使用LLM从聊天内容生成记忆摘要"""
        try:
            prompt = f"""
请从以下聊天对话中提取关键信息，生成一个简洁的记忆摘要。
重点关注：
1. 用户的个人信息、偏好、需求
2. 重要的决定或结论
3. 需要记住的关键事实

聊天内容：
{chat_content}

请生成一个简洁的记忆摘要（不超过200字）：
"""
            
            response = self.llm.generate_response([
                {"role": "user", "content": prompt}
            ])
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating memory from chat: {e}")
            # 如果LLM生成失败，返回聊天内容的简化版本
            return f"聊天会话记录: {chat_content[:200]}..."
    
    def get_memories_for_chat_session(
        self,
        agent_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """获取与聊天会话关联的所有记忆"""
        try:
            # 从chat storage获取记忆
            memories = self.chat_storage.get_memories_by_chat_session(agent_id, session_id)
            
            # 补充mem0的详细信息
            enhanced_memories = []
            for memory in memories:
                memory_id = memory["id"]
                
                # 从mem0获取详细信息
                mem0_memory = self.get(memory_id)
                
                if mem0_memory:
                    enhanced_memory = {
                        **memory,
                        "mem0_data": mem0_memory,
                        "vector_memory": mem0_memory.get("memory"),
                        "score": mem0_memory.get("score")
                    }
                else:
                    enhanced_memory = memory
                
                enhanced_memories.append(enhanced_memory)
            
            return enhanced_memories
            
        except Exception as e:
            logger.error(f"Error getting memories for chat session: {e}")
            return []
    
    def search_memories_for_agent(
        self,
        agent_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """为指定Agent搜索相关记忆"""
        try:
            # 使用mem0搜索
            search_results = self.search(
                query,
                agent_id=agent_id,
                limit=limit
            )
            
            if not search_results or not search_results.get("results"):
                return []
            
            # 补充聊天关联信息
            enhanced_results = []
            for result in search_results["results"]:
                memory_id = result["id"]
                
                # 获取关联的聊天记录
                chat_records = self.chat_storage.get_chat_records_by_memory(memory_id)
                
                enhanced_result = {
                    **result,
                    "linked_chat_count": len(chat_records),
                    "chat_sessions": list(set([
                        record["session_id"] for record in chat_records
                    ]))
                }
                
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching memories for agent: {e}")
            return []
    
    def update_memory_and_sync(
        self,
        memory_id: str,
        new_text: str
    ) -> Dict[str, Any]:
        """更新记忆并同步到chat storage"""
        try:
            # 更新mem0中的记忆
            update_result = self.update(memory_id, new_text)
            
            # 同步更新chat storage中的记忆
            self.chat_storage.update_memory(memory_id, new_text)
            
            logger.info(f"Updated memory {memory_id} and synced to chat storage")
            return update_result
            
        except Exception as e:
            logger.error(f"Error updating memory and sync: {e}")
            raise
    
    def delete_memory_and_unlink(
        self,
        memory_id: str
    ) -> Dict[str, Any]:
        """删除记忆并取消聊天关联"""
        try:
            # 取消聊天记录关联
            unlinked_count = self.chat_storage.unlink_chat_records(memory_id)
            
            # 删除mem0中的记忆
            delete_result = self.delete(memory_id)
            
            # 删除chat storage中的记忆
            self.chat_storage.delete_memory(memory_id)
            
            result = {
                **delete_result,
                "unlinked_chat_count": unlinked_count
            }
            
            logger.info(f"Deleted memory {memory_id} and unlinked {unlinked_count} chat records")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting memory and unlinking: {e}")
            raise
    
    def get_agent_memory_summary(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """获取Agent的记忆统计摘要"""
        try:
            # 获取mem0中的记忆数量
            mem0_memories = self.get_all(agent_id=agent_id)
            mem0_count = len(mem0_memories.get("results", [])) if mem0_memories else 0
            
            # 获取有记忆关联的会话
            sessions_with_memories = self.chat_storage.get_session_with_memories(agent_id)
            
            # 统计信息
            summary = {
                "agent_id": agent_id,
                "total_memories": mem0_count,
                "sessions_with_memories": len(sessions_with_memories),
                "total_linked_chats": sum([
                    session["chat_count"] for session in sessions_with_memories
                ]),
                "recent_sessions": sessions_with_memories[:5],  # 最近5个会话
                "memory_storage_healthy": True
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting agent memory summary: {e}")
            return {
                "agent_id": agent_id,
                "error": str(e),
                "memory_storage_healthy": False
            }
    
    def close(self):
        """关闭所有连接"""
        super().close()
        self.chat_storage.close()
    
    def __del__(self):
        self.close()