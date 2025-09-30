#!/usr/bin/env python3
"""
数据库初始化脚本
用于初始化阿里云RDS MySQL数据库的表结构
"""

import os
import asyncio
import aiomysql
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def init_database():
    """初始化数据库和表结构"""
    
    # 数据库配置
    config = {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'port': int(os.getenv('DATABASE_PORT', 3306)),
        'user': os.getenv('DATABASE_USER', 'root'),
        'password': os.getenv('DATABASE_PASSWORD', ''),
        'charset': 'utf8mb4'
    }
    
    db_name = os.getenv('DATABASE_NAME', 'mem0')
    
    logger.info(f"开始初始化数据库: {config['host']}:{config['port']}")
    
    try:
        # 直接连接到指定数据库（阿里云RDS数据库已预先创建）
        config['db'] = db_name
        logger.info(f"连接到数据库: {db_name}")
        conn = await aiomysql.connect(**config)
        
        try:
            async with conn.cursor() as cursor:
                
                # 创建用户记忆表
                logger.info("创建用户记忆表...")
                await cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_memories (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    agent_id VARCHAR(255),
                    run_id VARCHAR(255),
                    memory_id VARCHAR(255),
                    memory_content TEXT NOT NULL,
                    memory_type VARCHAR(50) DEFAULT 'episodic',
                    importance_score FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    metadata JSON,
                    INDEX idx_user_id (user_id),
                    INDEX idx_agent_id (agent_id),
                    INDEX idx_run_id (run_id),
                    INDEX idx_memory_id (memory_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_importance (importance_score)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 创建对话历史表
                logger.info("创建对话历史表...")
                await cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    agent_id VARCHAR(255),
                    run_id VARCHAR(255),
                    session_id VARCHAR(255),
                    role ENUM('user', 'assistant', 'system') NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON,
                    INDEX idx_user_id (user_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 创建向量嵌入表（如果需要）
                logger.info("创建向量嵌入表...")
                await cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_embeddings (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    memory_id VARCHAR(255) NOT NULL,
                    embedding_vector JSON NOT NULL,
                    model_name VARCHAR(255) NOT NULL,
                    dimension INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_memory_id (memory_id),
                    INDEX idx_model (model_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                await conn.commit()
                logger.info("✅ 数据库初始化完成！")
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

async def test_connection():
    """测试数据库连接"""
    config = {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'port': int(os.getenv('DATABASE_PORT', 3306)),
        'user': os.getenv('DATABASE_USER', 'root'),
        'password': os.getenv('DATABASE_PASSWORD', ''),
        'db': os.getenv('DATABASE_NAME', 'mem0'),
        'charset': 'utf8mb4'
    }
    
    try:
        conn = await aiomysql.connect(**config)
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
            logger.info(f"✅ 数据库连接成功！MySQL版本: {version[0]}")
            
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            logger.info(f"📋 数据库表: {[table[0] for table in tables]}")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        raise

if __name__ == "__main__":
    async def main():
        logger.info("🚀 开始数据库初始化...")
        await init_database()
        await test_connection()
        logger.info("🎉 数据库初始化和测试完成！")
    
    asyncio.run(main())