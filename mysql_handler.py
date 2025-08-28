"""
MySQL数据库处理模块
用于将记忆数据同步存储到MySQL数据库
"""

import aiomysql
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
import json


class MySQLHandler:
    """MySQL数据库处理器"""
    
    def __init__(self):
        self.pool = None
        self.initialized = False
        
    async def initialize(self):
        """初始化MySQL连接池"""
        if self.initialized:
            return
            
        try:
            # 先连接到MySQL服务器（不指定数据库）来创建数据库
            temp_pool = await aiomysql.create_pool(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', '123456'),
                charset='utf8mb4',
                autocommit=True,
                minsize=1,
                maxsize=10
            )
            
            # 创建数据库（如果不存在）
            await self._ensure_database_with_pool(temp_pool)
            
            # 关闭临时连接池
            temp_pool.close()
            await temp_pool.wait_closed()
            
            # 创建连接到指定数据库的连接池
            self.pool = await aiomysql.create_pool(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', '123456'),
                db=os.getenv('MYSQL_DATABASE', 'mem0'),
                charset='utf8mb4',
                autocommit=True,
                minsize=1,
                maxsize=10
            )
            
            # 创建表（如果不存在）
            await self._ensure_table()
            
            self.initialized = True
            logger.info("MySQL连接池初始化成功")
            
        except Exception as e:
            logger.error(f"MySQL连接池初始化失败: {e}")
            raise
    
    async def _ensure_database_with_pool(self, pool):
        """使用指定连接池确保数据库存在"""
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 创建数据库（如果不存在）
                    db_name = os.getenv('MYSQL_DATABASE', 'mem0')
                    await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"确保数据库 {db_name} 存在")
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            raise

    async def _ensure_database(self):
        """确保数据库存在（使用当前连接池）"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 创建数据库（如果不存在）
                    db_name = os.getenv('MYSQL_DATABASE', 'mem0')
                    await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    await cursor.execute(f"USE {db_name}")
                    logger.info(f"确保数据库 {db_name} 存在")
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            raise
    
    async def _ensure_table(self):
        """确保memory表存在"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 创建memory表
                    create_table_sql = """
                    CREATE TABLE IF NOT EXISTS memory (
                        id BIGINT AUTO_INCREMENT COMMENT 'id',
                        memory_id VARCHAR(255) NOT NULL COMMENT '记忆ID',
                        session_id BIGINT COMMENT '会话id',
                        user_id VARCHAR(255) NOT NULL COMMENT '用户id',
                        event VARCHAR(1000) COMMENT '事件',
                        time DATETIME COMMENT '事件发生的时间',
                        knowledge VARCHAR(1000) COMMENT '知识',
                        skill VARCHAR(1000) COMMENT '技能',
                        content TEXT COMMENT '记忆内容',
                        metadata JSON COMMENT '元数据',
                        embedding_provider VARCHAR(100) COMMENT 'Embedding提供者',
                        llm_provider VARCHAR(100) COMMENT 'LLM提供者',
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        PRIMARY KEY (id),
                        INDEX idx_memory_id (memory_id),
                        INDEX idx_user_id (user_id),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='记忆';
                    """
                    await cursor.execute(create_table_sql)
                    logger.info("memory表结构确认完成")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            raise
    
    async def insert_memory(self, 
                          memory_id: str,
                          user_id: str,
                          content: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          event: Optional[str] = None,
                          knowledge: Optional[str] = None,
                          skill: Optional[str] = None,
                          session_id: Optional[int] = None) -> int:
        """插入记忆到MySQL"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 准备数据
                    metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
                    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "dashscope")
                    llm_provider = os.getenv("LLM_PROVIDER", "dashscope")
                    
                    # 从content中智能提取event、knowledge和skill（如果未提供）
                    if not event and not knowledge and not skill:
                        event, knowledge, skill = await self._extract_memory_components(content)
                    
                    # 插入数据
                    insert_sql = """
                    INSERT INTO memory (
                        memory_id, user_id, content, metadata, 
                        event, knowledge, skill, session_id,
                        time, embedding_provider, llm_provider, 
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, 
                        %s, %s, %s, %s,
                        %s, %s, %s, 
                        %s, %s
                    )
                    """
                    
                    now = datetime.now()
                    values = (
                        memory_id, user_id, content, metadata_json,
                        event, knowledge, skill, session_id,
                        now, embedding_provider, llm_provider,
                        now, now
                    )
                    
                    await cursor.execute(insert_sql, values)
                    
                    # 获取插入的ID
                    last_id = cursor.lastrowid
                    
                    logger.info(f"记忆已存储到MySQL, ID: {last_id}, memory_id: {memory_id}")
                    return last_id
                    
        except Exception as e:
            logger.error(f"插入记忆到MySQL失败: {e}")
            raise
    
    async def update_memory(self, 
                          memory_id: str,
                          content: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          event: Optional[str] = None,
                          knowledge: Optional[str] = None,
                          skill: Optional[str] = None) -> bool:
        """更新MySQL中的记忆"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 构建更新语句
                    update_parts = []
                    values = []
                    
                    if content is not None:
                        update_parts.append("content = %s")
                        values.append(content)
                    
                    if metadata is not None:
                        update_parts.append("metadata = %s")
                        values.append(json.dumps(metadata, ensure_ascii=False))
                    
                    if event is not None:
                        update_parts.append("event = %s")
                        values.append(event)
                    
                    if knowledge is not None:
                        update_parts.append("knowledge = %s")
                        values.append(knowledge)
                    
                    if skill is not None:
                        update_parts.append("skill = %s")
                        values.append(skill)
                    
                    if not update_parts:
                        return False
                    
                    # 添加更新时间
                    update_parts.append("updated_at = %s")
                    values.append(datetime.now())
                    
                    # 添加where条件
                    values.append(memory_id)
                    
                    update_sql = f"""
                    UPDATE memory 
                    SET {', '.join(update_parts)}
                    WHERE memory_id = %s
                    """
                    
                    await cursor.execute(update_sql, values)
                    affected_rows = cursor.rowcount
                    
                    logger.info(f"MySQL记忆更新完成, memory_id: {memory_id}, 影响行数: {affected_rows}")
                    return affected_rows > 0
                    
        except Exception as e:
            logger.error(f"更新MySQL记忆失败: {e}")
            raise
    
    async def delete_memory(self, memory_id: Optional[str] = None, user_id: Optional[str] = None) -> int:
        """从MySQL删除记忆"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if memory_id:
                        # 删除特定记忆
                        delete_sql = "DELETE FROM memory WHERE memory_id = %s"
                        await cursor.execute(delete_sql, (memory_id,))
                    elif user_id:
                        # 删除用户的所有记忆
                        delete_sql = "DELETE FROM memory WHERE user_id = %s"
                        await cursor.execute(delete_sql, (user_id,))
                    else:
                        return 0
                    
                    affected_rows = cursor.rowcount
                    
                    logger.info(f"MySQL记忆删除完成, 影响行数: {affected_rows}")
                    return affected_rows
                    
        except Exception as e:
            logger.error(f"从MySQL删除记忆失败: {e}")
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """从MySQL获取单个记忆"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    select_sql = """
                    SELECT * FROM memory WHERE memory_id = %s
                    """
                    await cursor.execute(select_sql, (memory_id,))
                    result = await cursor.fetchone()
                    
                    if result and result.get('metadata'):
                        # 解析JSON字段
                        result['metadata'] = json.loads(result['metadata'])
                    
                    return result
                    
        except Exception as e:
            logger.error(f"从MySQL获取记忆失败: {e}")
            raise
    
    async def get_user_memories(self, 
                               user_id: str, 
                               limit: int = 100,
                               offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户的所有记忆"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    select_sql = """
                    SELECT * FROM memory 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                    """
                    await cursor.execute(select_sql, (user_id, limit, offset))
                    results = await cursor.fetchall()
                    
                    # 解析JSON字段
                    for result in results:
                        if result.get('metadata'):
                            result['metadata'] = json.loads(result['metadata'])
                    
                    return results
                    
        except Exception as e:
            logger.error(f"从MySQL获取用户记忆失败: {e}")
            raise
    
    async def _extract_memory_components(self, content: str) -> tuple:
        """从内容中提取event、knowledge和skill"""
        # 这是一个简单的实现，可以根据需要使用LLM来智能提取
        event = None
        knowledge = None
        skill = None
        
        # 简单的关键词匹配提取
        if "喜欢" in content or "偏好" in content:
            event = "用户偏好记录"
        elif "学会" in content or "掌握" in content:
            skill = content[:100]  # 取前100个字符作为skill
        elif "知道" in content or "了解" in content:
            knowledge = content[:100]  # 取前100个字符作为knowledge
        else:
            event = "一般对话记录"
        
        return event, knowledge, skill
    
    async def search_memories_by_time(self,
                                     user_id: str,
                                     start_time: datetime,
                                     end_time: datetime) -> List[Dict[str, Any]]:
        """按时间范围搜索记忆"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    select_sql = """
                    SELECT * FROM memory 
                    WHERE user_id = %s AND time BETWEEN %s AND %s
                    ORDER BY time DESC
                    """
                    await cursor.execute(select_sql, (user_id, start_time, end_time))
                    results = await cursor.fetchall()
                    
                    # 解析JSON字段
                    for result in results:
                        if result.get('metadata'):
                            result['metadata'] = json.loads(result['metadata'])
                    
                    return results
                    
        except Exception as e:
            logger.error(f"按时间搜索记忆失败: {e}")
            raise
    
    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL连接池已关闭")