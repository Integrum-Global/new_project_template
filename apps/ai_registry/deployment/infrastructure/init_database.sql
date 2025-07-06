-- AI Registry Database Initialization Script
-- This script sets up the database schema for the AI Registry application

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ai_registry;
USE ai_registry;

-- Create tables for AI use cases
CREATE TABLE IF NOT EXISTS use_cases (
    use_case_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    application_domain VARCHAR(200),
    implementation_status VARCHAR(50),
    business_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_domain (application_domain),
    INDEX idx_status (implementation_status),
    FULLTEXT idx_search (name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for AI methods
CREATE TABLE IF NOT EXISTS ai_methods (
    method_id INT PRIMARY KEY AUTO_INCREMENT,
    method_name VARCHAR(200) NOT NULL UNIQUE,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create junction table for use cases and AI methods (many-to-many)
CREATE TABLE IF NOT EXISTS use_case_methods (
    use_case_id INT,
    method_id INT,
    PRIMARY KEY (use_case_id, method_id),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(use_case_id) ON DELETE CASCADE,
    FOREIGN KEY (method_id) REFERENCES ai_methods(method_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for data sources
CREATE TABLE IF NOT EXISTS data_sources (
    source_id INT PRIMARY KEY AUTO_INCREMENT,
    use_case_id INT,
    source_type VARCHAR(100),
    source_description TEXT,
    data_volume VARCHAR(100),
    data_frequency VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (use_case_id) REFERENCES use_cases(use_case_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for stakeholders
CREATE TABLE IF NOT EXISTS stakeholders (
    stakeholder_id INT PRIMARY KEY AUTO_INCREMENT,
    use_case_id INT,
    stakeholder_type VARCHAR(100),
    stakeholder_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (use_case_id) REFERENCES use_cases(use_case_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for search history and analytics
CREATE TABLE IF NOT EXISTS search_history (
    search_id INT PRIMARY KEY AUTO_INCREMENT,
    query TEXT NOT NULL,
    result_count INT DEFAULT 0,
    user_id VARCHAR(100),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for MCP server cache
CREATE TABLE IF NOT EXISTS mcp_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value LONGTEXT,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    access_count INT DEFAULT 1,
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for API metrics
CREATE TABLE IF NOT EXISTS api_metrics (
    metric_id INT PRIMARY KEY AUTO_INCREMENT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    response_time_ms INT,
    status_code INT,
    error_message TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_endpoint (endpoint),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for document embeddings
CREATE TABLE IF NOT EXISTS document_embeddings (
    embedding_id INT PRIMARY KEY AUTO_INCREMENT,
    document_id VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    chunk_index INT,
    embedding_vector JSON,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_document (document_id),
    INDEX idx_type (document_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create table for knowledge base entries
CREATE TABLE IF NOT EXISTS knowledge_base (
    kb_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    content LONGTEXT,
    source_document VARCHAR(255),
    category VARCHAR(100),
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FULLTEXT idx_kb_search (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create views for common queries
CREATE OR REPLACE VIEW v_use_cases_with_methods AS
SELECT
    uc.use_case_id,
    uc.name,
    uc.description,
    uc.application_domain,
    uc.implementation_status,
    GROUP_CONCAT(am.method_name SEPARATOR ', ') AS ai_methods
FROM use_cases uc
LEFT JOIN use_case_methods ucm ON uc.use_case_id = ucm.use_case_id
LEFT JOIN ai_methods am ON ucm.method_id = am.method_id
GROUP BY uc.use_case_id;

CREATE OR REPLACE VIEW v_domain_statistics AS
SELECT
    application_domain,
    COUNT(*) as use_case_count,
    COUNT(DISTINCT implementation_status) as status_variety
FROM use_cases
GROUP BY application_domain
ORDER BY use_case_count DESC;

CREATE OR REPLACE VIEW v_method_popularity AS
SELECT
    am.method_name,
    am.category,
    COUNT(ucm.use_case_id) as usage_count
FROM ai_methods am
LEFT JOIN use_case_methods ucm ON am.method_id = ucm.method_id
GROUP BY am.method_id
ORDER BY usage_count DESC;

-- Create stored procedures for common operations
DELIMITER $$

CREATE PROCEDURE sp_search_use_cases(IN search_query VARCHAR(255))
BEGIN
    SELECT
        uc.use_case_id,
        uc.name,
        uc.description,
        uc.application_domain,
        uc.implementation_status,
        GROUP_CONCAT(am.method_name SEPARATOR ', ') AS ai_methods,
        MATCH(uc.name, uc.description) AGAINST(search_query IN NATURAL LANGUAGE MODE) AS relevance_score
    FROM use_cases uc
    LEFT JOIN use_case_methods ucm ON uc.use_case_id = ucm.use_case_id
    LEFT JOIN ai_methods am ON ucm.method_id = am.method_id
    WHERE MATCH(uc.name, uc.description) AGAINST(search_query IN NATURAL LANGUAGE MODE)
    GROUP BY uc.use_case_id
    ORDER BY relevance_score DESC
    LIMIT 50;
END$$

CREATE PROCEDURE sp_clean_expired_cache()
BEGIN
    DELETE FROM mcp_cache
    WHERE expires_at IS NOT NULL
    AND expires_at < CURRENT_TIMESTAMP;
END$$

CREATE PROCEDURE sp_record_api_metric(
    IN p_endpoint VARCHAR(255),
    IN p_method VARCHAR(10),
    IN p_response_time INT,
    IN p_status_code INT,
    IN p_error_message TEXT,
    IN p_user_id VARCHAR(100)
)
BEGIN
    INSERT INTO api_metrics (endpoint, method, response_time_ms, status_code, error_message, user_id)
    VALUES (p_endpoint, p_method, p_response_time, p_status_code, p_error_message, p_user_id);
END$$

DELIMITER ;

-- Create indexes for performance
CREATE INDEX idx_use_cases_updated ON use_cases(updated_at DESC);
CREATE INDEX idx_api_metrics_response_time ON api_metrics(response_time_ms);
CREATE INDEX idx_search_history_user ON search_history(user_id);

-- Create event to clean up old data periodically
DELIMITER $$

CREATE EVENT IF NOT EXISTS evt_cleanup_old_data
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    -- Clean expired cache entries
    CALL sp_clean_expired_cache();

    -- Clean old search history (keep last 30 days)
    DELETE FROM search_history
    WHERE created_at < DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 30 DAY);

    -- Clean old API metrics (keep last 7 days)
    DELETE FROM api_metrics
    WHERE created_at < DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY);
END$$

DELIMITER ;

-- Grant permissions for application user
-- Replace 'ai_registry_user' and 'password' with actual credentials
CREATE USER IF NOT EXISTS 'ai_registry_user'@'%' IDENTIFIED BY 'secure_password_here';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON ai_registry.* TO 'ai_registry_user'@'%';
GRANT CREATE TEMPORARY TABLES ON ai_registry.* TO 'ai_registry_user'@'%';
FLUSH PRIVILEGES;

-- Insert sample data for testing
INSERT INTO ai_methods (method_name, category) VALUES
('Machine Learning', 'Core Technology'),
('Deep Learning', 'Core Technology'),
('Natural Language Processing', 'Specialized'),
('Computer Vision', 'Specialized'),
('Reinforcement Learning', 'Advanced'),
('Transfer Learning', 'Technique'),
('Neural Networks', 'Architecture')
ON DUPLICATE KEY UPDATE category = VALUES(category);

-- Success message
SELECT 'Database initialization completed successfully!' AS status;
