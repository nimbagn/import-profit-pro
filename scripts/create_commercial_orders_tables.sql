-- Script de création des tables pour les commandes commerciales
-- Import Profit Pro

-- Table des commandes commerciales
CREATE TABLE IF NOT EXISTS `commercial_orders` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `reference` VARCHAR(50) NOT NULL,
    `order_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `commercial_id` BIGINT UNSIGNED NOT NULL,
    `region_id` BIGINT UNSIGNED,
    `notes` TEXT,
    `status` ENUM('draft', 'pending_validation', 'validated', 'rejected', 'completed') NOT NULL DEFAULT 'draft',
    `validated_by_id` BIGINT UNSIGNED,
    `validated_at` DATETIME NULL,
    `rejection_reason` TEXT,
    `user_id` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_reference` (`reference`),
    INDEX `idx_order_date` (`order_date`),
    INDEX `idx_order_reference` (`reference`),
    INDEX `idx_order_commercial` (`commercial_id`),
    INDEX `idx_order_status` (`status`),
    CONSTRAINT `fk_order_commercial` FOREIGN KEY (`commercial_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_order_region` FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_order_validator` FOREIGN KEY (`validated_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des clients dans une commande
CREATE TABLE IF NOT EXISTS `commercial_order_clients` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id` BIGINT UNSIGNED NOT NULL,
    `client_name` VARCHAR(120) NOT NULL,
    `client_phone` VARCHAR(20),
    `client_address` VARCHAR(255),
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_orderclient_order` (`order_id`),
    CONSTRAINT `fk_orderclient_order` FOREIGN KEY (`order_id`) REFERENCES `commercial_orders` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des articles commandés pour un client
CREATE TABLE IF NOT EXISTS `commercial_order_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_client_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL,
    `unit_price_gnf` DECIMAL(18,2),
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_orderitem_client` (`order_client_id`),
    INDEX `idx_orderitem_item` (`stock_item_id`),
    CONSTRAINT `fk_orderitem_client` FOREIGN KEY (`order_client_id`) REFERENCES `commercial_order_clients` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_orderitem_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ajouter la colonne original_order_id à stock_returns si elle n'existe pas
-- Note: MySQL ne supporte pas IF NOT EXISTS avec ADD COLUMN
-- On vérifie d'abord si la colonne existe avant de l'ajouter
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'stock_returns' 
    AND COLUMN_NAME = 'original_order_id'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `stock_returns` ADD COLUMN `original_order_id` BIGINT UNSIGNED NULL AFTER `original_outgoing_id`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter l'index s'il n'existe pas déjà
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'stock_returns' 
    AND INDEX_NAME = 'idx_return_order'
);

SET @sql = IF(@idx_exists = 0,
    'ALTER TABLE `stock_returns` ADD INDEX `idx_return_order` (`original_order_id`)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter la contrainte de clé étrangère si elle n'existe pas
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'stock_returns' 
    AND CONSTRAINT_NAME = 'fk_return_order'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE `stock_returns` ADD CONSTRAINT `fk_return_order` FOREIGN KEY (`original_order_id`) REFERENCES `commercial_orders` (`id`) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

