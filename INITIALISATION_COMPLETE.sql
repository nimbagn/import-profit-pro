-- =====================================================
-- SCRIPT D'INITIALISATION COMPLÈTE DE LA BASE DE DONNÉES
-- Import Profit Pro - Toutes les fonctionnalités
-- =====================================================
-- Exécutez: mysql -u root -p <nom_base> < INITIALISATION_COMPLETE.sql
-- OU utilisez: ./executer_initialisation.sh (détection automatique)
-- =====================================================
-- NOTE: Remplacez 'madargn' par le nom de votre base de données
-- ou utilisez le script shell qui détecte automatiquement
-- =====================================================

USE madargn;

SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. SUPPRESSION DES TABLES EXISTANTES (OPTIONNEL)
-- =====================================================

DROP TABLE IF EXISTS `inventory_details`;
DROP TABLE IF EXISTS `inventory_sessions`;
DROP TABLE IF EXISTS `stock_return_details`;
DROP TABLE IF EXISTS `stock_returns`;
DROP TABLE IF EXISTS `stock_outgoing_details`;
DROP TABLE IF EXISTS `stock_outgoings`;
DROP TABLE IF EXISTS `reception_details`;
DROP TABLE IF EXISTS `receptions`;
DROP TABLE IF EXISTS `stock_movements`;
DROP TABLE IF EXISTS `vehicle_stocks`;
DROP TABLE IF EXISTS `depot_stocks`;
DROP TABLE IF EXISTS `vehicle_odometers`;
DROP TABLE IF EXISTS `vehicle_maintenances`;
DROP TABLE IF EXISTS `vehicle_documents`;
DROP TABLE IF EXISTS `vehicles`;
DROP TABLE IF EXISTS `stock_items`;
DROP TABLE IF EXISTS `families`;
DROP TABLE IF EXISTS `depots`;
DROP TABLE IF EXISTS `regions`;
DROP TABLE IF EXISTS `simulation_items`;
DROP TABLE IF EXISTS `simulations`;
DROP TABLE IF EXISTS `articles`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `roles`;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 2. CRÉATION DES TABLES
-- =====================================================

-- Table des rôles
CREATE TABLE `roles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL,
    `code` VARCHAR(20) NOT NULL,
    `permissions` JSON,
    `description` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_roles_name` (`name`),
    UNIQUE KEY `uk_roles_code` (`code`),
    INDEX `idx_role_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des utilisateurs
CREATE TABLE `users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(80) NOT NULL,
    `email` VARCHAR(120) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(120),
    `phone` VARCHAR(20),
    `role_id` BIGINT UNSIGNED,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `last_login` DATETIME,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_users_username` (`username`),
    UNIQUE KEY `uk_users_email` (`email`),
    INDEX `idx_user_username` (`username`),
    INDEX `idx_user_email` (`email`),
    INDEX `idx_user_role` (`role_id`),
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des catégories
CREATE TABLE `categories` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des articles
CREATE TABLE `articles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `category_id` BIGINT UNSIGNED,
    `purchase_price` DECIMAL(18,2) NOT NULL,
    `purchase_currency` VARCHAR(3) NOT NULL DEFAULT 'USD',
    `unit_weight_kg` DECIMAL(18,4) NOT NULL,
    `description` TEXT,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_articles_category` (`category_id`),
    CONSTRAINT `fk_articles_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des simulations
CREATE TABLE `simulations` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `rate_usd` DECIMAL(18,2) NOT NULL,
    `rate_eur` DECIMAL(18,2) NOT NULL,
    `truck_capacity_tons` DECIMAL(18,2) NOT NULL,
    `is_completed` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des items de simulation
CREATE TABLE `simulation_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `simulation_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL,
    `selling_price_gnf` DECIMAL(18,2) NOT NULL,
    `purchase_price` DECIMAL(18,2) NOT NULL,
    `purchase_currency` VARCHAR(3) NOT NULL,
    `unit_weight_kg` DECIMAL(18,4) NOT NULL,
    `margin_pct` DECIMAL(5,2),
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_simitems_simulation` (`simulation_id`),
    INDEX `idx_simitems_article` (`article_id`),
    CONSTRAINT `fk_simitems_simulation` FOREIGN KEY (`simulation_id`) REFERENCES `simulations` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_simitems_article` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des régions
CREATE TABLE `regions` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(120) NOT NULL,
    `code` VARCHAR(20),
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_regions_name` (`name`),
    UNIQUE KEY `uk_regions_code` (`code`),
    INDEX `idx_region_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des dépôts
CREATE TABLE `depots` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(120) NOT NULL,
    `region_id` BIGINT UNSIGNED,
    `address` VARCHAR(255),
    `city` VARCHAR(100),
    `phone` VARCHAR(20),
    `email` VARCHAR(120),
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_depots_name` (`name`),
    INDEX `idx_depot_name` (`name`),
    INDEX `idx_depot_region` (`region_id`),
    CONSTRAINT `fk_depots_region` FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des véhicules
CREATE TABLE `vehicles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `plate_number` VARCHAR(20) NOT NULL,
    `brand` VARCHAR(50),
    `model` VARCHAR(50),
    `year` INT,
    `color` VARCHAR(30),
    `vin` VARCHAR(50),
    `whatsapp` VARCHAR(20),
    `current_user_id` BIGINT UNSIGNED,
    `acquisition_date` DATE,
    `status` ENUM('active', 'inactive', 'maintenance') NOT NULL DEFAULT 'active',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_vehicles_plate` (`plate_number`),
    UNIQUE KEY `uk_vehicles_vin` (`vin`),
    INDEX `idx_vehicle_plate` (`plate_number`),
    INDEX `idx_vehicle_user` (`current_user_id`),
    INDEX `idx_vehicle_status` (`status`),
    CONSTRAINT `fk_vehicles_user` FOREIGN KEY (`current_user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des familles
CREATE TABLE `families` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(120) NOT NULL,
    `code` VARCHAR(20),
    `description` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_families_name` (`name`),
    UNIQUE KEY `uk_families_code` (`code`),
    INDEX `idx_family_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des articles de stock
CREATE TABLE `stock_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `sku` VARCHAR(50) NOT NULL,
    `name` VARCHAR(160) NOT NULL,
    `family_id` BIGINT UNSIGNED,
    `purchase_price_gnf` DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    `unit_weight_kg` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `description` TEXT,
    `min_stock_depot` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `min_stock_vehicle` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_stockitems_sku` (`sku`),
    INDEX `idx_stockitem_sku` (`sku`),
    INDEX `idx_stockitem_name` (`name`),
    INDEX `idx_stockitem_family` (`family_id`),
    CONSTRAINT `fk_stockitems_family` FOREIGN KEY (`family_id`) REFERENCES `families` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des stocks de dépôt
CREATE TABLE `depot_stocks` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `depot_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_depot_stock` (`depot_id`, `stock_item_id`),
    INDEX `idx_depotstock_depot` (`depot_id`),
    INDEX `idx_depotstock_item` (`stock_item_id`),
    CONSTRAINT `fk_depotstocks_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_depotstocks_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des stocks de véhicule
CREATE TABLE `vehicle_stocks` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vehicle_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_vehicle_stock` (`vehicle_id`, `stock_item_id`),
    INDEX `idx_vehiclestock_vehicle` (`vehicle_id`),
    INDEX `idx_vehiclestock_item` (`stock_item_id`),
    CONSTRAINT `fk_vehiclestocks_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_vehiclestocks_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des mouvements de stock
CREATE TABLE `stock_movements` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `movement_type` ENUM('transfer', 'reception', 'adjustment', 'inventory') NOT NULL,
    `movement_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL,
    `user_id` BIGINT UNSIGNED,
    `from_depot_id` BIGINT UNSIGNED,
    `from_vehicle_id` BIGINT UNSIGNED,
    `to_depot_id` BIGINT UNSIGNED,
    `to_vehicle_id` BIGINT UNSIGNED,
    `supplier_name` VARCHAR(120),
    `bl_number` VARCHAR(50),
    `reason` TEXT,
    `inventory_session_id` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_movement_date` (`movement_date`),
    INDEX `idx_movement_type` (`movement_type`),
    INDEX `idx_movement_item` (`stock_item_id`),
    INDEX `idx_movement_user` (`user_id`),
    CONSTRAINT `fk_movements_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_movements_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_movements_from_depot` FOREIGN KEY (`from_depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_movements_from_vehicle` FOREIGN KEY (`from_vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_movements_to_depot` FOREIGN KEY (`to_depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_movements_to_vehicle` FOREIGN KEY (`to_vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des réceptions
CREATE TABLE `receptions` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `reference` VARCHAR(50) NOT NULL,
    `reception_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `depot_id` BIGINT UNSIGNED NOT NULL,
    `supplier_name` VARCHAR(120) NOT NULL,
    `bl_number` VARCHAR(50) NOT NULL,
    `user_id` BIGINT UNSIGNED,
    `notes` TEXT,
    `status` ENUM('draft', 'completed', 'cancelled') NOT NULL DEFAULT 'draft',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_receptions_reference` (`reference`),
    INDEX `idx_reception_date` (`reception_date`),
    INDEX `idx_reception_depot` (`depot_id`),
    INDEX `idx_reception_status` (`status`),
    CONSTRAINT `fk_receptions_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_receptions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des détails de réception
CREATE TABLE `reception_details` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `reception_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL,
    `unit_price_gnf` DECIMAL(18,2) NOT NULL,
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_reception_detail` (`reception_id`, `stock_item_id`),
    INDEX `idx_receptiondetail_reception` (`reception_id`),
    INDEX `idx_receptiondetail_item` (`stock_item_id`),
    CONSTRAINT `fk_receptiondetails_reception` FOREIGN KEY (`reception_id`) REFERENCES `receptions` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_receptiondetails_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des sorties de stock
CREATE TABLE `stock_outgoings` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `reference` VARCHAR(50) NOT NULL,
    `outgoing_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `depot_id` BIGINT UNSIGNED,
    `vehicle_id` BIGINT UNSIGNED,
    `client_name` VARCHAR(120),
    `commercial_id` BIGINT UNSIGNED,
    `user_id` BIGINT UNSIGNED,
    `notes` TEXT,
    `status` ENUM('draft', 'completed', 'cancelled') NOT NULL DEFAULT 'draft',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_outgoings_reference` (`reference`),
    INDEX `idx_outgoing_date` (`outgoing_date`),
    INDEX `idx_outgoing_depot` (`depot_id`),
    INDEX `idx_outgoing_vehicle` (`vehicle_id`),
    INDEX `idx_outgoing_status` (`status`),
    CONSTRAINT `fk_outgoings_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_outgoings_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_outgoings_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des détails de sortie
CREATE TABLE `stock_outgoing_details` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `outgoing_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL,
    `unit_price_gnf` DECIMAL(18,2),
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_outgoing_detail` (`outgoing_id`, `stock_item_id`),
    INDEX `idx_outgoingdetail_outgoing` (`outgoing_id`),
    INDEX `idx_outgoingdetail_item` (`stock_item_id`),
    CONSTRAINT `fk_outgoingdetails_outgoing` FOREIGN KEY (`outgoing_id`) REFERENCES `stock_outgoings` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_outgoingdetails_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des retours de stock
CREATE TABLE `stock_returns` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `reference` VARCHAR(50) NOT NULL,
    `return_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `depot_id` BIGINT UNSIGNED,
    `vehicle_id` BIGINT UNSIGNED,
    `client_name` VARCHAR(120),
    `commercial_id` BIGINT UNSIGNED,
    `user_id` BIGINT UNSIGNED,
    `notes` TEXT,
    `status` ENUM('draft', 'completed', 'cancelled') NOT NULL DEFAULT 'draft',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_returns_reference` (`reference`),
    INDEX `idx_return_date` (`return_date`),
    INDEX `idx_return_depot` (`depot_id`),
    INDEX `idx_return_vehicle` (`vehicle_id`),
    INDEX `idx_return_status` (`status`),
    CONSTRAINT `fk_returns_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_returns_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_returns_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des détails de retour
CREATE TABLE `stock_return_details` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `return_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `quantity` DECIMAL(18,4) NOT NULL,
    `unit_price_gnf` DECIMAL(18,2),
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_return_detail` (`return_id`, `stock_item_id`),
    INDEX `idx_returndetail_return` (`return_id`),
    INDEX `idx_returndetail_item` (`stock_item_id`),
    CONSTRAINT `fk_returndetails_return` FOREIGN KEY (`return_id`) REFERENCES `stock_returns` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_returndetails_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des sessions d'inventaire
CREATE TABLE `inventory_sessions` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `session_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `depot_id` BIGINT UNSIGNED NOT NULL,
    `operator_id` BIGINT UNSIGNED,
    `status` ENUM('draft', 'in_progress', 'completed', 'validated') NOT NULL DEFAULT 'draft',
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    `validated_at` DATETIME,
    `validated_by_id` BIGINT UNSIGNED,
    PRIMARY KEY (`id`),
    INDEX `idx_inventory_date` (`session_date`),
    INDEX `idx_inventory_depot` (`depot_id`),
    INDEX `idx_inventory_status` (`status`),
    CONSTRAINT `fk_inventorysessions_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_inventorysessions_operator` FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_inventorysessions_validator` FOREIGN KEY (`validated_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des détails d'inventaire
CREATE TABLE `inventory_details` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `session_id` BIGINT UNSIGNED NOT NULL,
    `stock_item_id` BIGINT UNSIGNED NOT NULL,
    `system_quantity` DECIMAL(18,4) NOT NULL,
    `counted_quantity` DECIMAL(18,4) NOT NULL,
    `pile_dimensions` VARCHAR(100),
    `variance` DECIMAL(18,4) NOT NULL,
    `reason` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_inventory_detail` (`session_id`, `stock_item_id`),
    INDEX `idx_inventorydetail_session` (`session_id`),
    INDEX `idx_inventorydetail_item` (`stock_item_id`),
    CONSTRAINT `fk_inventorydetails_session` FOREIGN KEY (`session_id`) REFERENCES `inventory_sessions` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_inventorydetails_item` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_items` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des documents véhicule
CREATE TABLE `vehicle_documents` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vehicle_id` BIGINT UNSIGNED NOT NULL,
    `document_type` ENUM('insurance', 'registration', 'technical_inspection', 'road_tax', 'license', 'other') NOT NULL,
    `document_number` VARCHAR(100),
    `issue_date` DATE,
    `expiry_date` DATE NOT NULL,
    `attachment_url` VARCHAR(500),
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_vehicledoc_vehicle` (`vehicle_id`),
    INDEX `idx_vehicledoc_type` (`document_type`),
    INDEX `idx_vehicledoc_expiry` (`expiry_date`),
    CONSTRAINT `fk_vehicledocuments_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des maintenances véhicule
CREATE TABLE `vehicle_maintenances` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vehicle_id` BIGINT UNSIGNED NOT NULL,
    `maintenance_type` VARCHAR(50) NOT NULL,
    `status` ENUM('planned', 'completed', 'cancelled') NOT NULL DEFAULT 'planned',
    `planned_date` DATE,
    `completed_date` DATE,
    `due_at_km` INT,
    `cost_gnf` DECIMAL(18,2),
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_vehiclemaint_vehicle` (`vehicle_id`),
    INDEX `idx_vehiclemaint_status` (`status`),
    INDEX `idx_vehiclemaint_planned` (`planned_date`),
    CONSTRAINT `fk_vehiclemaintenances_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des relevés odomètre
CREATE TABLE `vehicle_odometers` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vehicle_id` BIGINT UNSIGNED NOT NULL,
    `reading_date` DATE NOT NULL,
    `odometer_km` INT NOT NULL,
    `source` ENUM('manual', 'gps', 'system') NOT NULL DEFAULT 'manual',
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_vehicleodo_vehicle` (`vehicle_id`),
    INDEX `idx_vehicleodo_date` (`reading_date`),
    CONSTRAINT `fk_vehicleodometers_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. INITIALISATION DES DONNÉES
-- =====================================================

-- Initialiser les rôles
INSERT INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`) VALUES
('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW()),
('Magasinier', 'warehouse', '{"stocks": ["read", "create", "update"], "movements": ["read", "create"], "inventory": ["read", "create", "update"], "vehicles": ["read"], "regions": ["read"], "depots": ["read"], "families": ["read"], "stock_items": ["read"]}', 'Gestion des réceptions, transferts et inventaires', NOW()),
('Commercial', 'commercial', '{"stocks": ["read"], "vehicles": ["read"], "simulations": ["read", "create"], "regions": ["read"], "depots": ["read"], "families": ["read"], "stock_items": ["read"]}', 'Consultation stock véhicule, demandes de réassort', NOW()),
('Superviseur', 'supervisor', '{"stocks": ["read"], "inventory": ["read", "validate"], "vehicles": ["read", "update"], "reports": ["read"], "regions": ["read"], "depots": ["read"], "families": ["read"], "stock_items": ["read"]}', 'Suivi régional, KPI, validation inventaires', NOW());

-- Créer l'utilisateur admin
-- Hash du mot de passe 'admin123' généré avec Werkzeug
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);
SET @admin_password_hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`) VALUES
('admin', 'admin@importprofit.pro', @admin_password_hash, 'Administrateur', @admin_role_id, 1, NOW());

-- Initialiser les catégories
INSERT INTO `categories` (`name`, `description`, `created_at`) VALUES
('Électronique', 'Appareils électroniques et gadgets', NOW()),
('Informatique', 'Ordinateurs, tablettes, accessoires', NOW()),
('Textile', 'Vêtements et tissus', NOW()),
('Chaussures', 'Chaussures et accessoires', NOW()),
('Maroquinerie', 'Sacs, portefeuilles, accessoires cuir', NOW()),
('Électroménager', 'Appareils électroménagers', NOW()),
('Mobilier', 'Meubles et décoration', NOW()),
('Autre', 'Autres catégories', NOW());

-- Ajouter quelques articles de démonstration
SET @cat_electronique = (SELECT id FROM categories WHERE name = 'Électronique' LIMIT 1);
SET @cat_informatique = (SELECT id FROM categories WHERE name = 'Informatique' LIMIT 1);
SET @cat_textile = (SELECT id FROM categories WHERE name = 'Textile' LIMIT 1);
SET @cat_chaussures = (SELECT id FROM categories WHERE name = 'Chaussures' LIMIT 1);

INSERT INTO `articles` (`name`, `category_id`, `purchase_price`, `purchase_currency`, `unit_weight_kg`, `is_active`, `created_at`) VALUES
('Smartphone Samsung Galaxy S24', @cat_electronique, 150.00, 'USD', 0.2, 1, NOW()),
('Ordinateur Portable Dell XPS', @cat_informatique, 800.00, 'USD', 2.5, 1, NOW()),
('Vêtements Importés Premium', @cat_textile, 25.00, 'EUR', 0.5, 1, NOW()),
('Chaussures Nike Air Max', @cat_chaussures, 80.00, 'USD', 0.8, 1, NOW());

-- =====================================================
-- 4. VÉRIFICATION
-- =====================================================

SELECT '=== INITIALISATION TERMINÉE ===' as '';
SELECT '✅ Tables créées' as '';
SELECT '✅ Rôles initialisés' as '';
SELECT '✅ Utilisateur admin créé' as '';
SELECT '✅ Catégories initialisées' as '';
SELECT '✅ Articles de démonstration ajoutés' as '';

SELECT '=== VÉRIFICATION ===' as '';
SELECT COUNT(*) as total_roles FROM roles;
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(*) as total_categories FROM categories;
SELECT COUNT(*) as total_articles FROM articles;

SELECT '=== UTILISATEUR ADMIN ===' as '';
SELECT 
    u.id,
    u.username,
    u.email,
    r.name as role_name,
    r.code as role_code,
    u.is_active,
    CASE 
        WHEN u.password_hash IS NOT NULL AND u.password_hash != '' 
        THEN CONCAT('✅ Hash OK (', LENGTH(u.password_hash), ' chars)')
        ELSE '❌ Pas de hash'
    END as password_status
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

SELECT '=== IDENTIFIANTS DE CONNEXION ===' as '';
SELECT 'Username: admin' as '';
SELECT 'Password: admin123' as '';
SELECT 'URL: http://localhost:5002/auth/login' as '';

SELECT '✅ Base de données initialisée avec succès!' as '';

