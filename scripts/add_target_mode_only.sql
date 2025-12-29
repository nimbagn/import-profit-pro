-- Script pour ajouter uniquement la colonne target_mode manquante
-- Exécuter avec: mysql -u root -p madargn < scripts/add_target_mode_only.sql

USE madargn;

-- Ajouter target_mode seulement si elle n'existe pas
SET @db_exists = (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'madargn' AND TABLE_NAME = 'simulations');

SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'simulations' 
    AND COLUMN_NAME = 'target_mode'
);

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE simulations ADD COLUMN target_mode ENUM(\'none\', \'price\', \'purchase\', \'global\') NOT NULL DEFAULT \'none\' AFTER truck_capacity_tons',
    'SELECT "Colonne target_mode existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérifier les colonnes
SHOW COLUMNS FROM simulations LIKE 'target_mode';

