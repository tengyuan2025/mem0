#!/usr/bin/env python3
"""
MySQL Integration Example for mem0

This example demonstrates how to use mem0 with MySQL database synchronization.
It shows how to:
1. Initialize mem0 with MySQL sync
2. Add memories that are automatically synced to MySQL
3. Query memories from both vector store and MySQL
4. View memory history stored in MySQL

Prerequisites:
- MySQL server running (can use docker-compose_all.yml from xiaozhi-server)
- Database 'xiaozhi_esp32_server' exists
- User 'root' with password '123456' has access

Usage:
    python examples/mysql_integration_example.py
"""

import logging
import sys
from pathlib import Path

# Add the mem0 directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mem0.memory.mysql_memory import MySQLSyncMemory
from mem0.configs.base import MemoryConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main example function"""
    
    # MySQL configuration (matching xiaozhi-server setup)
    mysql_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root", 
        "password": "123456",
        "database": "xiaozhi_esp32_server"
    }
    
    # mem0 configuration
    memory_config = MemoryConfig()
    
    try:
        # Initialize MySQL-synced memory
        logger.info("Initializing mem0 with MySQL sync...")
        memory = MySQLSyncMemory(config=memory_config, mysql_config=mysql_config)
        logger.info("✓ Successfully connected to MySQL and initialized mem0")
        
        # Test data
        user_id = "test_user_001"
        messages = [
            "I love playing basketball on weekends",
            "My favorite food is sushi from Japan", 
            "I work as a software engineer at a tech company",
            "I have a pet cat named Whiskers"
        ]
        
        # Add memories
        logger.info("\n=== Adding Memories ===")
        memory_ids = []
        for i, message in enumerate(messages, 1):
            logger.info(f"Adding memory {i}: {message}")
            result = memory.add(message, user_id=user_id)
            
            if result and "results" in result and result["results"]:
                memory_id = result["results"][0]["id"]
                memory_ids.append(memory_id)
                logger.info(f"  ✓ Memory added with ID: {memory_id}")
            else:
                logger.error(f"  ✗ Failed to add memory: {message}")
        
        # Search memories
        logger.info("\n=== Searching Memories ===")
        search_query = "basketball sports"
        logger.info(f"Searching for: '{search_query}'")
        search_results = memory.search(search_query, user_id=user_id)
        
        if search_results and "results" in search_results:
            for result in search_results["results"]:
                logger.info(f"  Found: {result['memory']} (score: {result.get('score', 'N/A')})")
        else:
            logger.info("  No search results found")
        
        # Get all memories from vector store
        logger.info("\n=== Getting All Memories (Vector Store) ===")
        all_memories = memory.get_all(user_id=user_id)
        if all_memories and "results" in all_memories:
            for mem in all_memories["results"]:
                logger.info(f"  Vector: {mem['id'][:8]}... - {mem['memory']}")
        
        # Get all memories from MySQL
        logger.info("\n=== Getting All Memories (MySQL) ===")
        mysql_memories = memory.get_mysql_memories(user_id=user_id)
        for mem in mysql_memories:
            logger.info(f"  MySQL: {mem['id'][:8]}... - {mem['memory_text']}")
        
        # Test memory update
        if memory_ids:
            logger.info("\n=== Testing Memory Update ===")
            test_memory_id = memory_ids[0]
            updated_text = "I love playing basketball and tennis on weekends"
            logger.info(f"Updating memory {test_memory_id[:8]}... to: {updated_text}")
            
            memory.update(test_memory_id, updated_text)
            logger.info("  ✓ Memory updated successfully")
            
            # Check history
            logger.info("  Checking MySQL history:")
            history = memory.get_mysql_history(test_memory_id)
            for record in history:
                logger.info(f"    {record['event']}: {record['old_memory']} -> {record['new_memory']}")
        
        # Test memory deletion
        if len(memory_ids) > 1:
            logger.info("\n=== Testing Memory Deletion ===")
            test_memory_id = memory_ids[1]
            logger.info(f"Deleting memory {test_memory_id[:8]}...")
            
            memory.delete(test_memory_id)
            logger.info("  ✓ Memory deleted successfully")
            
            # Check history
            logger.info("  Checking MySQL history:")
            history = memory.get_mysql_history(test_memory_id)
            for record in history:
                logger.info(f"    {record['event']}: {record['old_memory']} -> {record['new_memory']}")
        
        # Final counts
        logger.info("\n=== Final Status ===")
        final_vector_memories = memory.get_all(user_id=user_id)
        final_mysql_memories = memory.get_mysql_memories(user_id=user_id)
        
        vector_count = len(final_vector_memories["results"]) if final_vector_memories and "results" in final_vector_memories else 0
        mysql_count = len(final_mysql_memories)
        
        logger.info(f"Vector store memories: {vector_count}")
        logger.info(f"MySQL memories: {mysql_count}")
        
        if vector_count == mysql_count:
            logger.info("✓ Vector store and MySQL are in sync!")
        else:
            logger.warning("⚠ Vector store and MySQL counts don't match")
        
        # Clean up
        memory.close()
        logger.info("\n✓ MySQL integration test completed successfully!")
        
    except Exception as e:
        logger.error(f"\n✗ Error during MySQL integration test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())