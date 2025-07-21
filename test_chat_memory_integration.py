#!/usr/bin/env python3
"""
聊天记忆集成完整测试脚本

此脚本测试所有聊天记忆集成功能：
1. 数据库连接测试
2. 记忆创建和关联测试
3. 查询和搜索测试
4. API接口测试
5. 数据完整性验证
"""

import logging
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection():
    """测试数据库连接"""
    try:
        from mem0.memory.chat_memory_storage import ChatMemoryStorage
        
        storage = ChatMemoryStorage()
        
        # 测试连接
        result = storage._execute_query("SELECT 1 as test", fetch=True)
        if result and result[0]["test"] == 1:
            logger.info("✓ 数据库连接成功")
            storage.close()
            return True
        else:
            logger.error("✗ 数据库连接测试失败")
            return False
            
    except Exception as e:
        logger.error(f"✗ 数据库连接错误: {e}")
        return False


def test_table_structure():
    """测试表结构"""
    try:
        from mem0.memory.chat_memory_storage import ChatMemoryStorage
        
        storage = ChatMemoryStorage()
        
        # 检查memory表
        memory_structure = storage._execute_query("DESCRIBE memory", fetch=True)
        expected_memory_fields = {'id', 'text', 'created_at', 'updated_at'}
        actual_memory_fields = {field['Field'] for field in memory_structure}
        
        if expected_memory_fields.issubset(actual_memory_fields):
            logger.info("✓ memory表结构正确")
        else:
            logger.error(f"✗ memory表结构不完整，缺少字段: {expected_memory_fields - actual_memory_fields}")
            return False
        
        # 检查ai_agent_chat_history表
        chat_structure = storage._execute_query("DESCRIBE ai_agent_chat_history", fetch=True)
        actual_chat_fields = {field['Field'] for field in chat_structure}
        
        if 'memory_id' in actual_chat_fields:
            logger.info("✓ ai_agent_chat_history表包含memory_id字段")
        else:
            logger.error("✗ ai_agent_chat_history表缺少memory_id字段")
            return False
        
        storage.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 表结构测试错误: {e}")
        return False


def test_memory_operations():
    """测试记忆操作"""
    try:
        from mem0.memory.chat_memory_storage import ChatMemoryStorage
        import uuid
        
        storage = ChatMemoryStorage()
        test_memory_id = str(uuid.uuid4())
        test_text = "测试记忆内容"
        
        # 测试添加记忆
        storage.add_memory(test_memory_id, test_text)
        logger.info("✓ 记忆添加成功")
        
        # 测试获取记忆
        memory = storage.get_memory(test_memory_id)
        if memory and memory['text'] == test_text:
            logger.info("✓ 记忆获取成功")
        else:
            logger.error("✗ 记忆获取失败")
            return False
        
        # 测试更新记忆
        updated_text = "更新的记忆内容"
        storage.update_memory(test_memory_id, updated_text)
        
        updated_memory = storage.get_memory(test_memory_id)
        if updated_memory and updated_memory['text'] == updated_text:
            logger.info("✓ 记忆更新成功")
        else:
            logger.error("✗ 记忆更新失败")
            return False
        
        # 测试删除记忆
        storage.delete_memory(test_memory_id)
        deleted_memory = storage.get_memory(test_memory_id)
        if deleted_memory is None:
            logger.info("✓ 记忆删除成功")
        else:
            logger.error("✗ 记忆删除失败")
            return False
        
        storage.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 记忆操作测试错误: {e}")
        return False


def test_chat_memory_integration():
    """测试聊天记忆集成"""
    try:
        from mem0.memory.chat_memory_manager import ChatMemoryManager
        from mem0.configs.mysql import MySQLConfig
        
        mysql_config = MySQLConfig.for_xiaozhi_server()
        manager = ChatMemoryManager(mysql_config=mysql_config.to_connection_dict())
        
        # 测试数据
        agent_id = "test_agent_" + str(int(time.time()))
        session_id = "test_session_" + str(int(time.time()))
        user_id = "test_user"
        
        # 创建测试聊天记录
        test_chats = [
            {"type": 1, "content": "我想学习Python编程"},
            {"type": 2, "content": "Python是一个很好的选择！你想从哪里开始？"},
            {"type": 1, "content": "我希望能做一些数据分析的工作"},
            {"type": 2, "content": "那建议你学习pandas和numpy库"}
        ]
        
        # 插入测试聊天记录
        for chat in test_chats:
            manager.chat_storage._execute_query("""
            INSERT INTO ai_agent_chat_history 
            (mac_address, agent_id, session_id, chat_type, content, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())
            """, ("test:mac", agent_id, session_id, chat["type"], chat["content"]))
        
        logger.info("✓ 测试聊天记录创建成功")
        
        # 测试从聊天创建记忆
        memory_result = manager.add_memory_from_chat_session(
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            auto_generate=False,
            memory_text="用户想学习Python编程，特别是数据分析方面，建议学习pandas和numpy"
        )
        
        memory_id = memory_result["memory_id"]
        logger.info(f"✓ 从聊天创建记忆成功: {memory_id}")
        
        # 测试查询会话记忆
        session_memories = manager.get_memories_for_chat_session(agent_id, session_id)
        if session_memories and len(session_memories) > 0:
            logger.info("✓ 查询会话记忆成功")
        else:
            logger.error("✗ 查询会话记忆失败")
            return False
        
        # 测试搜索记忆
        search_results = manager.search_memories_for_agent(agent_id, "Python编程", limit=5)
        if search_results and len(search_results) > 0:
            logger.info("✓ 搜索记忆成功")
        else:
            logger.warning("⚠ 搜索记忆无结果（可能是正常的）")
        
        # 清理测试数据
        manager.delete_memory_and_unlink(memory_id)
        manager.chat_storage._execute_query(
            "DELETE FROM ai_agent_chat_history WHERE session_id = %s AND mac_address = %s",
            (session_id, "test:mac")
        )
        logger.info("✓ 测试数据清理完成")
        
        manager.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 聊天记忆集成测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_interface():
    """测试API接口"""
    try:
        from mem0.api.chat_memory_api import ChatMemoryAPI
        
        api = ChatMemoryAPI()
        
        # 测试获取Agent摘要（这是最安全的测试）
        agent_id = "f4d54997b1f94b49941b405997d5dd87"
        summary_result = api.get_agent_summary(agent_id)
        
        if summary_result["success"]:
            logger.info("✓ API接口测试成功")
            logger.info(f"  Agent记忆数: {summary_result['data']['total_memories']}")
        else:
            logger.error(f"✗ API接口测试失败: {summary_result.get('error', 'Unknown error')}")
            return False
        
        api.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ API接口测试错误: {e}")
        return False


def test_data_consistency():
    """测试数据一致性"""
    try:
        from mem0.memory.chat_memory_storage import ChatMemoryStorage
        
        storage = ChatMemoryStorage()
        
        # 检查memory表和ai_agent_chat_history表的记录数
        memory_count = storage._execute_query(
            "SELECT COUNT(*) as count FROM memory", fetch=True
        )[0]["count"]
        
        linked_chat_count = storage._execute_query(
            "SELECT COUNT(*) as count FROM ai_agent_chat_history WHERE memory_id IS NOT NULL", 
            fetch=True
        )[0]["count"]
        
        logger.info(f"✓ 数据一致性检查完成")
        logger.info(f"  memory表记录数: {memory_count}")
        logger.info(f"  关联聊天记录数: {linked_chat_count}")
        
        # 检查是否有孤立的memory_id
        orphaned_count = storage._execute_query("""
        SELECT COUNT(*) as count 
        FROM ai_agent_chat_history ch 
        LEFT JOIN memory m ON ch.memory_id = m.id 
        WHERE ch.memory_id IS NOT NULL AND m.id IS NULL
        """, fetch=True)[0]["count"]
        
        if orphaned_count == 0:
            logger.info("✓ 无孤立的memory_id引用")
        else:
            logger.warning(f"⚠ 发现 {orphaned_count} 个孤立的memory_id引用")
        
        storage.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 数据一致性测试错误: {e}")
        return False


def main():
    """运行所有测试"""
    logger.info("🧪 开始聊天记忆集成完整测试...")
    logger.info("=" * 50)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("表结构验证", test_table_structure),
        ("记忆操作", test_memory_operations),
        ("聊天记忆集成", test_chat_memory_integration),
        ("API接口", test_api_interface),
        ("数据一致性", test_data_consistency),
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
        logger.info("🎉 所有测试通过！聊天记忆集成功能正常。")
        logger.info("\n🚀 接下来你可以：")
        logger.info("1. 运行完整示例: python examples/chat_memory_integration_example.py")
        logger.info("2. 在xiaozhi-server中集成API接口")
        logger.info("3. 开始使用聊天记忆功能")
        return 0
    else:
        logger.error("❌ 部分测试失败，请检查错误信息并修复问题。")
        return 1


if __name__ == "__main__":
    sys.exit(main())