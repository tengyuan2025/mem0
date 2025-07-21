import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import pytz

from mem0.memory.main import Memory
from mem0.memory.mysql_storage import MySQLManager
from mem0.memory.role_manager import RoleManager

logger = logging.getLogger(__name__)


class MySQLSyncMemory(Memory):
    """
    Extended Memory class that syncs all memory operations to MySQL database
    alongside the existing vector store operations.
    """
    
    def __init__(self, config=None, mysql_config=None):
        super().__init__(config)
        
        # Initialize MySQL storage
        mysql_config = mysql_config or {}
        self.mysql_db = MySQLManager(**mysql_config)
        
        # Initialize role manager with MySQL config
        from mem0.configs.mysql import MySQLConfig
        if isinstance(mysql_config, dict):
            mysql_conn_config = MySQLConfig(**mysql_config).to_connection_dict()
        else:
            mysql_conn_config = mysql_config.to_connection_dict()
        self.role_manager = RoleManager(mysql_conn_config)
        
        # 修复可能存在的孤立role_id引用
        self.role_manager.fix_orphaned_role_references()
        
        logger.info("MySQL sync enabled for mem0 memory operations")
    
    def _create_memory(self, data, existing_embeddings, metadata=None, original_text=None):
        """Override to sync with MySQL"""
        # Call parent method to handle vector store
        memory_id = super()._create_memory(data, existing_embeddings, metadata, original_text)
        
        # Sync to MySQL
        try:
            self._sync_memory_to_mysql(memory_id, data, metadata, original_text, "ADD")
        except Exception as e:
            logger.error(f"Failed to sync memory {memory_id} to MySQL: {e}")
            # Don't fail the operation, just log the error
        
        return memory_id
    
    def _update_memory(self, memory_id, data, existing_embeddings, metadata=None):
        """Override to sync with MySQL"""
        # Get existing memory for history
        try:
            existing_memory = self.vector_store.get(vector_id=memory_id)
            prev_value = existing_memory.payload.get("data") if existing_memory else None
        except Exception:
            prev_value = None
        
        # Call parent method to handle vector store
        result = super()._update_memory(memory_id, data, existing_embeddings, metadata)
        
        # Sync to MySQL
        try:
            self._sync_memory_to_mysql(memory_id, data, metadata, None, "UPDATE", prev_value)
        except Exception as e:
            logger.error(f"Failed to sync memory update {memory_id} to MySQL: {e}")
        
        return result
    
    def _delete_memory(self, memory_id):
        """Override to sync with MySQL"""
        # Get existing memory for history
        try:
            existing_memory = self.vector_store.get(vector_id=memory_id)
            prev_value = existing_memory.payload.get("data") if existing_memory else None
        except Exception:
            prev_value = None
        
        # Call parent method to handle vector store
        result = super()._delete_memory(memory_id)
        
        # Sync to MySQL
        try:
            self._sync_memory_deletion_to_mysql(memory_id, prev_value)
        except Exception as e:
            logger.error(f"Failed to sync memory deletion {memory_id} to MySQL: {e}")
        
        return result
    
    def _sync_memory_to_mysql(self, memory_id, data, metadata=None, original_text=None, event="ADD", prev_value=None):
        """Sync memory data to MySQL"""
        metadata = metadata or {}
        
        # Extract fields from metadata
        user_id = metadata.get("user_id")
        # mem0框架会将run_id参数添加到metadata中，优先使用run_id
        session_id = metadata.get("run_id") or metadata.get("session_id")
        actor_id = metadata.get("actor_id")
        role = metadata.get("role")
        created_at = metadata.get("created_at")
        updated_at = metadata.get("updated_at")
        
        # 调试日志
        logger.info(f"Syncing memory - session_id: {session_id}, metadata keys: {list(metadata.keys())}, run_id: {metadata.get('run_id')}, session_id: {metadata.get('session_id')}")
        
        # 检查是否是总结类型的记忆
        is_summary = (
            original_text and 
            ('总结' in original_text or '基于对话总结' in data)
        )
        
        if is_summary:
            logger.info("Detected summary memory - checking for existing summary for this participant")
            # 检查该用户在此session中是否已有总结记忆
            check_query = """
            SELECT id FROM memory 
            WHERE user_id = %s AND session_id = %s AND memory_text LIKE '%总结%'
            LIMIT 1
            """
            try:
                existing_summary = self.mysql_db._execute_query(
                    check_query, 
                    (user_id, session_id), 
                    fetch=True
                )
                
                if existing_summary:
                    # 如果已有总结，更新而不是新增
                    logger.info(f"Updating existing summary for user {user_id} in session {session_id}")
                    update_query = """
                    UPDATE memory 
                    SET memory_text = %s, updated_at = %s 
                    WHERE user_id = %s AND session_id = %s AND memory_text LIKE '%总结%'
                    """
                    self.mysql_db._execute_query(
                        update_query, 
                        (data, updated_at or created_at, user_id, session_id)
                    )
                    return  # 不继续执行后面的插入逻辑
            except Exception as e:
                logger.error(f"Error checking existing summary: {e}")
                # 如果检查失败，继续正常流程
        
        # 处理角色信息 - 优先使用请求中传入的角色信息
        voice_hash = metadata.get("voice_hash")
        request_role_id = metadata.get("role_id")
        request_role_name = metadata.get("role_name")
        
        if request_role_id and request_role_name:
            # 如果请求中包含角色信息，直接使用
            role_id = request_role_id
            clean_text = data  # 保持原始文本，因为已经在xiaozhi-server中处理过了
            logger.info(f"Using role from request: {request_role_name} (ID: {request_role_id})")
        else:
            # 如果没有角色信息，使用原有的文本解析逻辑（向后兼容）
            try:
                clean_text, text_role_info = self.role_manager.parse_role_from_text(data)
                
                # 如果有voice_hash，尝试基于voice_hash进行角色识别
                if voice_hash and text_role_info and text_role_info.get('name') == '用户':
                    voice_matched_role = self.role_manager.identify_role_by_voice(voice_hash)
                    
                    if voice_matched_role:
                        logger.info(f"Matched voice_hash {voice_hash} to existing role: {voice_matched_role['name']} (ID: {voice_matched_role['id']})")
                        role_info = voice_matched_role
                    else:
                        self.role_manager.update_role_voice_hash(text_role_info['id'], voice_hash)
                        text_role_info['voice_hash'] = voice_hash
                        role_info = text_role_info
                else:
                    role_info = text_role_info
                
                role_id = role_info.get('id') if role_info and isinstance(role_info, dict) else None
                
                # 如果解析出了角色，更新数据为清理后的文本
                if clean_text != data:
                    data = clean_text
                    
            except Exception as role_error:
                logger.error(f"Error in role processing: {role_error}")
                clean_text = data
                role_id = None
        
        # Prepare additional metadata (excluding standard fields)
        additional_metadata = {
            k: v for k, v in metadata.items() 
            if k not in ["user_id", "session_id", "actor_id", "role", "data", "created_at", "updated_at", "original_text"]
        }
        
        if event == "ADD":
            # Add new memory record
            self.mysql_db.add_memory(
                memory_id=memory_id,
                memory_text=data,
                user_id=user_id,
                session_id=session_id,
                actor_id=actor_id,
                role=role,
                role_id=role_id,
                metadata=additional_metadata if additional_metadata else None,
                original_text=original_text,
                created_at=created_at
            )
        elif event == "UPDATE":
            # Update existing memory record
            self.mysql_db.update_memory(
                memory_id=memory_id,
                memory_text=data,
                metadata=additional_metadata if additional_metadata else None,
                updated_at=updated_at
            )
        
        # Add history record
        self.mysql_db.add_history(
            memory_id=memory_id,
            old_memory=prev_value,
            new_memory=data,
            event=event,
            created_at=created_at,
            updated_at=updated_at,
            actor_id=actor_id,
            role=role
        )
    
    def _sync_memory_deletion_to_mysql(self, memory_id, prev_value=None):
        """Sync memory deletion to MySQL"""
        # Delete the memory record
        self.mysql_db.delete_memory(memory_id)
        
        # Add history record for deletion
        self.mysql_db.add_history(
            memory_id=memory_id,
            old_memory=prev_value,
            new_memory=None,
            event="DELETE",
            is_deleted=1
        )
    
    def get_mysql_memories(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ):
        """Get memories directly from MySQL"""
        try:
            return self.mysql_db.get_all_memories(
                user_id=user_id,
                session_id=session_id,
                actor_id=actor_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get memories from MySQL: {e}")
            return []
    
    def get_mysql_memory(self, memory_id: str):
        """Get a specific memory from MySQL"""
        try:
            return self.mysql_db.get_memory(memory_id)
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id} from MySQL: {e}")
            return None
    
    def get_mysql_history(self, memory_id: str):
        """Get memory history from MySQL"""
        try:
            return self.mysql_db.get_history(memory_id)
        except Exception as e:
            logger.error(f"Failed to get history for memory {memory_id} from MySQL: {e}")
            return []
    
    def sync_existing_memories_to_mysql(self):
        """
        Sync all existing memories from vector store to MySQL.
        Useful for migrating existing data.
        """
        logger.info("Starting sync of existing memories to MySQL...")
        
        try:
            # Get all memories from vector store
            memories = self.vector_store.list()
            if isinstance(memories, tuple):
                memories = memories[0]
            
            synced_count = 0
            for memory in memories:
                try:
                    # Extract memory data
                    memory_id = memory.id
                    data = memory.payload.get("data", "")
                    metadata = memory.payload
                    original_text = metadata.get("original_text")
                    
                    # Sync to MySQL
                    self._sync_memory_to_mysql(memory_id, data, metadata, original_text, "ADD")
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync memory {memory.id}: {e}")
                    continue
            
            logger.info(f"Successfully synced {synced_count} memories to MySQL")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync existing memories to MySQL: {e}")
            return 0
    
    def reset(self):
        """Reset both vector store and MySQL"""
        super().reset()
        try:
            self.mysql_db.reset()
            logger.info("MySQL storage reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset MySQL storage: {e}")
    
    def get_all_with_roles(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ):
        """获取包含角色信息的记忆列表"""
        try:
            # 使用JOIN查询获取记忆和角色信息
            query = """
            SELECT 
                m.id, m.memory_text, m.user_id, m.session_id, m.actor_id, 
                m.role, m.role_id, m.metadata, m.original_text, 
                m.created_at, m.updated_at,
                r.name as role_name
            FROM memory m
            LEFT JOIN role r ON m.role_id = r.id
            WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND m.user_id = %s"
                params.append(user_id)
            if session_id:
                query += " AND m.session_id = %s"
                params.append(session_id)
            if actor_id:
                query += " AND m.actor_id = %s"
                params.append(actor_id)
                
            query += " ORDER BY m.created_at DESC LIMIT %s"
            params.append(limit)
            
            results = self.mysql_db._execute_query(query, tuple(params), fetch=True)
            
            formatted_results = []
            for row in results:
                memory_item = {
                    "id": row["id"],
                    "memory": row["memory_text"],
                    "text": row["memory_text"],  # 使用清理后的文本
                    "hash": None,  # 暂时设为None，因为我们移除了hash字段
                    "metadata": row["metadata"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "user_id": row["user_id"],
                    "session_id": row["session_id"],  # 直接使用数据库中的session_id，不再自动生成
                    "role_id": row["role_id"],
                    "role_name": row["role_name"]
                }
                
                # 解析metadata JSON
                if row["metadata"]:
                    import json
                    try:
                        memory_item["metadata"] = json.loads(row["metadata"])
                    except:
                        memory_item["metadata"] = {}
                else:
                    memory_item["metadata"] = {}
                    
                formatted_results.append(memory_item)
            
            return {"results": formatted_results}
            
        except Exception as e:
            logger.error(f"Error getting memories with roles: {e}")
            return {"results": []}

    def close(self):
        """Close database connections"""
        try:
            self.mysql_db.close()
            self.role_manager.close()
        except Exception as e:
            logger.error(f"Error closing MySQL connection: {e}")
        
        # Close parent resources
        if hasattr(self.db, 'close'):
            self.db.close()
    
    def __del__(self):
        self.close()