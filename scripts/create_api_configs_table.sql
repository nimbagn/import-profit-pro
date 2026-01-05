-- Script SQL pour créer la table api_configs (MySQL)
-- Cette table stocke les configurations des APIs externes (Message Pro, etc.)

-- Créer la table api_configs
CREATE TABLE IF NOT EXISTS api_configs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL UNIQUE,
    api_secret TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    updated_by_id BIGINT UNSIGNED,
    
    INDEX idx_apiconfig_name (api_name),
    INDEX idx_apiconfig_active (is_active),
    
    FOREIGN KEY (updated_by_id) REFERENCES users(id) 
        ON UPDATE CASCADE 
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

