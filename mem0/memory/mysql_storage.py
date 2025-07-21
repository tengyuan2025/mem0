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


class MySQLManager:
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
        self._create_memory_table()
        self._create_history_table()
        self._create_audio_table()

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

    def _create_memory_table(self) -> None:
        """Create the memory table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS memory (
            id VARCHAR(36) PRIMARY KEY,
            memory_text TEXT NOT NULL,
            user_id VARCHAR(255),
            session_id VARCHAR(50),
            actor_id VARCHAR(255),
            role VARCHAR(50),
            role_id INT,
            metadata JSON,
            original_text TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            INDEX idx_user_id (user_id),
            INDEX idx_session_id (session_id),
            INDEX idx_actor_id (actor_id),
            INDEX idx_role_id (role_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self._execute_query(create_table_query)
            logger.info("Memory table created successfully")
        except Error as e:
            logger.error(f"Error creating memory table: {e}")
            raise

    def _create_history_table(self) -> None:
        """Create the history table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS memory_history (
            id VARCHAR(36) PRIMARY KEY,
            memory_id VARCHAR(36),
            old_memory TEXT,
            new_memory TEXT,
            event VARCHAR(10),
            created_at DATETIME,
            updated_at DATETIME,
            is_deleted TINYINT(1) DEFAULT 0,
            actor_id VARCHAR(255),
            role VARCHAR(50),
            INDEX idx_memory_id (memory_id),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (memory_id) REFERENCES memory(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self._execute_query(create_table_query)
            logger.info("Memory history table created successfully")
        except Error as e:
            logger.error(f"Error creating history table: {e}")
            raise

    def _create_audio_table(self) -> None:
        """Create the audio table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS audio (
            id VARCHAR(36) PRIMARY KEY,
            memory_id VARCHAR(36),
            audio_path VARCHAR(500),
            audio_url VARCHAR(500),
            file_size BIGINT,
            duration FLOAT,
            format VARCHAR(20),
            voice_hash VARCHAR(255),
            user_id VARCHAR(255),
            session_id VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_memory_id (memory_id),
            INDEX idx_voice_hash (voice_hash),
            INDEX idx_user_id (user_id),
            INDEX idx_session_id (session_id),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (memory_id) REFERENCES memory(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self._execute_query(create_table_query)
            logger.info("Audio table created successfully")
        except Error as e:
            logger.error(f"Error creating audio table: {e}")
            raise

    def add_memory(
        self,
        memory_id: str,
        memory_text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
        role_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        original_text: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> None:
        """Add a new memory record"""
        if created_at is None:
            created_at = datetime.now(pytz.timezone("US/Pacific")).strftime('%Y-%m-%d %H:%M:%S')
        
        insert_query = """
        INSERT INTO memory (
            id, memory_text, user_id, session_id, 
            actor_id, role, role_id, metadata, original_text, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        try:
            self._execute_query(insert_query, (
                memory_id, memory_text, user_id, session_id,
                actor_id, role, role_id, metadata_json, original_text, created_at
            ))
            logger.debug(f"Added memory to MySQL: {memory_id}")
        except Error as e:
            logger.error(f"Error adding memory to MySQL: {e}")
            raise

    def update_memory(
        self,
        memory_id: str,
        memory_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        """Update an existing memory record"""
        if updated_at is None:
            updated_at = datetime.now(pytz.timezone("US/Pacific")).strftime('%Y-%m-%d %H:%M:%S')
        
        update_query = """
        UPDATE memory 
        SET memory_text = %s, metadata = %s, updated_at = %s
        WHERE id = %s
        """
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        try:
            self._execute_query(update_query, (
                memory_text, metadata_json, updated_at, memory_id
            ))
            logger.debug(f"Updated memory in MySQL: {memory_id}")
        except Error as e:
            logger.error(f"Error updating memory in MySQL: {e}")
            raise

    def delete_memory(self, memory_id: str) -> None:
        """Delete a memory record"""
        delete_query = "DELETE FROM memory WHERE id = %s"
        
        try:
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
                memory = result[0]
                if memory['metadata']:
                    memory['metadata'] = json.loads(memory['metadata'])
                return memory
            return None
        except Error as e:
            logger.error(f"Error getting memory from MySQL: {e}")
            raise

    def get_all_memories(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get all memories with optional filtering"""
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("user_id = %s")
            params.append(user_id)
        if session_id:
            where_conditions.append("session_id = %s")
            params.append(session_id)
        if actor_id:
            where_conditions.append("actor_id = %s")
            params.append(actor_id)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        select_query = f"""
        SELECT * FROM memory 
        {where_clause}
        ORDER BY created_at DESC 
        LIMIT %s
        """
        params.append(limit)
        
        try:
            result = self._execute_query(select_query, tuple(params), fetch=True)
            memories = []
            for memory in result:
                if memory['metadata']:
                    memory['metadata'] = json.loads(memory['metadata'])
                memories.append(memory)
            return memories
        except Error as e:
            logger.error(f"Error getting all memories from MySQL: {e}")
            raise

    def add_history(
        self,
        memory_id: str,
        old_memory: Optional[str],
        new_memory: Optional[str],
        event: str,
        *,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        is_deleted: int = 0,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        """Add a history record"""
        insert_query = """
        INSERT INTO memory_history (
            id, memory_id, old_memory, new_memory, event,
            created_at, updated_at, is_deleted, actor_id, role
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            self._execute_query(insert_query, (
                str(uuid.uuid4()), memory_id, old_memory, new_memory, event,
                created_at, updated_at, is_deleted, actor_id, role
            ))
        except Error as e:
            logger.error(f"Error adding history record to MySQL: {e}")
            raise

    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get history records for a memory"""
        select_query = """
        SELECT id, memory_id, old_memory, new_memory, event,
               created_at, updated_at, is_deleted, actor_id, role
        FROM memory_history
        WHERE memory_id = %s
        ORDER BY created_at ASC, updated_at ASC
        """
        
        try:
            result = self._execute_query(select_query, (memory_id,), fetch=True)
            return [
                {
                    "id": r["id"],
                    "memory_id": r["memory_id"],
                    "old_memory": r["old_memory"],
                    "new_memory": r["new_memory"],
                    "event": r["event"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "is_deleted": bool(r["is_deleted"]),
                    "actor_id": r["actor_id"],
                    "role": r["role"],
                }
                for r in result
            ]
        except Error as e:
            logger.error(f"Error getting history from MySQL: {e}")
            raise

    def reset(self) -> None:
        """Drop and recreate tables"""
        try:
            self._execute_query("DROP TABLE IF EXISTS audio")
            self._execute_query("DROP TABLE IF EXISTS memory_history")
            self._execute_query("DROP TABLE IF EXISTS memory")
            self._create_memory_table()
            self._create_history_table()
            self._create_audio_table()
            logger.info("MySQL tables reset successfully")
        except Error as e:
            logger.error(f"Error resetting MySQL tables: {e}")
            raise

    def add_audio(
        self,
        audio_id: str,
        memory_id: str,
        audio_path: Optional[str] = None,
        audio_url: Optional[str] = None,
        file_size: Optional[int] = None,
        duration: Optional[float] = None,
        format: Optional[str] = None,
        voice_hash: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Add an audio record"""
        insert_query = """
        INSERT INTO audio (
            id, memory_id, audio_path, audio_url, file_size, 
            duration, format, voice_hash, user_id, session_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            self._execute_query(insert_query, (
                audio_id, memory_id, audio_path, audio_url, file_size,
                duration, format, voice_hash, user_id, session_id
            ))
            logger.debug(f"Added audio record to MySQL: {audio_id}")
        except Error as e:
            logger.error(f"Error adding audio record to MySQL: {e}")
            raise

    def get_audio_by_memory_id(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get audio records by memory ID"""
        select_query = "SELECT * FROM audio WHERE memory_id = %s ORDER BY created_at ASC"
        
        try:
            result = self._execute_query(select_query, (memory_id,), fetch=True)
            return result or []
        except Error as e:
            logger.error(f"Error getting audio records from MySQL: {e}")
            raise

    def close(self) -> None:
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

    def __del__(self):
        self.close()