-- Script de création des tables pour les récapitulatifs de chargement de stock
-- Import Profit Pro

-- Table des récapitulatifs de chargement
CREATE TABLE IF NOT EXISTS `stock_loading_summaries` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id` BIGINT UNSIGNED NOT NULL,
    `commercial_id` BIGINT UNSIGNED NOT NULL,
    `commercial_depot_id` BIGINT UNSIGNED NULL,
    `commercial_vehicle_id` BIGINT UNSIGNED NULL,
    `source_depot_id` BIGINT UNSIGNED NOT NULL,
    `status` ENUM('pending', 'stock_checked', 'loading_in_progress', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    `pre_loading_stock_verified` BOOLEAN NOT NULL DEFAULT FALSE,
    `pre_loading_stock_verified_at` DATETIME NULL,
    `pre_loading_stock_verified_by_id` BIGINT UNSIGNED NULL,
    `post_loading_stock_verified` BOOLEAN NOT NULL DEFAULT FALSE,
    `post_loading_stock_verified_at` DATETIME NULL,
    `post_loading_stock_verified_by_id` BIGINT UNSIGNED NULL,
    `loading_completed_at` DATETIME NULL,
    `loading_completed_by_id` BIGINT UNSIGNED NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_loadingsummary_order` (`order_id`),
    INDEX `idx_loadingsummary_order` (`order_id`),
    INDEX `idx_loadingsummary_commercial` (`commercial_id`),
    INDEX `idx_loadingsummary_status` (`status`),
    CONSTRAINT `fk_loadingsummary_order` FOREIGN KEY (`order_id`) REFERENCES `commercial_orders` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_loadingsummary_commercial` FOREIGN KEY (`commercial_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_loadingsummary_commercial_depot` FOREIGN KEY (`commercial_depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_loadingsummary_commercial_vehicle` FOREIGN KEY (`commercial_vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_loadingsummary_source_depot` FOREIGN KEY (`source_depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_loadingsummary_pre_verifier` FOREIGN KEY (`pre_loading_stock_verified_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_loadingsummary_post_verifier` FOREIGN KEY (`post_loading_stock_verified_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_loadingsummary_loader` FOREIGN KEY (`loading_completed_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des articles dans un récapitulatif de chargement
CREATE TABLE IF NOT EXISTS `stock_loading_summary_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `summary_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity_required` DECIMAL(18,4) NOT NULL,
    `quantity_loaded` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `pre_loading_stock_remaining` DECIMAL(18,4) NULL,
    `post_loading_stock_remaining` DECIMAL(18,4) NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_loadingsummaryitem_summary` (`summary_id`),
    INDEX `idx_loadingsummaryitem_item` (`stock_item_id`),
    CONSTRAINT `fk_loadingsummaryitem_summary` FOREIGN KEY (`summary_id`) REFERENCES `stock_loading_summaries` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_loadingsummaryitem_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

