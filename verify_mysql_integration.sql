-- 验证MySQL聊天记忆集成的SQL脚本
-- 可以直接在MySQL客户端中执行

USE xiaozhi_esp32_server;

-- 1. 检查memory表是否存在
SELECT 'Checking memory table...' as status;
DESCRIBE memory;

-- 2. 检查ai_agent_chat_history表是否有memory_id字段
SELECT 'Checking ai_agent_chat_history table...' as status;
DESCRIBE ai_agent_chat_history;

-- 3. 显示当前数据统计
SELECT 'Data statistics...' as status;
SELECT 
    'memory' as table_name,
    COUNT(*) as record_count
FROM memory
UNION ALL
SELECT 
    'ai_agent_chat_history' as table_name,
    COUNT(*) as record_count
FROM ai_agent_chat_history
UNION ALL
SELECT 
    'linked_chat_records' as table_name,
    COUNT(*) as record_count
FROM ai_agent_chat_history 
WHERE memory_id IS NOT NULL;

-- 4. 检查是否有孤立的memory_id引用
SELECT 'Checking data integrity...' as status;
SELECT 
    COUNT(*) as orphaned_memory_references
FROM ai_agent_chat_history ch 
LEFT JOIN memory m ON ch.memory_id = m.id 
WHERE ch.memory_id IS NOT NULL AND m.id IS NULL;

-- 5. 显示现有的聊天记录示例（前5条）
SELECT 'Sample chat records...' as status;
SELECT 
    id,
    agent_id,
    session_id,
    chat_type,
    LEFT(content, 50) as content_preview,
    memory_id,
    created_at
FROM ai_agent_chat_history 
ORDER BY created_at DESC 
LIMIT 5;

-- 6. 如果有记忆数据，显示示例
SELECT 'Sample memory records...' as status;
SELECT 
    id,
    LEFT(text, 100) as text_preview,
    created_at,
    updated_at
FROM memory 
ORDER BY created_at DESC 
LIMIT 3;

-- 7. 测试插入一条记忆和关联聊天记录
SELECT 'Testing insert operations...' as status;

-- 插入测试记忆
INSERT INTO memory (id, text, created_at, updated_at) 
VALUES (
    'test-memory-12345', 
    '这是一个测试记忆，用于验证MySQL集成功能', 
    NOW(), 
    NOW()
);

-- 插入测试聊天记录并关联记忆
INSERT INTO ai_agent_chat_history 
(mac_address, agent_id, session_id, chat_type, content, memory_id, created_at) 
VALUES (
    'test:mac:address',
    'test_agent_123',
    'test_session_456', 
    1,
    '测试聊天内容',
    'test-memory-12345',
    NOW()
);

-- 验证关联是否成功
SELECT 'Verifying test data...' as status;
SELECT 
    m.id as memory_id,
    m.text as memory_text,
    ch.content as chat_content,
    ch.chat_type
FROM memory m
JOIN ai_agent_chat_history ch ON m.id = ch.memory_id
WHERE m.id = 'test-memory-12345';

-- 清理测试数据
SELECT 'Cleaning up test data...' as status;
DELETE FROM ai_agent_chat_history WHERE memory_id = 'test-memory-12345';
DELETE FROM memory WHERE id = 'test-memory-12345';

-- 最终状态确认
SELECT 'Final verification complete!' as status;
SELECT 'MySQL chat-memory integration is ready!' as message;