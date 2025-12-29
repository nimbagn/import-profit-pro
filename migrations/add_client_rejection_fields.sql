-- Migration: Ajout des champs pour le rejet de clients individuels
-- Date: 2025-12-21
-- Description: Permet de rejeter un client individuel dans une commande au lieu de rejeter toute la commande

-- Vérifier si les colonnes existent déjà avant de les ajouter
SET @col_status_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'status'
);

SET @col_rejection_reason_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'rejection_reason'
);

SET @col_rejected_by_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'rejected_by_id'
);

SET @col_rejected_at_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'rejected_at'
);

-- Ajouter la colonne status si elle n'existe pas
SET @sql_status = IF(@col_status_exists = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `status` ENUM(\'pending\', \'approved\', \'rejected\') NOT NULL DEFAULT \'pending\' AFTER `comments`',
    'SELECT "Colonne status existe déjà" AS message');
PREPARE stmt FROM @sql_status;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter la colonne rejection_reason si elle n'existe pas
SET @sql_rejection_reason = IF(@col_rejection_reason_exists = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `rejection_reason` TEXT NULL AFTER `status`',
    'SELECT "Colonne rejection_reason existe déjà" AS message');
PREPARE stmt FROM @sql_rejection_reason;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter la colonne rejected_by_id si elle n'existe pas
SET @sql_rejected_by = IF(@col_rejected_by_exists = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `rejected_by_id` BIGINT UNSIGNED NULL AFTER `rejection_reason`',
    'SELECT "Colonne rejected_by_id existe déjà" AS message');
PREPARE stmt FROM @sql_rejected_by;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter la colonne rejected_at si elle n'existe pas
SET @sql_rejected_at = IF(@col_rejected_at_exists = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `rejected_at` DATETIME NULL AFTER `rejected_by_id`',
    'SELECT "Colonne rejected_at existe déjà" AS message');
PREPARE stmt FROM @sql_rejected_at;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter l'index sur status s'il n'existe pas
SET @index_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND INDEX_NAME = 'idx_orderclient_status'
);

SET @sql_index = IF(@index_exists = 0,
    'ALTER TABLE `commercial_order_clients` ADD INDEX `idx_orderclient_status` (`status`)',
    'SELECT "Index idx_orderclient_status existe déjà" AS message');
PREPARE stmt FROM @sql_index;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter la contrainte de clé étrangère si elle n'existe pas
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND CONSTRAINT_NAME = 'fk_orderclient_rejected_by'
);

SET @sql_fk = IF(@fk_exists = 0,
    'ALTER TABLE `commercial_order_clients` ADD CONSTRAINT `fk_orderclient_rejected_by` FOREIGN KEY (`rejected_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT "Contrainte fk_orderclient_rejected_by existe déjà" AS message');
PREPARE stmt FROM @sql_fk;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Migration terminée avec succès' AS result;

