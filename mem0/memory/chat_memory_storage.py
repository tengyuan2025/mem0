import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import mysql.connector
from mysql.connector import Error
import pytz

from mem0.configs.mysql import MySQLConfig

logger = logging.getLogger(__name__)


class ChatMemoryStorage:
    """
    增强的MySQL存储管理器，用于处理记忆与聊天记录的关联
    """
    
    def __init__(
        self,
        config: Optional[Union[MySQLConfig, Dict[str, Any]]] = None,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "123456",
        database: str = "xiaozhi_esp32_server",
        **kwargs
    ):
        # Handle configuration
        if config is not None:
            if isinstance(config, dict):
                self.config = MySQLConfig(**config)
            elif isinstance(config, MySQLConfig):
                self.config = config
            else:
                raise ValueError("config must be MySQLConfig instance or dict")
        else:
            # Use individual parameters for backward compatibility
            self.config = MySQLConfig(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                **kwargs
            )
        
        self.connection = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        """Establish connection to MySQL database"""
        try:
            connection_config = self.config.to_connection_dict()
            self.connection = mysql.connector.connect(**connection_config)
            logger.info(f"Successfully connected to MySQL database: {self.config.database}")
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            raise

    def _reconnect(self) -> None:
        """Reconnect to MySQL database if connection is lost"""
        try:
            if self.connection:
                self.connection.close()
        except:
            pass
        self._connect()

    def _execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute MySQL query with automatic reconnection"""
        with self._lock:
            try:
                if not self.connection or not self.connection.is_connected():
                    self._reconnect()
                
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                    cursor.close()
                    return result
                else:
                    self.connection.commit()
                    cursor.close()
                    return None
                    
            except Error as e:
                logger.error(f"MySQL query error: {e}")
                try:
                    self._reconnect()
                    cursor = self.connection.cursor(dictionary=True)
                    cursor.execute(query, params or ())
                    
                    if fetch:
                        result = cursor.fetchall()
                        cursor.close()
                        return result
                    else:
                        self.connection.commit()
                        cursor.close()
                        return None
                except Error as retry_error:
                    logger.error(f"MySQL retry failed: {retry_error}")
                    raise retry_error

    def add_memory(
        self,
        memory_id: str,
        text: str,
        created_at: Optional[str] = None,
    ) -> None:
        """Add a new memory record"""
        if created_at is None:
            created_at = datetime.now(pytz.timezone("US/Pacific")).isoformat()
        
        insert_query = """
        INSERT INTO memory (id, text, created_at, updated_at) 
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            self._execute_query(insert_query, (
                memory_id, text, created_at, created_at
            ))
            logger.debug(f"Added memory to MySQL: {memory_id}")
        except Error as e:
            logger.error(f"Error adding memory to MySQL: {e}")
            raise

    def update_memory(
        self,
        memory_id: str,
        text: str,
        updated_at: Optional[str] = None,
    ) -> None:
        """Update an existing memory record"""
        if updated_at is None:
            updated_at = datetime.now(pytz.timezone("US/Pacific")).isoformat()
        
        update_query = """
        UPDATE memory 
        SET text = %s, updated_at = %s
        WHERE id = %s
        """
        
        try:
            self._execute_query(update_query, (text, updated_at, memory_id))
            logger.debug(f"Updated memory in MySQL: {memory_id}")
        except Error as e:
            logger.error(f"Error updating memory in MySQL: {e}")
            raise

    def delete_memory(self, memory_id: str) -> None:
        """Delete a memory record and unlink chat records"""
        try:
            # First, unlink chat records
            self.unlink_chat_records(memory_id)
            
            # Then delete the memory
            delete_query = "DELETE FROM memory WHERE id = %s"
            self._execute_query(delete_query, (memory_id,))
            logger.debug(f"Deleted memory from MySQL: {memory_id}")
        except Error as e:
            logger.error(f"Error deleting memory from MySQL: {e}")
            raise

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory record by ID"""
        select_query = "SELECT * FROM memory WHERE id = %s"
        
        try:
            result = self._execute_query(select_query, (memory_id,), fetch=True)
            if result:
                return result[0]
            return None
        except Error as e:
            logger.error(f"Error getting memory from MySQL: {e}")
            raise

    def link_chat_to_memory(
        self,
        memory_id: str,
        agent_id: str,
        session_id: str,
        chat_ids: Optional[List[int]] = None
    ) -> int:
        """
        将聊天记录关联到记忆
        
        Args:
            memory_id: 记忆ID
            agent_id: Agent ID
            session_id: 会话ID  
            chat_ids: 具体的聊天记录ID列表，如果为None则关联整个会话
            
        Returns:
            关联的聊天记录数量
        """
        try:
            if chat_ids:
                # 关联指定的聊天记录
                update_query = """
                UPDATE ai_agent_chat_history 
                SET memory_id = %s 
                WHERE id IN ({})
                """.format(','.join(['%s'] * len(chat_ids)))
                
                params = [memory_id] + chat_ids
                self._execute_query(update_query, params)
                affected_rows = len(chat_ids)
            else:
                # 关联整个会话的聊天记录
                update_query = """
                UPDATE ai_agent_chat_history 
                SET memory_id = %s 
                WHERE agent_id = %s AND session_id = %s
                """
                
                self._execute_query(update_query, (memory_id, agent_id, session_id))
                
                # 获取影响的行数
                count_query = """
                SELECT COUNT(*) as count 
                FROM ai_agent_chat_history 
                WHERE agent_id = %s AND session_id = %s AND memory_id = %s
                """
                result = self._execute_query(count_query, (agent_id, session_id, memory_id), fetch=True)
                affected_rows = result[0]['count'] if result else 0
            
            logger.info(f"Linked {affected_rows} chat records to memory {memory_id}")
            return affected_rows
            
        except Error as e:
            logger.error(f"Error linking chat to memory: {e}")
            raise

    def unlink_chat_records(self, memory_id: str) -> int:
        """取消聊天记录与记忆的关联"""
        try:
            update_query = """
            UPDATE ai_agent_chat_history 
            SET memory_id = NULL 
            WHERE memory_id = %s
            """
            
            # 先获取影响的行数
            count_query = """
            SELECT COUNT(*) as count 
            FROM ai_agent_chat_history 
            WHERE memory_id = %s
            """
            result = self._execute_query(count_query, (memory_id,), fetch=True)
            affected_rows = result[0]['count'] if result else 0
            
            # 执行取消关联
            self._execute_query(update_query, (memory_id,))
            
            logger.info(f"Unlinked {affected_rows} chat records from memory {memory_id}")
            return affected_rows
            
        except Error as e:
            logger.error(f"Error unlinking chat records: {e}")
            raise

    def get_chat_records_by_memory(self, memory_id: str) -> List[Dict[str, Any]]:
        """获取与指定记忆关联的所有聊天记录"""
        select_query = """
        SELECT * FROM ai_agent_chat_history 
        WHERE memory_id = %s 
        ORDER BY created_at ASC
        """
        
        try:
            result = self._execute_query(select_query, (memory_id,), fetch=True)
            return result or []
        except Error as e:
            logger.error(f"Error getting chat records by memory: {e}")
            raise

    def get_memories_by_chat_session(
        self,
        agent_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """获取与指定聊天会话关联的所有记忆"""
        select_query = """
        SELECT DISTINCT m.* 
        FROM memory m
        JOIN ai_agent_chat_history ch ON m.id = ch.memory_id
        WHERE ch.agent_id = %s AND ch.session_id = %s
        ORDER BY m.created_at DESC
        """
        
        try:
            result = self._execute_query(select_query, (agent_id, session_id), fetch=True)
            return result or []
        except Error as e:
            logger.error(f"Error getting memories by chat session: {e}")
            raise

    def get_session_with_memories(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取包含记忆的会话列表"""
        select_query = """
        SELECT 
            ch.session_id,
            ch.agent_id,
            COUNT(DISTINCT ch.memory_id) as memory_count,
            COUNT(ch.id) as chat_count,
            MIN(ch.created_at) as session_start,
            MAX(ch.created_at) as session_end
        FROM ai_agent_chat_history ch
        WHERE ch.agent_id = %s AND ch.memory_id IS NOT NULL
        GROUP BY ch.session_id, ch.agent_id
        ORDER BY session_end DESC
        LIMIT %s
        """
        
        try:
            result = self._execute_query(select_query, (agent_id, limit), fetch=True)
            return result or []
        except Error as e:
            logger.error(f"Error getting sessions with memories: {e}")
            raise

    def create_memory_from_chat_session(
        self,
        agent_id: str,
        session_id: str,
        memory_text: str,
        memory_id: Optional[str] = None
    ) -> str:
        """
        从聊天会话创建记忆并自动关联
        
        Args:
            agent_id: Agent ID
            session_id: 会话ID
            memory_text: 记忆文本
            memory_id: 可选的记忆ID，如果不提供则自动生成
            
        Returns:
            创建的记忆ID
        """
        try:
            if memory_id is None:
                memory_id = str(uuid.uuid4())
            
            # 创建记忆
            self.add_memory(memory_id, memory_text)
            
            # 关联聊天记录
            linked_count = self.link_chat_to_memory(memory_id, agent_id, session_id)
            
            logger.info(f"Created memory {memory_id} and linked {linked_count} chat records")
            return memory_id
            
        except Error as e:
            logger.error(f"Error creating memory from chat session: {e}")
            raise

    def get_chat_session_content(
        self,
        agent_id: str,
        session_id: str
    ) -> str:
        """获取会话的完整聊天内容，用于生成记忆"""
        select_query = """
        SELECT chat_type, content, created_at
        FROM ai_agent_chat_history 
        WHERE agent_id = %s AND session_id = %s 
        ORDER BY created_at ASC
        """
        
        try:
            result = self._execute_query(select_query, (agent_id, session_id), fetch=True)
            
            if not result:
                return ""
            
            # 格式化聊天内容
            chat_content = []
            for record in result:
                chat_type = record['chat_type']
                content = record['content']
                timestamp = record['created_at']
                
                if chat_type == 1:  # 用户消息
                    chat_content.append(f"用户: {content}")
                elif chat_type == 2:  # AI回复
                    chat_content.append(f"AI: {content}")
                else:
                    chat_content.append(f"系统: {content}")
            
            return "\n".join(chat_content)
            
        except Error as e:
            logger.error(f"Error getting chat session content: {e}")
            raise

    def close(self) -> None:
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

    def __del__(self):
        self.close()