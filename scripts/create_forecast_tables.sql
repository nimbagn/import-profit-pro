-- =========================================================
-- CRÉATION DES TABLES POUR LES PRÉVISIONS & VENTES
-- =========================================================

-- Table des prévisions
CREATE TABLE IF NOT EXISTS `forecasts` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `status` ENUM('draft', 'active', 'completed', 'archived') NOT NULL DEFAULT 'draft',
    `total_forecast_value` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `total_realized_value` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `created_by_id` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_forecast_dates` (`start_date`, `end_date`),
    KEY `idx_forecast_status` (`status`),
    KEY `idx_forecast_created_by` (`created_by_id`),
    CONSTRAINT `fk_forecasts_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des éléments de prévision
CREATE TABLE IF NOT EXISTS `forecast_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `forecast_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    
    -- Prévisions
    `forecast_quantity` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `selling_price_gnf` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    
    -- Réalisations (calculées depuis StockOutgoing)
    `realized_quantity` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `realized_value_gnf` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    
    -- Métriques calculées
    `realization_percentage` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `equivalent_quantity` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `evaluated_value` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `evaluated_value_cfa` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `deviation_50pct` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `quantity_available` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `number_of_days` INT NOT NULL DEFAULT 1,
    
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_forecast_item` (`forecast_id`, `stock_item_id`),
    KEY `idx_forecastitem_forecast` (`forecast_id`),
    KEY `idx_forecastitem_item` (`stock_item_id`),
    CONSTRAINT `fk_forecast_items_forecast` FOREIGN KEY (`forecast_id`) REFERENCES `forecasts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_forecast_items_stock_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- VÉRIFICATION
-- =========================================================

SELECT 'Tables forecasts et forecast_items créées avec succès!' AS message;

