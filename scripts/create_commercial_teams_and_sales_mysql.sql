-- =========================================================
-- SCRIPT DE MIGRATION : ÉQUIPES COMMERCIALES ET CONFIRMATION DES VENTES
-- =========================================================
-- Date : 2026-01-03
-- Description : Création des tables pour la gestion des équipes commerciales
--               (lockistes, vendeurs) et le système de confirmation des ventes
-- Compatible MySQL
-- =========================================================
-- IMPORTANT : Exécutez ce script dans votre base de données MySQL
-- =========================================================

-- =========================================================
-- 1. MODIFICATIONS TABLE USERS
-- =========================================================

-- Ajouter colonnes pour la supervision d'équipes (si elles n'existent pas)
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND COLUMN_NAME = 'supervised_team_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE users ADD COLUMN supervised_team_id BIGINT UNSIGNED NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND COLUMN_NAME = 'supervised_team_type');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE users ADD COLUMN supervised_team_type VARCHAR(20) NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer index pour supervised_team_id (si n'existe pas)
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND INDEX_NAME = 'idx_users_supervised_team');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_users_supervised_team ON users(supervised_team_id)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =========================================================
-- 2. MODIFICATIONS TABLE PROMOTION_TEAMS
-- =========================================================

-- Ajouter colonne supervisor_id
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_teams' 
    AND COLUMN_NAME = 'supervisor_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_teams ADD COLUMN supervisor_id BIGINT UNSIGNED NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter colonne region_id
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_teams' 
    AND COLUMN_NAME = 'region_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_teams ADD COLUMN region_id BIGINT UNSIGNED NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter contraintes FK
SET @fk_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_teams' 
    AND CONSTRAINT_NAME = 'promotion_teams_ibfk_supervisor');

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE promotion_teams ADD CONSTRAINT promotion_teams_ibfk_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @fk_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_teams' 
    AND CONSTRAINT_NAME = 'promotion_teams_ibfk_region');

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE promotion_teams ADD CONSTRAINT promotion_teams_ibfk_region FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer index
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_teams' 
    AND INDEX_NAME = 'idx_promoteam_supervisor');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_promoteam_supervisor ON promotion_teams(supervisor_id)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_teams' 
    AND INDEX_NAME = 'idx_promoteam_region_id');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_promoteam_region_id ON promotion_teams(region_id)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =========================================================
-- 2.5. MODIFICATIONS TABLE PROMOTION_MEMBERS
-- =========================================================

-- Ajouter colonnes de géolocalisation (si elles n'existent pas)
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'home_latitude');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_members ADD COLUMN home_latitude DECIMAL(18,4) NULL AFTER address',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'home_longitude');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_members ADD COLUMN home_longitude DECIMAL(18,4) NULL AFTER home_latitude',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'intermediaire_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_members ADD COLUMN intermediaire_id BIGINT UNSIGNED NULL AFTER home_longitude',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter contrainte FK pour intermediaire_id
SET @fk_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_members' 
    AND CONSTRAINT_NAME = 'promotion_members_ibfk_intermediaire');

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE promotion_members ADD CONSTRAINT promotion_members_ibfk_intermediaire FOREIGN KEY (intermediaire_id) REFERENCES promotion_members(id) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer index pour géolocalisation
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_members' 
    AND INDEX_NAME = 'idx_promomember_location');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_promomember_location ON promotion_members(home_latitude, home_longitude)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer index pour intermediaire
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_members' 
    AND INDEX_NAME = 'idx_promomember_intermediary');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_promomember_intermediary ON promotion_members(intermediaire_id)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =========================================================
-- 3. TABLES ÉQUIPES LOCKISTES
-- =========================================================

CREATE TABLE IF NOT EXISTS lockiste_teams (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    region_id BIGINT UNSIGNED NULL,
    team_leader_id BIGINT UNSIGNED NOT NULL,
    supervisor_id BIGINT UNSIGNED NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (team_leader_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (supervisor_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_lockiste_team_name (name),
    INDEX idx_lockiste_team_leader (team_leader_id),
    INDEX idx_lockiste_team_supervisor (supervisor_id),
    INDEX idx_lockiste_team_region (region_id),
    INDEX idx_lockiste_team_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lockiste_members (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    team_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES lockiste_teams(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_lockiste_member_team (team_id),
    INDEX idx_lockiste_member_user (user_id),
    INDEX idx_lockiste_member_name (full_name),
    INDEX idx_lockiste_member_phone (phone),
    INDEX idx_lockiste_member_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 4. TABLES ÉQUIPES VANDEURS
-- =========================================================

CREATE TABLE IF NOT EXISTS vendeur_teams (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    region_id BIGINT UNSIGNED NULL,
    team_leader_id BIGINT UNSIGNED NOT NULL,
    supervisor_id BIGINT UNSIGNED NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (team_leader_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (supervisor_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_vendeur_team_name (name),
    INDEX idx_vendeur_team_leader (team_leader_id),
    INDEX idx_vendeur_team_supervisor (supervisor_id),
    INDEX idx_vendeur_team_region (region_id),
    INDEX idx_vendeur_team_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vendeur_members (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    team_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES vendeur_teams(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_vendeur_member_team (team_id),
    INDEX idx_vendeur_member_user (user_id),
    INDEX idx_vendeur_member_name (full_name),
    INDEX idx_vendeur_member_phone (phone),
    INDEX idx_vendeur_member_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 5. MODIFICATIONS TABLE COMMERCIAL_ORDERS
-- =========================================================

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_orders' 
    AND COLUMN_NAME = 'sale_confirmed');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE commercial_orders ADD COLUMN sale_confirmed BOOLEAN NOT NULL DEFAULT FALSE',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_orders' 
    AND COLUMN_NAME = 'sale_confirmed_at');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE commercial_orders ADD COLUMN sale_confirmed_at TIMESTAMP NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_orders' 
    AND COLUMN_NAME = 'sale_confirmed_by_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE commercial_orders ADD COLUMN sale_confirmed_by_id BIGINT UNSIGNED NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter contrainte FK
SET @fk_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_orders' 
    AND CONSTRAINT_NAME = 'commercial_orders_ibfk_sale_confirmed_by');

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE commercial_orders ADD CONSTRAINT commercial_orders_ibfk_sale_confirmed_by FOREIGN KEY (sale_confirmed_by_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer index
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_orders' 
    AND INDEX_NAME = 'idx_order_sale_confirmed');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_order_sale_confirmed ON commercial_orders(sale_confirmed)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_orders' 
    AND INDEX_NAME = 'idx_order_sale_confirmed_by');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_order_sale_confirmed_by ON commercial_orders(sale_confirmed_by_id)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =========================================================
-- 6. TABLE COMMERCIAL_SALES (VENTES FINALES CONFIRMÉES)
-- =========================================================

CREATE TABLE IF NOT EXISTS commercial_sales (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NULL,
    order_client_id BIGINT UNSIGNED NULL,
    commercial_id BIGINT UNSIGNED NOT NULL,
    supervisor_id BIGINT UNSIGNED NOT NULL,
    invoice_number VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL,
    sale_date DATE NOT NULL,
    total_amount_gnf DECIMAL(18,2) NOT NULL,
    payment_method ENUM('cash', 'credit', 'check', 'transfer') NOT NULL DEFAULT 'cash',
    payment_status ENUM('pending', 'partial', 'paid', 'overdue') NOT NULL DEFAULT 'pending',
    payment_due_date DATE NULL,
    confirmed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    status ENUM('confirmed', 'cancelled') NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES commercial_orders(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (order_client_id) REFERENCES commercial_order_clients(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (commercial_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (supervisor_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_commercial_sale_order (order_id),
    INDEX idx_commercial_sale_commercial (commercial_id),
    INDEX idx_commercial_sale_supervisor (supervisor_id),
    INDEX idx_commercial_sale_date (sale_date),
    INDEX idx_commercial_sale_invoice (invoice_number),
    INDEX idx_commercial_sale_status (status),
    INDEX idx_commercial_sale_payment_status (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 7. TABLE COMMERCIAL_SALE_ITEMS (DÉTAILS DES VENTES)
-- =========================================================

CREATE TABLE IF NOT EXISTS commercial_sale_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sale_id BIGINT UNSIGNED NOT NULL,
    stock_item_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(18,4) NOT NULL,
    unit_price_gnf DECIMAL(18,2) NOT NULL,
    total_price_gnf DECIMAL(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES commercial_sales(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_sale_item_sale (sale_id),
    INDEX idx_sale_item_stock (stock_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- 8. TABLE SALES_OBJECTIVES (OBJECTIFS DE VENTE)
-- =========================================================

CREATE TABLE IF NOT EXISTS sales_objectives (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    commercial_id BIGINT UNSIGNED NOT NULL,
    supervisor_id BIGINT UNSIGNED NOT NULL,
    forecast_id BIGINT UNSIGNED NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    target_amount_gnf DECIMAL(18,2) NOT NULL,
    target_quantity DECIMAL(18,4) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (commercial_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (supervisor_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (forecast_id) REFERENCES forecasts(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_objective_commercial (commercial_id),
    INDEX idx_objective_supervisor (supervisor_id),
    INDEX idx_objective_forecast (forecast_id),
    INDEX idx_objective_period (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ajouter colonne forecast_id si la table existe déjà
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'sales_objectives' 
    AND COLUMN_NAME = 'forecast_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE sales_objectives ADD COLUMN forecast_id BIGINT UNSIGNED NULL AFTER supervisor_id',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter contrainte FK pour forecast_id si elle n'existe pas
SET @fk_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'sales_objectives' 
    AND CONSTRAINT_NAME = 'sales_objectives_ibfk_forecast');

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE sales_objectives ADD CONSTRAINT sales_objectives_ibfk_forecast FOREIGN KEY (forecast_id) REFERENCES forecasts(id) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer index pour forecast_id si n'existe pas
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'sales_objectives' 
    AND INDEX_NAME = 'idx_objective_forecast');

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_objective_forecast ON sales_objectives(forecast_id)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =========================================================
-- 9. TABLE SALES_OBJECTIVE_ITEMS (ARTICLES DES OBJECTIFS)
-- =========================================================

CREATE TABLE IF NOT EXISTS sales_objective_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    objective_id BIGINT UNSIGNED NOT NULL,
    stock_item_id BIGINT UNSIGNED NOT NULL,
    target_quantity DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    selling_price_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (objective_id) REFERENCES sales_objectives(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE KEY uq_objective_item (objective_id, stock_item_id),
    INDEX idx_objectiveitem_objective (objective_id),
    INDEX idx_objectiveitem_stock (stock_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
