-- Script SQL pour créer la table search_index
-- Moteur de recherche global

CREATE TABLE IF NOT EXISTS search_index (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    keywords VARCHAR(1000),
    module VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    search_metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_search_entity (entity_type, entity_id),
    INDEX idx_search_module (module),
    INDEX idx_search_title (title),
    INDEX idx_search_created (created_at),
    FULLTEXT INDEX idx_search_fulltext (title, content, keywords)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

