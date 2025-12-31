-- Script pour ajouter la colonne additional_permissions à la table users
-- Permet d'attribuer des permissions supplémentaires aux utilisateurs RH
-- À exécuter directement dans MySQL: mysql -u root -p madargn < scripts/add_additional_permissions_column.sql

USE madargn;

-- Ajouter la colonne additional_permissions si elle n'existe pas
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND COLUMN_NAME = 'additional_permissions'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `users` ADD COLUMN `additional_permissions` JSON NULL AFTER `last_login`',
    'SELECT "La colonne additional_permissions existe déjà" as message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Colonne additional_permissions ajoutée avec succès!' as message;

