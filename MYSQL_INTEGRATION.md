# MySQL Integration for mem0

This document describes the MySQL integration for mem0, which allows you to sync all memory operations to a MySQL database alongside the existing vector store operations.

## Overview

The MySQL integration provides:
- **Dual Storage**: Memories are stored in both vector database (for semantic search) and MySQL database (for relational queries)
- **Automatic Sync**: All memory operations (add, update, delete) are automatically synced to MySQL
- **History Tracking**: Complete history of all memory changes stored in MySQL
- **Easy Migration**: Existing memories can be migrated to MySQL
- **Configurable**: Flexible configuration for different MySQL setups

## Architecture

```
mem0 Memory Operations
         |
         v
┌─────────────────┐    ┌──────────────────┐
│  Vector Store   │    │  MySQL Database  │
│  (Semantic)     │    │  (Relational)    │
├─────────────────┤    ├──────────────────┤
│ • Embeddings    │    │ • memory table   │
│ • Fast Search   │    │ • history table  │
│ • Similarity    │    │ • SQL queries    │
└─────────────────┘    └──────────────────┘
```

## Database Schema

### Memory Table
```sql
CREATE TABLE memory (
    id VARCHAR(36) PRIMARY KEY,           -- Memory UUID
    memory_text TEXT NOT NULL,            -- Memory content
    memory_hash VARCHAR(32),              -- Content hash
    user_id VARCHAR(255),                 -- User identifier
    agent_id VARCHAR(255),                -- Agent identifier  
    run_id VARCHAR(255),                  -- Run identifier
    actor_id VARCHAR(255),                -- Actor identifier
    role VARCHAR(50),                     -- Message role
    metadata JSON,                        -- Additional metadata
    original_text TEXT,                   -- Original input text
    created_at DATETIME,                  -- Creation timestamp
    updated_at DATETIME,                  -- Update timestamp
    
    INDEX idx_user_id (user_id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_run_id (run_id),
    INDEX idx_actor_id (actor_id),
    INDEX idx_created_at (created_at)
);
```

### Memory History Table
```sql
CREATE TABLE memory_history (
    id VARCHAR(36) PRIMARY KEY,           -- History record UUID
    memory_id VARCHAR(36),                -- Reference to memory
    old_memory TEXT,                      -- Previous content
    new_memory TEXT,                      -- New content
    event VARCHAR(10),                    -- ADD/UPDATE/DELETE
    created_at DATETIME,                  -- Event timestamp
    updated_at DATETIME,                  -- Update timestamp
    is_deleted TINYINT(1) DEFAULT 0,      -- Deletion flag
    actor_id VARCHAR(255),                -- Actor who made change
    role VARCHAR(50),                     -- Actor role
    
    INDEX idx_memory_id (memory_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (memory_id) REFERENCES memory(id) ON DELETE CASCADE
);
```

## Installation

### 1. Install MySQL Dependency

```bash
# Install MySQL connector
pip install mysql-connector-python

# Or add to requirements.txt
echo "mysql-connector-python>=8.0.0" >> requirements.txt
```

### 2. Setup MySQL Database

#### Option A: Using xiaozhi-server Docker Setup
```bash
# Use existing xiaozhi-server setup
cd /path/to/xiaozhi-esp32-server/main/xiaozhi-server
docker-compose -f docker-compose_all.yml up -d xiaozhi-esp32-server-db
```

#### Option B: Custom MySQL Setup
```bash
# Start MySQL with Docker
docker run --name mem0-mysql \
  -e MYSQL_ROOT_PASSWORD=yourpassword \
  -e MYSQL_DATABASE=mem0 \
  -p 3306:3306 \
  -d mysql:latest
```

## Usage

### Basic Usage

```python
from mem0.memory.mysql_memory import MySQLSyncMemory
from mem0.configs.base import MemoryConfig
from mem0.configs.mysql import MySQLConfig

# Configure MySQL connection
mysql_config = MySQLConfig.for_xiaozhi_server(
    host="localhost",
    password="123456"
)

# Configure mem0
memory_config = MemoryConfig()

# Initialize with MySQL sync
memory = MySQLSyncMemory(
    config=memory_config,
    mysql_config=mysql_config.to_connection_dict()
)

# Add memories (automatically synced to MySQL)
result = memory.add("I love playing basketball", user_id="user123")

# Search memories (uses vector store)
results = memory.search("sports", user_id="user123")

# Query MySQL directly
mysql_memories = memory.get_mysql_memories(user_id="user123")
mysql_history = memory.get_mysql_history(memory_id="some-uuid")
```

### Configuration Options

#### Using MySQLConfig Class
```python
from mem0.configs.mysql import MySQLConfig

# Basic configuration
config = MySQLConfig(
    host="localhost",
    port=3306,
    user="root",
    password="mypassword",
    database="mydb"
)

# For xiaozhi-server
config = MySQLConfig.for_xiaozhi_server(
    host="localhost",
    password="123456"
)

# For Docker
config = MySQLConfig.for_docker(
    host="localhost",
    port=3306
)
```

#### Using Dictionary
```python
mysql_config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "xiaozhi_esp32_server"
}

memory = MySQLSyncMemory(mysql_config=mysql_config)
```

### Advanced Features

#### Migrate Existing Memories
```python
# Sync all existing vector store memories to MySQL
count = memory.sync_existing_memories_to_mysql()
print(f"Migrated {count} memories to MySQL")
```

#### Query MySQL Directly
```python
# Get memories with custom filters
memories = memory.get_mysql_memories(
    user_id="user123",
    agent_id="agent456", 
    limit=50
)

# Get specific memory
memory_data = memory.get_mysql_memory("memory-uuid")

# Get history for a memory
history = memory.get_mysql_history("memory-uuid")
for record in history:
    print(f"{record['event']}: {record['old_memory']} -> {record['new_memory']}")
```

#### Custom SQL Queries
```python
# Access MySQL manager directly for custom queries
mysql_db = memory.mysql_db

# Custom query example
result = mysql_db._execute_query(
    "SELECT COUNT(*) as count FROM memory WHERE user_id = %s",
    ("user123",),
    fetch=True
)
print(f"User has {result[0]['count']} memories")
```

## Configuration Examples

### Development Setup
```python
from mem0.configs.mysql import MySQLConfig

config = MySQLConfig(
    host="localhost",
    port=3306,
    user="root",
    password="devpassword",
    database="mem0_dev"
)
```

### Production Setup with SSL
```python
config = MySQLConfig(
    host="prod-mysql.example.com",
    port=3306,
    user="mem0_user",
    password="secure_password",
    database="mem0_prod",
    ssl_disabled=False,
    ssl_ca="/path/to/ca.pem",
    ssl_cert="/path/to/client-cert.pem",
    ssl_key="/path/to/client-key.pem"
)
```

### Connection Pool Setup
```python
config = MySQLConfig(
    host="localhost",
    user="root",
    password="password",
    database="mem0",
    pool_name="mem0_pool",
    pool_size=10,
    pool_reset_session=True
)
```

## Example Scripts

### Complete Example
```bash
# Run the complete example
python examples/mysql_integration_example.py
```

### Testing
```bash
# Validate code syntax
python validate_mysql_code.py

# Test with actual MySQL (requires running MySQL)
python test_mysql_integration.py
```

## Benefits

### 1. **Dual Query Capabilities**
- Vector store: Semantic similarity search
- MySQL: Complex relational queries, joins, aggregations

### 2. **Data Persistence**
- MySQL provides reliable ACID transactions
- Easy backup and replication
- Standard SQL tooling

### 3. **Analytics & Reporting**
- Use SQL for complex analytics
- Generate reports on memory usage
- Track memory evolution over time

### 4. **Integration**
- Easy integration with existing MySQL infrastructure
- Use with BI tools like Grafana, Tableau
- Export data for further analysis

## Troubleshooting

### Common Issues

#### Connection Errors
```python
# Check MySQL connection
try:
    memory = MySQLSyncMemory(mysql_config=config)
    print("✓ MySQL connection successful")
except Exception as e:
    print(f"✗ MySQL connection failed: {e}")
```

#### Missing Tables
```python
# Tables are created automatically, but you can recreate them
memory.mysql_db.reset()  # Drops and recreates tables
```

#### Sync Issues
```python
# Check for sync errors in logs
import logging
logging.basicConfig(level=logging.DEBUG)

# Memory operations will show sync status
memory.add("test message", user_id="test")
```

### Performance Considerations

1. **Indexing**: Tables are indexed on common query fields
2. **Batch Operations**: Use transactions for bulk operations
3. **Connection Pooling**: Configure pools for high-concurrency apps
4. **Monitoring**: Monitor MySQL performance and mem0 sync operations

## Migration Guide

### From SQLite to MySQL
```python
# 1. Create MySQL-synced memory instance
mysql_memory = MySQLSyncMemory(mysql_config=mysql_config)

# 2. Migrate existing memories
count = mysql_memory.sync_existing_memories_to_mysql()
print(f"Migrated {count} memories")

# 3. Verify migration
vector_memories = mysql_memory.get_all(user_id="test_user")
mysql_memories = mysql_memory.get_mysql_memories(user_id="test_user")
print(f"Vector: {len(vector_memories['results'])}, MySQL: {len(mysql_memories)}")
```

## API Reference

### MySQLSyncMemory Class
- Inherits from `Memory` class
- All standard mem0 methods work unchanged
- Additional MySQL-specific methods

#### Additional Methods
```python
# MySQL-specific queries
get_mysql_memories(user_id, agent_id, run_id, actor_id, limit)
get_mysql_memory(memory_id)
get_mysql_history(memory_id)

# Migration and sync
sync_existing_memories_to_mysql()

# Database management
reset()  # Resets both vector store and MySQL
close()  # Closes all connections
```

### MySQLConfig Class
```python
# Factory methods
MySQLConfig.for_xiaozhi_server(host, password)
MySQLConfig.for_docker(host, port)

# Configuration
to_connection_dict()  # Convert to mysql.connector format
```

### MySQLManager Class
```python
# Direct database operations
add_memory(memory_id, memory_text, ...)
update_memory(memory_id, memory_text, ...)
delete_memory(memory_id)
get_memory(memory_id)
get_all_memories(filters...)
add_history(memory_id, old_memory, new_memory, event)
get_history(memory_id)
```

## Contributing

To contribute to the MySQL integration:

1. Follow the existing code patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure backward compatibility
5. Test with both development and production MySQL setups

## License

This MySQL integration follows the same license as the main mem0 project.