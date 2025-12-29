-- Script pour ajouter les colonnes manquantes à la table simulations
-- Exécuter avec: mysql -u root -p madargn < scripts/add_rate_xof_and_columns.sql
-- OU: mysql -u root -p import_profit < scripts/add_rate_xof_and_columns.sql

-- Utiliser la base de données appropriée (remplacer par votre base de données)
-- USE madargn;
-- OU
-- USE import_profit;

-- Vérifier et ajouter rate_xof
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'rate_xof');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN rate_xof DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER rate_eur',
    'SELECT "Colonne rate_xof existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter customs_gnf
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'customs_gnf');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN customs_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER rate_xof',
    'SELECT "Colonne customs_gnf existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter handling_gnf
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'handling_gnf');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN handling_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER customs_gnf',
    'SELECT "Colonne handling_gnf existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter others_gnf
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'others_gnf');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN others_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER handling_gnf',
    'SELECT "Colonne others_gnf existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter transport_fixed_gnf
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'transport_fixed_gnf');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN transport_fixed_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER others_gnf',
    'SELECT "Colonne transport_fixed_gnf existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter transport_per_kg_gnf
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'transport_per_kg_gnf');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN transport_per_kg_gnf DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER transport_fixed_gnf',
    'SELECT "Colonne transport_per_kg_gnf existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter basis
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'basis');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN basis ENUM(\'value\', \'weight\') NOT NULL DEFAULT \'value\' AFTER transport_per_kg_gnf',
    'SELECT "Colonne basis existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter truck_capacity_tons
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'truck_capacity_tons');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN truck_capacity_tons DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER basis',
    'SELECT "Colonne truck_capacity_tons existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter target_mode
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'target_mode');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN target_mode ENUM(\'none\', \'price\', \'purchase\', \'global\') NOT NULL DEFAULT \'none\' AFTER truck_capacity_tons',
    'SELECT "Colonne target_mode existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier et ajouter target_margin_pct
SET @db_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
                  WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'simulations' 
                  AND COLUMN_NAME = 'target_margin_pct');

SET @sql = IF(@db_exists = 0,
    'ALTER TABLE simulations ADD COLUMN target_margin_pct DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER target_mode',
    'SELECT "Colonne target_margin_pct existe déjà" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier les colonnes ajoutées
SHOW COLUMNS FROM simulations;

