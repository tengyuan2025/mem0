#!/usr/bin/env python3
"""
数据库初始化脚本 - 同步版本
用于初始化阿里云RDS MySQL数据库的表结构
使用pymysql，无需额外异步依赖
"""

import os
import pymysql
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def init_database():
    """初始化数据库和表结构"""
    
    # 调试：显示环境变量
    print("==== 数据库初始化脚本调试信息 ====")
    print(f"📋 数据库配置检查:")
    print(f"  DATABASE_HOST = {os.getenv('DATABASE_HOST', '未设置')}")
    print(f"  DATABASE_PORT = {os.getenv('DATABASE_PORT', '未设置')}")
    print(f"  DATABASE_NAME = {os.getenv('DATABASE_NAME', '未设置')}")
    print(f"  DATABASE_USER = {os.getenv('DATABASE_USER', '未设置')}")
    print(f"  DATABASE_PASSWORD = {'已设置' if os.getenv('DATABASE_PASSWORD') else '未设置'}")
    
    # 数据库配置
    config = {
        'host': os.getenv('DATABASE_HOST', os.getenv('MYSQL_HOST', 'localhost')),
        'port': int(os.getenv('DATABASE_PORT', os.getenv('MYSQL_PORT', 3306))),
        'user': os.getenv('DATABASE_USER', os.getenv('MYSQL_USER', 'root')),
        'password': os.getenv('DATABASE_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
        'charset': 'utf8mb4'
    }
    
    db_name = os.getenv('DATABASE_NAME', os.getenv('MYSQL_DATABASE', 'mem0'))
    
    print(f"📋 最终使用的配置:")
    print(f"  host = {config['host']}")
    print(f"  port = {config['port']}")
    print(f"  user = {config['user']}")
    print(f"  password = {'已设置' if config['password'] else '未设置'}")
    print(f"  database = {db_name}")
    print("====================================")
    
    print(f"🗄️ 开始初始化数据库: {config['host']}:{config['port']}")
    
    try:
        # 直接连接到指定数据库（阿里云RDS数据库已预先创建）
        config['database'] = db_name
        print(f"📝 连接到数据库: {db_name}")
        conn = pymysql.connect(**config)
        
        try:
            with conn.cursor() as cursor:
                
                # 创建用户记忆表
                print("📝 创建用户记忆表...")
                cursor.execute("""
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
                print("📝 创建对话历史表...")
                cursor.execute("""
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
                print("📝 创建向量嵌入表...")
                cursor.execute("""
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
                
                conn.commit()
                print("✅ 数据库初始化完成！")
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    return True

def test_connection():
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
        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ 数据库连接成功！MySQL版本: {version[0]}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📋 数据库表: {[table[0] for table in tables]}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始数据库初始化...")
    
    success = init_database()
    if success:
        success = test_connection()
    
    if success:
        print("🎉 数据库初始化和测试完成！")
        sys.exit(0)
    else:
        print("💥 数据库初始化失败！")
        sys.exit(1)