-- Script pour créer les tables des fiches de prix
-- Exécuter avec: mysql -u root -p madargn < scripts/create_price_lists_tables.sql

USE madargn;

-- Table price_lists
CREATE TABLE IF NOT EXISTS price_lists (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_id BIGINT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_pricelist_dates (start_date, end_date),
    INDEX idx_pricelist_active (is_active),
    INDEX idx_pricelist_created_by (created_by_id),
    CONSTRAINT fk_pricelist_created_by FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table price_list_items
CREATE TABLE IF NOT EXISTS price_list_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    price_list_id BIGINT UNSIGNED NOT NULL,
    article_id BIGINT UNSIGNED NOT NULL,
    wholesale_price DECIMAL(18,2) NULL,
    retail_price DECIMAL(18,2) NULL,
    freebies VARCHAR(200) NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_pricelistitem_unique (price_list_id, article_id),
    INDEX idx_pricelistitem_article (article_id),
    INDEX idx_pricelistitem_pricelist (price_list_id),
    CONSTRAINT fk_pricelistitem_pricelist FOREIGN KEY (price_list_id) REFERENCES price_lists(id) ON DELETE CASCADE,
    CONSTRAINT fk_pricelistitem_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vérifier les tables créées
SHOW TABLES LIKE 'price_%';








