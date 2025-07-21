#!/usr/bin/env python3
"""
聊天记忆集成示例

此示例演示如何将mem0记忆系统与xiaozhi聊天系统集成：
1. 从聊天会话创建记忆
2. 将记忆关联到聊天记录
3. 查询与聊天相关的记忆
4. 搜索Agent的所有记忆

使用前提：
- MySQL服务器运行中
- 数据库'xiaozhi_esp32_server'存在
- memory表和ai_agent_chat_history表已创建
"""

import logging
import sys
from pathlib import Path

# Add the mem0 directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mem0.memory.chat_memory_manager import ChatMemoryManager
from mem0.configs.base import MemoryConfig
from mem0.configs.mysql import MySQLConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主示例函数"""
    
    # MySQL配置 (xiaozhi-server配置)
    mysql_config = MySQLConfig.for_xiaozhi_server(
        host="localhost",
        password="123456"
    )
    
    # mem0配置
    memory_config = MemoryConfig()
    
    try:
        # 初始化聊天记忆管理器
        logger.info("初始化聊天记忆管理器...")
        manager = ChatMemoryManager(
            config=memory_config,
            mysql_config=mysql_config.to_connection_dict()
        )
        logger.info("✓ 成功连接到MySQL并初始化mem0")
        
        # 测试数据 - 使用您提供的真实ID
        agent_id = "f4d54997b1f94b49941b405997d5dd87"
        session_id = "test-session-" + str(int(__import__('time').time()))
        user_id = "test_user_001"
        
        logger.info(f"\n=== 测试数据 ===")
        logger.info(f"Agent ID: {agent_id}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"User ID: {user_id}")
        
        # 1. 模拟一些聊天记录（在实际使用中，这些记录会由xiaozhi-server创建）
        logger.info(f"\n=== 1. 模拟创建聊天记录 ===")
        chat_data = [
            {"type": 1, "content": "我喜欢在周末打篮球"},
            {"type": 2, "content": "那太好了！运动对健康很有益。你通常在哪里打篮球？"},
            {"type": 1, "content": "我经常去市体育馆，那里有很好的室内球场"},
            {"type": 2, "content": "市体育馆是个不错的选择。你打篮球多长时间了？"},
            {"type": 1, "content": "差不多5年了，我最喜欢的位置是控球后卫"}
        ]
        
        # 插入模拟聊天记录
        for i, chat in enumerate(chat_data):
            try:
                manager.chat_storage._execute_query("""
                INSERT INTO ai_agent_chat_history 
                (mac_address, agent_id, session_id, chat_type, content, created_at) 
                VALUES (%s, %s, %s, %s, %s, NOW())
                """, ("test:mac:address", agent_id, session_id, chat["type"], chat["content"]))
                logger.info(f"  ✓ 插入聊天记录 {i+1}: {chat['content'][:30]}...")
            except Exception as e:
                logger.warning(f"  插入聊天记录失败 (可能已存在): {e}")
        
        # 2. 从聊天会话创建记忆
        logger.info(f"\n=== 2. 从聊天会话创建记忆 ===")
        try:
            memory_result = manager.add_memory_from_chat_session(
                agent_id=agent_id,
                session_id=session_id,
                user_id=user_id,
                auto_generate=True  # 自动生成记忆文本
            )
            
            memory_id = memory_result["memory_id"]
            logger.info(f"  ✓ 成功创建记忆: {memory_id}")
            logger.info(f"  记忆内容: {memory_result['memory_text'][:100]}...")
            logger.info(f"  关联聊天记录数: {memory_result['linked_chat_count']}")
            
        except Exception as e:
            logger.error(f"  ✗ 创建记忆失败: {e}")
            return 1
        
        # 3. 查询与聊天会话相关的记忆
        logger.info(f"\n=== 3. 查询会话关联的记忆 ===")
        try:
            session_memories = manager.get_memories_for_chat_session(agent_id, session_id)
            logger.info(f"  找到 {len(session_memories)} 个关联记忆:")
            
            for memory in session_memories:
                logger.info(f"    - {memory['id'][:8]}...: {memory['text'][:50]}...")
                
        except Exception as e:
            logger.error(f"  ✗ 查询会话记忆失败: {e}")
        
        # 4. 搜索Agent的记忆
        logger.info(f"\n=== 4. 搜索Agent记忆 ===")
        try:
            search_query = "篮球运动"
            search_results = manager.search_memories_for_agent(
                agent_id=agent_id,
                query=search_query,
                limit=5
            )
            
            logger.info(f"  搜索'{search_query}'找到 {len(search_results)} 个结果:")
            for result in search_results:
                logger.info(f"    - {result['id'][:8]}...: {result['memory'][:50]}... (score: {result.get('score', 'N/A')})")
                logger.info(f"      关联聊天数: {result['linked_chat_count']}, 会话: {result['chat_sessions']}")
                
        except Exception as e:
            logger.error(f"  ✗ 搜索记忆失败: {e}")
        
        # 5. 获取Agent记忆统计
        logger.info(f"\n=== 5. Agent记忆统计 ===")
        try:
            summary = manager.get_agent_memory_summary(agent_id)
            logger.info(f"  Agent: {summary['agent_id']}")
            logger.info(f"  总记忆数: {summary['total_memories']}")
            logger.info(f"  有记忆的会话数: {summary['sessions_with_memories']}")
            logger.info(f"  关联聊天记录数: {summary['total_linked_chats']}")
            logger.info(f"  存储状态: {'健康' if summary['memory_storage_healthy'] else '异常'}")
            
        except Exception as e:
            logger.error(f"  ✗ 获取统计失败: {e}")
        
        # 6. 测试记忆更新和同步
        logger.info(f"\n=== 6. 测试记忆更新 ===")
        try:
            updated_text = "用户喜欢在周末打篮球，主要在市体育馆的室内球场，擅长控球后卫位置，已经练习5年了。"
            update_result = manager.update_memory_and_sync(memory_id, updated_text)
            logger.info(f"  ✓ 记忆更新成功: {update_result['message']}")
            
        except Exception as e:
            logger.error(f"  ✗ 记忆更新失败: {e}")
        
        # 7. 验证数据完整性
        logger.info(f"\n=== 7. 数据完整性验证 ===")
        try:
            # 检查memory表
            memory_record = manager.chat_storage.get_memory(memory_id)
            if memory_record:
                logger.info(f"  ✓ memory表记录存在: {memory_record['id']}")
            else:
                logger.warning(f"  ⚠ memory表记录不存在")
            
            # 检查聊天记录关联
            linked_chats = manager.chat_storage.get_chat_records_by_memory(memory_id)
            logger.info(f"  ✓ 关联聊天记录数: {len(linked_chats)}")
            
            # 检查mem0记忆
            mem0_memory = manager.get(memory_id)
            if mem0_memory:
                logger.info(f"  ✓ mem0记忆存在: {mem0_memory['id']}")
            else:
                logger.warning(f"  ⚠ mem0记忆不存在")
                
        except Exception as e:
            logger.error(f"  ✗ 数据验证失败: {e}")
        
        # 8. 清理测试数据（可选）
        logger.info(f"\n=== 8. 清理选项 ===")
        cleanup = input("是否清理测试数据？(y/N): ").lower().strip()
        
        if cleanup == 'y':
            try:
                # 删除记忆（会自动取消聊天关联）
                delete_result = manager.delete_memory_and_unlink(memory_id)
                logger.info(f"  ✓ 删除记忆成功，取消关联 {delete_result['unlinked_chat_count']} 条聊天记录")
                
                # 删除测试聊天记录
                manager.chat_storage._execute_query(
                    "DELETE FROM ai_agent_chat_history WHERE session_id = %s AND mac_address = %s",
                    (session_id, "test:mac:address")
                )
                logger.info(f"  ✓ 删除测试聊天记录")
                
            except Exception as e:
                logger.error(f"  ✗ 清理失败: {e}")
        else:
            logger.info(f"  保留测试数据，记忆ID: {memory_id}")
        
        # 关闭连接
        manager.close()
        logger.info(f"\n✅ 聊天记忆集成测试完成！")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ 聊天记忆集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())