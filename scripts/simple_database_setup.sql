-- =====================================================
-- SCRIPT SIMPLE DE CONFIGURATION DE LA BASE DE DONNÉES
-- IMPORT PROFIT PRO - MySQL
-- =====================================================

-- Utiliser la base de données madargn
USE madargn;

-- =====================================================
-- 1. SUPPRESSION DES TABLES EXISTANTES
-- =====================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `stock_items`;
DROP TABLE IF EXISTS `stock_movements`;
DROP TABLE IF EXISTS `inventory_items`;
DROP TABLE IF EXISTS `inventories`;
DROP TABLE IF EXISTS `simulation_items`;
DROP TABLE IF EXISTS `simulations`;
DROP TABLE IF EXISTS `forecast_items`;
DROP TABLE IF EXISTS `forecasts`;
DROP TABLE IF EXISTS `optimization_results`;
DROP TABLE IF EXISTS `articles`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `roles`;
DROP TABLE IF EXISTS `depots`;
DROP TABLE IF EXISTS `vehicles`;
DROP TABLE IF EXISTS `currencies`;
DROP TABLE IF EXISTS `exchange_rates`;
DROP TABLE IF EXISTS `regions`;

-- =====================================================
-- 2. CRÉATION DES TABLES DE BASE
-- =====================================================

-- Table des rôles
CREATE TABLE `roles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des utilisateurs
CREATE TABLE `users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `role_id` BIGINT UNSIGNED,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_users_email` (`email`),
    KEY `idx_users_role_id` (`role_id`),
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des catégories
CREATE TABLE `categories` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des articles
CREATE TABLE `articles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `category_id` BIGINT UNSIGNED NOT NULL,
    `purchase_price` DECIMAL(15,2) NOT NULL,
    `purchase_currency` VARCHAR(3) NOT NULL DEFAULT 'USD',
    `unit_weight_kg` DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    `selling_price` DECIMAL(15,2) DEFAULT NULL,
    `selling_currency` VARCHAR(3) DEFAULT 'GNF',
    `description` TEXT,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_articles_name` (`name`),
    KEY `idx_articles_category_id` (`category_id`),
    CONSTRAINT `fk_articles_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des dépôts
CREATE TABLE `depots` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `location` VARCHAR(200),
    `capacity_tons` DECIMAL(10,2) DEFAULT 0.00,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_depots_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des véhicules
CREATE TABLE `vehicles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `type` VARCHAR(50) NOT NULL,
    `capacity_tons` DECIMAL(10,2) NOT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_vehicles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des devises
CREATE TABLE `currencies` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `code` VARCHAR(3) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `symbol` VARCHAR(10),
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_currencies_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des taux de change
CREATE TABLE `exchange_rates` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `from_currency` VARCHAR(3) NOT NULL,
    `to_currency` VARCHAR(3) NOT NULL,
    `rate` DECIMAL(15,6) NOT NULL,
    `date` DATE NOT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_exchange_rates` (`from_currency`, `to_currency`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des régions
CREATE TABLE `regions` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `country` VARCHAR(100) NOT NULL,
    `code` VARCHAR(10),
    `population` INT DEFAULT 0,
    `description` TEXT,
    `status` VARCHAR(20) DEFAULT 'active',
    `priority` VARCHAR(20) DEFAULT 'medium',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_regions_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des simulations
CREATE TABLE `simulations` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `rate_usd` DECIMAL(10,2) NOT NULL,
    `rate_eur` DECIMAL(10,2) NOT NULL,
    `truck_capacity_tons` DECIMAL(10,2) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `total_value` DECIMAL(15,2) DEFAULT 0.00,
    `total_weight` DECIMAL(10,2) DEFAULT 0.00,
    `margin_pct` DECIMAL(5,2) DEFAULT 0.00,
    `created_by` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_simulations_status` (`status`),
    KEY `idx_simulations_created_by` (`created_by`),
    CONSTRAINT `fk_simulations_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des éléments de simulation
CREATE TABLE `simulation_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `simulation_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `unit_price` DECIMAL(15,2) NOT NULL,
    `total_price` DECIMAL(15,2) NOT NULL,
    `weight_kg` DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_simulation_items_simulation_id` (`simulation_id`),
    KEY `idx_simulation_items_article_id` (`article_id`),
    CONSTRAINT `fk_simulation_items_simulation` FOREIGN KEY (`simulation_id`) REFERENCES `simulations` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_simulation_items_article` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des inventaires
CREATE TABLE `inventories` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `depot_id` BIGINT UNSIGNED NOT NULL,
    `agent_name` VARCHAR(100) NOT NULL,
    `inventory_date` DATETIME NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `total_items` INT DEFAULT 0,
    `created_by` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_inventories_depot_id` (`depot_id`),
    KEY `idx_inventories_status` (`status`),
    KEY `idx_inventories_created_by` (`created_by`),
    CONSTRAINT `fk_inventories_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_inventories_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des éléments d'inventaire
CREATE TABLE `inventory_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `inventory_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `theoretical_quantity` INT NOT NULL DEFAULT 0,
    `physical_quantity` INT NOT NULL DEFAULT 0,
    `difference` INT NOT NULL DEFAULT 0,
    `counting_mode` VARCHAR(20) DEFAULT 'direct',
    `piles_data` JSON,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_inventory_items_inventory_id` (`inventory_id`),
    KEY `idx_inventory_items_article_id` (`article_id`),
    CONSTRAINT `fk_inventory_items_inventory` FOREIGN KEY (`inventory_id`) REFERENCES `inventories` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_inventory_items_article` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des mouvements de stock
CREATE TABLE `stock_movements` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `transfer_reference` VARCHAR(100) NOT NULL,
    `document_reference` VARCHAR(100),
    `from_depot_id` BIGINT UNSIGNED,
    `to_depot_id` BIGINT UNSIGNED,
    `vehicle_id` BIGINT UNSIGNED,
    `driver_name` VARCHAR(100),
    `movement_date` DATETIME NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `total_items` INT DEFAULT 0,
    `total_weight` DECIMAL(10,2) DEFAULT 0.00,
    `created_by` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_stock_movements_transfer_ref` (`transfer_reference`),
    KEY `idx_stock_movements_from_depot` (`from_depot_id`),
    KEY `idx_stock_movements_to_depot` (`to_depot_id`),
    KEY `idx_stock_movements_vehicle` (`vehicle_id`),
    KEY `idx_stock_movements_status` (`status`),
    KEY `idx_stock_movements_created_by` (`created_by`),
    CONSTRAINT `fk_stock_movements_from_depot` FOREIGN KEY (`from_depot_id`) REFERENCES `depots` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_stock_movements_to_depot` FOREIGN KEY (`to_depot_id`) REFERENCES `depots` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_stock_movements_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_stock_movements_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des éléments de mouvement de stock
CREATE TABLE `stock_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `movement_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `unit_weight_kg` DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    `total_weight_kg` DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_stock_items_movement_id` (`movement_id`),
    KEY `idx_stock_items_article_id` (`article_id`),
    CONSTRAINT `fk_stock_items_movement` FOREIGN KEY (`movement_id`) REFERENCES `stock_movements` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_stock_items_article` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des prévisions
CREATE TABLE `forecasts` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `forecast_date` DATE NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'draft',
    `total_value` DECIMAL(15,2) DEFAULT 0.00,
    `created_by` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_forecasts_status` (`status`),
    KEY `idx_forecasts_created_by` (`created_by`),
    CONSTRAINT `fk_forecasts_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des éléments de prévision
CREATE TABLE `forecast_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `forecast_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `predicted_quantity` INT NOT NULL DEFAULT 1,
    `predicted_price` DECIMAL(15,2) NOT NULL,
    `confidence_level` DECIMAL(5,2) DEFAULT 0.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_forecast_items_forecast_id` (`forecast_id`),
    KEY `idx_forecast_items_article_id` (`article_id`),
    CONSTRAINT `fk_forecast_items_forecast` FOREIGN KEY (`forecast_id`) REFERENCES `forecasts` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_forecast_items_article` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des résultats d'optimisation
CREATE TABLE `optimization_results` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `optimization_type` VARCHAR(50) NOT NULL,
    `parameters` JSON,
    `results` JSON,
    `status` VARCHAR(20) NOT NULL DEFAULT 'completed',
    `created_by` BIGINT UNSIGNED,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_optimization_results_type` (`optimization_type`),
    KEY `idx_optimization_results_status` (`status`),
    KEY `idx_optimization_results_created_by` (`created_by`),
    CONSTRAINT `fk_optimization_results_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. INSERTION DES DONNÉES DE BASE
-- =====================================================

-- Insertion des rôles
INSERT INTO `roles` (`name`, `description`) VALUES
('admin', 'Administrateur système'),
('manager', 'Gestionnaire'),
('user', 'Utilisateur standard'),
('inventory', 'Agent d\'inventaire');

-- Insertion des utilisateurs
INSERT INTO `users` (`name`, `email`, `password`, `role_id`, `is_active`) VALUES
('Admin Principal', 'admin@importprofit.com', 'admin123', 1, TRUE),
('Gestionnaire Stock', 'manager@importprofit.com', 'manager123', 2, TRUE),
('Agent Inventaire', 'inventory@importprofit.com', 'inventory123', 4, TRUE);

-- Insertion des catégories
INSERT INTO `categories` (`name`, `description`, `is_active`) VALUES
('Électronique', 'Appareils électroniques et accessoires', TRUE),
('Informatique', 'Ordinateurs, tablettes et accessoires', TRUE),
('Textile', 'Vêtements et tissus', TRUE),
('Chaussures', 'Chaussures et accessoires', TRUE),
('Maroquinerie', 'Sacs et accessoires en cuir', TRUE),
('Électroménager', 'Appareils électroménagers', TRUE),
('Mobilier', 'Meubles et décoration', TRUE),
('Autre', 'Autres produits', TRUE);

-- Insertion des dépôts
INSERT INTO `depots` (`name`, `location`, `capacity_tons`, `is_active`) VALUES
('Dépôt Principal', 'Conakry, Guinée', 100.00, TRUE),
('Dépôt Secondaire', 'Kankan, Guinée', 50.00, TRUE),
('Dépôt Nord', 'Labé, Guinée', 30.00, TRUE);

-- Insertion des véhicules
INSERT INTO `vehicles` (`name`, `type`, `capacity_tons`, `is_active`) VALUES
('Camion 25T', 'Camion', 25.00, TRUE),
('Camion 15T', 'Camion', 15.00, TRUE),
('Pickup', 'Véhicule léger', 2.00, TRUE);

-- Insertion des devises
INSERT INTO `currencies` (`code`, `name`, `symbol`, `is_active`) VALUES
('USD', 'Dollar américain', '$', TRUE),
('EUR', 'Euro', '€', TRUE),
('GNF', 'Franc guinéen', 'GNF', TRUE),
('XOF', 'Franc CFA', 'FCFA', TRUE);

-- Insertion des taux de change
INSERT INTO `exchange_rates` (`from_currency`, `to_currency`, `rate`, `date`, `is_active`) VALUES
('USD', 'GNF', 8500.00, CURDATE(), TRUE),
('EUR', 'GNF', 9200.00, CURDATE(), TRUE),
('USD', 'EUR', 0.92, CURDATE(), TRUE),
('EUR', 'USD', 1.09, CURDATE(), TRUE);

-- Insertion des régions
INSERT INTO `regions` (`name`, `country`, `code`, `population`, `description`, `status`, `priority`) VALUES
('Conakry', 'Guinée', 'CNK', 2000000, 'Capitale et région économique', 'active', 'high'),
('Kankan', 'Guinée', 'KNK', 500000, 'Région de l\'est', 'active', 'medium'),
('Labé', 'Guinée', 'LBE', 300000, 'Région du nord', 'active', 'medium'),
('Boké', 'Guinée', 'BKE', 200000, 'Région minière', 'active', 'high');

-- Insertion des articles de démonstration
INSERT INTO `articles` (`name`, `category_id`, `purchase_price`, `purchase_currency`, `unit_weight_kg`, `selling_price`, `selling_currency`, `description`, `is_active`) VALUES
('Smartphone Samsung Galaxy', 1, 150.00, 'USD', 0.200, 150000, 'GNF', 'Smartphone Android haut de gamme', TRUE),
('Ordinateur Portable Dell', 2, 800.00, 'USD', 2.500, 800000, 'GNF', 'Ordinateur portable professionnel', TRUE),
('Vêtements Importés', 3, 25.00, 'EUR', 0.500, 25000, 'GNF', 'Vêtements de qualité importés', TRUE),
('Chaussures Nike', 4, 80.00, 'USD', 0.800, 80000, 'GNF', 'Chaussures de sport Nike', TRUE),
('Sac en Cuir', 5, 120.00, 'EUR', 0.300, 120000, 'GNF', 'Sac à main en cuir véritable', TRUE),
('Réfrigérateur Samsung', 6, 400.00, 'USD', 50.000, 400000, 'GNF', 'Réfrigérateur 2 portes', TRUE),
('Table en Bois', 7, 200.00, 'USD', 25.000, 200000, 'GNF', 'Table à manger en bois massif', TRUE);

-- Réactiver les contraintes
SET FOREIGN_KEY_CHECKS = 1;

-- Afficher les tables créées
SHOW TABLES;

-- Compter les enregistrements
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'roles', COUNT(*) FROM roles
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'articles', COUNT(*) FROM articles
UNION ALL
SELECT 'depots', COUNT(*) FROM depots
UNION ALL
SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL
SELECT 'currencies', COUNT(*) FROM currencies
UNION ALL
SELECT 'exchange_rates', COUNT(*) FROM exchange_rates
UNION ALL
SELECT 'regions', COUNT(*) FROM regions;

SELECT 'Base de données configurée avec succès!' as message;
