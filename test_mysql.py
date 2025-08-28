"""
MySQL集成测试脚本
用于测试MySQL记忆存储功能
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from mysql_handler import MySQLHandler

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")


async def test_mysql_handler():
    """测试MySQL处理器"""
    handler = MySQLHandler()
    
    try:
        # 1. 初始化连接
        logger.info("正在初始化MySQL连接...")
        await handler.initialize()
        logger.info("✅ MySQL连接初始化成功")
        
        # 2. 测试插入记忆
        logger.info("正在测试插入记忆...")
        test_memory_id = f"test_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_user_id = "test_user_123"
        test_content = "这是一条测试记忆：用户喜欢喝咖啡，特别是拿铁。"
        test_metadata = {
            "category": "preference",
            "confidence": 0.9,
            "source": "conversation"
        }
        
        inserted_id = await handler.insert_memory(
            memory_id=test_memory_id,
            user_id=test_user_id,
            content=test_content,
            metadata=test_metadata,
            event="用户偏好记录",
            knowledge="用户喜欢咖啡",
            skill=None
        )
        
        logger.info(f"✅ 记忆插入成功，数据库ID: {inserted_id}")
        
        # 3. 测试查询记忆
        logger.info("正在测试查询记忆...")
        retrieved_memory = await handler.get_memory(test_memory_id)
        
        if retrieved_memory:
            logger.info("✅ 记忆查询成功")
            logger.info(f"   记忆内容: {retrieved_memory['content']}")
            logger.info(f"   用户ID: {retrieved_memory['user_id']}")
            logger.info(f"   创建时间: {retrieved_memory['created_at']}")
        else:
            logger.error("❌ 记忆查询失败")
        
        # 4. 测试获取用户所有记忆
        logger.info("正在测试获取用户所有记忆...")
        user_memories = await handler.get_user_memories(test_user_id, limit=10)
        
        if user_memories:
            logger.info(f"✅ 获取用户记忆成功，共{len(user_memories)}条记录")
            for memory in user_memories:
                logger.info(f"   - {memory['memory_id']}: {memory['content'][:50]}...")
        else:
            logger.info("ℹ️ 该用户暂无记忆记录")
        
        # 5. 测试更新记忆
        logger.info("正在测试更新记忆...")
        updated_content = "这是一条更新后的测试记忆：用户喜欢喝咖啡和茶，特别是拿铁和绿茶。"
        update_result = await handler.update_memory(
            memory_id=test_memory_id,
            content=updated_content,
            knowledge="用户喜欢咖啡和茶"
        )
        
        if update_result:
            logger.info("✅ 记忆更新成功")
            
            # 验证更新结果
            updated_memory = await handler.get_memory(test_memory_id)
            if updated_memory and updated_memory['content'] == updated_content:
                logger.info("✅ 更新内容验证成功")
            else:
                logger.error("❌ 更新内容验证失败")
        else:
            logger.error("❌ 记忆更新失败")
        
        # 6. 测试按时间搜索
        logger.info("正在测试按时间搜索记忆...")
        from datetime import timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        time_search_results = await handler.search_memories_by_time(
            user_id=test_user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if time_search_results:
            logger.info(f"✅ 按时间搜索成功，找到{len(time_search_results)}条记录")
        else:
            logger.info("ℹ️ 指定时间范围内无记录")
        
        # 清理测试数据 - 删除测试记忆
        logger.info("正在清理测试数据...")
        delete_result = await handler.delete_memory(memory_id=test_memory_id)
        
        if delete_result > 0:
            logger.info(f"✅ 记忆删除成功，删除了{delete_result}条记录")
            
            # 验证删除结果
            deleted_memory = await handler.get_memory(test_memory_id)
            if not deleted_memory:
                logger.info("✅ 删除验证成功，记忆已不存在")
            else:
                logger.error("❌ 删除验证失败，记忆仍然存在")
        else:
            logger.error("❌ 记忆删除失败")
        
        logger.info("🎉 所有测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        await handler.close()
        logger.info("MySQL连接已关闭")


async def test_database_connection():
    """测试数据库连接"""
    try:
        import aiomysql
        
        connection = await aiomysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '123456'),
            charset='utf8mb4'
        )
        
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
            logger.info(f"✅ MySQL连接成功，版本: {version[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ MySQL连接失败: {e}")
        logger.info("请确保：")
        logger.info("1. MySQL服务正在运行")
        logger.info("2. 用户名密码正确")
        logger.info("3. 网络连接正常")
        return False


if __name__ == "__main__":
    async def main():
        logger.info("开始MySQL集成测试...")
        
        # 首先测试基础连接
        logger.info("=" * 50)
        logger.info("1. 测试数据库基础连接")
        logger.info("=" * 50)
        
        connection_ok = await test_database_connection()
        
        if connection_ok:
            logger.info("\n" + "=" * 50)
            logger.info("2. 测试MySQL处理器功能")
            logger.info("=" * 50)
            await test_mysql_handler()
        else:
            logger.error("数据库连接失败，跳过功能测试")
    
    # 运行测试
    asyncio.run(main())