#!/usr/bin/env python3
"""
数据库连接测试脚本
用于测试阿里云RDS MySQL数据库连接
"""

import os
import asyncio
from mysql_handler import MySQLHandler
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_mysql_connection():
    """测试MySQL连接和基本操作"""
    
    # 检查环境变量
    required_vars = ['DATABASE_HOST', 'DATABASE_USER', 'DATABASE_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {missing_vars}")
        return False
    
    # 显示连接信息（隐藏密码）
    logger.info(f"测试数据库连接:")
    logger.info(f"  主机: {os.getenv('DATABASE_HOST')}")
    logger.info(f"  端口: {os.getenv('DATABASE_PORT', 3306)}")
    logger.info(f"  用户: {os.getenv('DATABASE_USER')}")
    logger.info(f"  数据库: {os.getenv('DATABASE_NAME', 'mem0')}")
    
    try:
        # 初始化MySQL处理器
        mysql_handler = MySQLHandler()
        await mysql_handler.initialize()
        
        # 测试插入数据
        logger.info("测试插入记忆数据...")
        memory_id = await mysql_handler.insert_memory(
            memory_id="test_memory_001",
            user_id="test_user",
            content="这是一个测试记忆",
            metadata={"test": True, "type": "connection_test"}
        )
        logger.info(f"✅ 记忆插入成功: {memory_id}")
        
        # 测试查询数据
        logger.info("测试查询记忆数据...")
        memories = await mysql_handler.get_user_memories("test_user", limit=5)
        logger.info(f"✅ 查询成功，找到 {len(memories)} 条记忆")
        
        # 测试更新数据
        logger.info("测试更新记忆数据...")
        await mysql_handler.update_memory(
            memory_id="test_memory_001",
            content="这是一个更新后的测试记忆",
            metadata={"test": True, "type": "connection_test", "updated": True}
        )
        logger.info("✅ 记忆更新成功")
        
        # 测试删除数据
        logger.info("测试删除记忆数据...")
        await mysql_handler.delete_memory(
            memory_id="test_memory_001",
            user_id="test_user"
        )
        logger.info("✅ 记忆删除成功")
        
        # 关闭连接
        await mysql_handler.close()
        
        logger.info("🎉 数据库连接测试完全通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库测试失败: {e}")
        return False

if __name__ == "__main__":
    async def main():
        logger.info("🚀 开始数据库连接测试...")
        
        # 设置ENABLE_MYSQL环境变量
        os.environ["ENABLE_MYSQL"] = "true"
        
        success = await test_mysql_connection()
        
        if success:
            logger.info("✅ 数据库配置正确，可以正常使用云数据库！")
        else:
            logger.error("❌ 数据库配置有问题，请检查配置和网络连接")
    
    asyncio.run(main())