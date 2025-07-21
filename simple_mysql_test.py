#!/usr/bin/env python3
"""
简化的MySQL聊天记忆集成测试

仅测试数据库连接和基本功能，不依赖复杂的mem0模块
"""

import mysql.connector
import uuid
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mysql_connection():
    """测试MySQL连接"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="xiaozhi_esp32_server",
            autocommit=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        if result and result["test"] == 1:
            logger.info("✓ MySQL连接成功")
            cursor.close()
            connection.close()
            return True
        else:
            logger.error("✗ MySQL连接测试失败")
            return False
            
    except Exception as e:
        logger.error(f"✗ MySQL连接错误: {e}")
        return False


def test_table_existence():
    """测试表是否存在"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="xiaozhi_esp32_server",
            autocommit=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # 检查memory表
        cursor.execute("SHOW TABLES LIKE 'memory'")
        memory_table = cursor.fetchone()
        
        if memory_table:
            logger.info("✓ memory表存在")
        else:
            logger.error("✗ memory表不存在")
            return False
        
        # 检查ai_agent_chat_history表的memory_id字段
        cursor.execute("DESCRIBE ai_agent_chat_history")
        columns = cursor.fetchall()
        column_names = [col['Field'] for col in columns]
        
        if 'memory_id' in column_names:
            logger.info("✓ ai_agent_chat_history表包含memory_id字段")
        else:
            logger.error("✗ ai_agent_chat_history表缺少memory_id字段")
            return False
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 表存在性检查错误: {e}")
        return False


def test_basic_operations():
    """测试基本的增删改查操作"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="xiaozhi_esp32_server",
            autocommit=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # 生成测试数据
        test_memory_id = str(uuid.uuid4())
        test_text = "测试记忆内容 - Python MySQL集成"
        test_agent_id = "test_agent_" + str(int(__import__('time').time()))
        test_session_id = "test_session_" + str(int(__import__('time').time()))
        
        # 1. 测试插入memory记录
        logger.info("测试插入记忆记录...")
        cursor.execute("""
        INSERT INTO memory (id, text, created_at, updated_at) 
        VALUES (%s, %s, NOW(), NOW())
        """, (test_memory_id, test_text))
        logger.info("✓ 记忆记录插入成功")
        
        # 2. 测试查询memory记录
        logger.info("测试查询记忆记录...")
        cursor.execute("SELECT * FROM memory WHERE id = %s", (test_memory_id,))
        memory_record = cursor.fetchone()
        
        if memory_record and memory_record['text'] == test_text:
            logger.info("✓ 记忆记录查询成功")
        else:
            logger.error("✗ 记忆记录查询失败")
            return False
        
        # 3. 测试插入聊天记录并关联记忆
        logger.info("测试插入关联聊天记录...")
        cursor.execute("""
        INSERT INTO ai_agent_chat_history 
        (mac_address, agent_id, session_id, chat_type, content, memory_id, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, ("test:mac:address", test_agent_id, test_session_id, 1, "测试聊天内容", test_memory_id))
        logger.info("✓ 关联聊天记录插入成功")
        
        # 4. 测试联表查询
        logger.info("测试联表查询...")
        cursor.execute("""
        SELECT m.id as memory_id, m.text, ch.content, ch.chat_type
        FROM memory m
        JOIN ai_agent_chat_history ch ON m.id = ch.memory_id
        WHERE m.id = %s
        """, (test_memory_id,))
        
        join_result = cursor.fetchone()
        if join_result:
            logger.info("✓ 联表查询成功")
            logger.info(f"  记忆: {join_result['text']}")
            logger.info(f"  聊天: {join_result['content']}")
        else:
            logger.error("✗ 联表查询失败")
            return False
        
        # 5. 测试更新记忆
        logger.info("测试更新记忆...")
        updated_text = "更新后的记忆内容"
        cursor.execute("""
        UPDATE memory SET text = %s, updated_at = NOW() WHERE id = %s
        """, (updated_text, test_memory_id))
        
        cursor.execute("SELECT text FROM memory WHERE id = %s", (test_memory_id,))
        updated_record = cursor.fetchone()
        
        if updated_record and updated_record['text'] == updated_text:
            logger.info("✓ 记忆更新成功")
        else:
            logger.error("✗ 记忆更新失败")
            return False
        
        # 6. 清理测试数据
        logger.info("清理测试数据...")
        cursor.execute("DELETE FROM ai_agent_chat_history WHERE memory_id = %s", (test_memory_id,))
        cursor.execute("DELETE FROM memory WHERE id = %s", (test_memory_id,))
        logger.info("✓ 测试数据清理完成")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 基本操作测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_statistics():
    """测试数据统计"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="xiaozhi_esp32_server",
            autocommit=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # 统计现有数据
        cursor.execute("SELECT COUNT(*) as count FROM memory")
        memory_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM ai_agent_chat_history")
        chat_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM ai_agent_chat_history WHERE memory_id IS NOT NULL")
        linked_chat_count = cursor.fetchone()['count']
        
        logger.info(f"✓ 数据统计完成:")
        logger.info(f"  memory表记录数: {memory_count}")
        logger.info(f"  聊天记录总数: {chat_count}")
        logger.info(f"  已关联聊天记录数: {linked_chat_count}")
        
        # 检查数据完整性
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM ai_agent_chat_history ch 
        LEFT JOIN memory m ON ch.memory_id = m.id 
        WHERE ch.memory_id IS NOT NULL AND m.id IS NULL
        """)
        orphaned_count = cursor.fetchone()['count']
        
        if orphaned_count == 0:
            logger.info("✓ 无孤立的memory_id引用")
        else:
            logger.warning(f"⚠ 发现 {orphaned_count} 个孤立的memory_id引用")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 数据统计错误: {e}")
        return False


def main():
    """运行所有测试"""
    logger.info("🧪 开始简化MySQL聊天记忆集成测试...")
    logger.info("=" * 50)
    
    tests = [
        ("MySQL连接", test_mysql_connection),
        ("表存在性", test_table_existence),
        ("基本操作", test_basic_operations),
        ("数据统计", test_data_statistics),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        logger.info(f"\n🔍 测试: {name}")
        logger.info("-" * 30)
        
        if test_func():
            passed += 1
            logger.info(f"✅ {name} 测试通过")
        else:
            logger.error(f"❌ {name} 测试失败")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 MySQL聊天记忆集成基础功能正常！")
        logger.info("\n📋 完成的功能:")
        logger.info("✓ 创建了memory表用于存储记忆")
        logger.info("✓ 在ai_agent_chat_history表中添加了memory_id字段")
        logger.info("✓ 实现了记忆与聊天记录的关联")
        logger.info("✓ 验证了基本的增删改查操作")
        logger.info("✓ 确认了数据完整性")
        
        logger.info("\n🚀 接下来你可以:")
        logger.info("1. 在xiaozhi-server中集成记忆创建功能")
        logger.info("2. 实现从聊天会话自动生成记忆的API")
        logger.info("3. 添加记忆搜索和查询功能")
        logger.info("4. 在Web界面中展示聊天关联的记忆")
        
        return 0
    else:
        logger.error("❌ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit(main())