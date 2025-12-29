-- Script pour ajouter la colonne purchase_currency à la table articles si elle n'existe pas
-- Ce script vérifie d'abord si la colonne existe avant de l'ajouter

-- Vérifier et ajouter la colonne purchase_currency si elle n'existe pas
SET @db_name = DATABASE();
SET @table_name = 'articles';
SET @column_name = 'purchase_currency';

SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = @table_name 
    AND COLUMN_NAME = @column_name
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `articles` ADD COLUMN `purchase_currency` VARCHAR(8) NOT NULL DEFAULT ''USD'' AFTER `purchase_price`',
    'SELECT ''La colonne purchase_currency existe déjà'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

