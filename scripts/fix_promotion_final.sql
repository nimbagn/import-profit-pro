-- =========================================================
-- Script SQL pour corriger les colonnes de promotion_members
-- Exécutez avec: mysql -u root -p madargn < scripts/fix_promotion_final.sql
-- =========================================================

USE madargn;

-- Supprimer les anciens index s'ils existent
SET @sql = (
    SELECT CONCAT('ALTER TABLE `promotion_members` DROP INDEX `', INDEX_NAME, '`')
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members'
    AND INDEX_NAME LIKE '%intermediary%'
    LIMIT 1
);

SET @sql = IF(@sql IS NOT NULL, @sql, 'SELECT "Aucun ancien index à supprimer" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Supprimer les anciennes FK s'ils existent
SET @sql = (
    SELECT CONCAT('ALTER TABLE `promotion_members` DROP FOREIGN KEY `', CONSTRAINT_NAME, '`')
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members'
    AND CONSTRAINT_NAME LIKE '%intermediary%'
    LIMIT 1
);

SET @sql = IF(@sql IS NOT NULL, @sql, 'SELECT "Aucune ancienne FK à supprimer" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Renommer intermediary_id en intermediaire_id si elle existe
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'intermediary_id'
);

SET @sql = IF(@col_exists > 0,
    'ALTER TABLE `promotion_members` CHANGE COLUMN `intermediary_id` `intermediaire_id` BIGINT UNSIGNED NULL',
    'SELECT "Colonne intermediary_id n''existe pas" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter home_latitude si elle n'existe pas
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'home_latitude'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `promotion_members` ADD COLUMN `home_latitude` DECIMAL(10, 8) NULL AFTER `address`',
    'SELECT "Colonne home_latitude existe déjà" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter home_longitude si elle n'existe pas
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'home_longitude'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `promotion_members` ADD COLUMN `home_longitude` DECIMAL(11, 8) NULL AFTER `home_latitude`',
    'SELECT "Colonne home_longitude existe déjà" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter intermediaire_id si elle n'existe pas
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND COLUMN_NAME = 'intermediaire_id'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `promotion_members` ADD COLUMN `intermediaire_id` BIGINT UNSIGNED NULL AFTER `home_longitude`',
    'SELECT "Colonne intermediaire_id existe déjà" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer l'index intermediaire
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND INDEX_NAME = 'idx_promomember_intermediary'
);

SET @sql = IF(@idx_exists = 0,
    'ALTER TABLE `promotion_members` ADD INDEX `idx_promomember_intermediary` (`intermediaire_id`)',
    'SELECT "Index idx_promomember_intermediary existe déjà" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer l'index location
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND INDEX_NAME = 'idx_promomember_location'
);

SET @sql = IF(@idx_exists = 0,
    'ALTER TABLE `promotion_members` ADD INDEX `idx_promomember_location` (`home_latitude`, `home_longitude`)',
    'SELECT "Index idx_promomember_location existe déjà" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer la contrainte FK
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'promotion_members' 
    AND CONSTRAINT_NAME = 'fk_promomember_intermediary'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE `promotion_members` ADD CONSTRAINT `fk_promomember_intermediary` FOREIGN KEY (`intermediaire_id`) REFERENCES `promotion_members` (`id`) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT "Contrainte FK existe déjà" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT '✅ Script de correction terminé avec succès!' AS result;

