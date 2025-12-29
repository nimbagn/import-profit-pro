-- Script sécurisé pour ajouter uniquement les colonnes manquantes
-- Exécuter avec: mysql -u root -p madargn < scripts/add_missing_columns_safe.sql

USE madargn;

-- Fonction pour ajouter une colonne seulement si elle n'existe pas
DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_not_exists$$
CREATE PROCEDURE add_column_if_not_exists(
    IN table_name VARCHAR(64),
    IN column_name VARCHAR(64),
    IN column_definition TEXT
)
BEGIN
    DECLARE column_count INT;
    
    SELECT COUNT(*) INTO column_count
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = table_name
    AND COLUMN_NAME = column_name;
    
    IF column_count = 0 THEN
        SET @sql = CONCAT('ALTER TABLE ', table_name, ' ADD COLUMN ', column_name, ' ', column_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('Colonne ', column_name, ' ajoutée') AS message;
    ELSE
        SELECT CONCAT('Colonne ', column_name, ' existe déjà') AS message;
    END IF;
END$$

DELIMITER ;

-- Ajouter les colonnes manquantes
CALL add_column_if_not_exists('simulations', 'rate_xof', 'DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER rate_eur');
CALL add_column_if_not_exists('simulations', 'customs_gnf', 'DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER rate_xof');
CALL add_column_if_not_exists('simulations', 'handling_gnf', 'DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER customs_gnf');
CALL add_column_if_not_exists('simulations', 'others_gnf', 'DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER handling_gnf');
CALL add_column_if_not_exists('simulations', 'transport_fixed_gnf', 'DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER others_gnf');
CALL add_column_if_not_exists('simulations', 'transport_per_kg_gnf', 'DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER transport_fixed_gnf');
CALL add_column_if_not_exists('simulations', 'basis', 'ENUM(\'value\', \'weight\') NOT NULL DEFAULT \'value\' AFTER transport_per_kg_gnf');
CALL add_column_if_not_exists('simulations', 'truck_capacity_tons', 'DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER basis');
CALL add_column_if_not_exists('simulations', 'target_mode', 'ENUM(\'none\', \'price\', \'purchase\', \'global\') NOT NULL DEFAULT \'none\' AFTER truck_capacity_tons');
CALL add_column_if_not_exists('simulations', 'target_margin_pct', 'DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER target_mode');

-- Nettoyer
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

-- Vérifier les colonnes
SHOW COLUMNS FROM simulations;

