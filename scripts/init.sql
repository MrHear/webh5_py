-- =========================================
-- OneSpace Database Initialization
-- =========================================

-- 确保使用正确的字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建帖子表 (如果不存在)
CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    mood VARCHAR(50),
    weather VARCHAR(50),
    images JSON,
    is_private BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_is_private (is_private)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 可以添加更多初始化 SQL 语句
