-- Script d'ajout des champs de paiement et commentaires aux commandes clients
-- Import Profit Pro

-- Ajouter les colonnes de paiement et commentaires à commercial_order_clients
SET @col_payment_type = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'payment_type'
);

SET @sql = IF(@col_payment_type = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `payment_type` ENUM("cash", "credit") NOT NULL DEFAULT "cash" AFTER `client_address`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_payment_due_date = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'payment_due_date'
);

SET @sql = IF(@col_payment_due_date = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `payment_due_date` DATE NULL AFTER `payment_type`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_comments = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'commercial_order_clients' 
    AND COLUMN_NAME = 'comments'
);

SET @sql = IF(@col_comments = 0,
    'ALTER TABLE `commercial_order_clients` ADD COLUMN `comments` TEXT NULL AFTER `payment_due_date`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

