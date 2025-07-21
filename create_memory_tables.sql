-- 创建memory表
CREATE TABLE IF NOT EXISTS memory (
    id VARCHAR(36) PRIMARY KEY,
    text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 为ai_agent_chat_history表添加memory_id字段
ALTER TABLE ai_agent_chat_history 
ADD COLUMN memory_id VARCHAR(36) NULL AFTER audio_id,
ADD INDEX idx_memory_id (memory_id);

-- 添加外键约束（可选，建议先不加，等数据同步好后再加）
-- ALTER TABLE ai_agent_chat_history 
-- ADD CONSTRAINT fk_chat_memory 
-- FOREIGN KEY (memory_id) REFERENCES memory(id) ON DELETE SET NULL;