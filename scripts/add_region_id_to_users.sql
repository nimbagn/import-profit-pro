-- Script pour ajouter la colonne region_id à la table users
-- Permet de gérer les utilisateurs par région

-- Vérifier si la colonne existe déjà
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'users'
    AND COLUMN_NAME = 'region_id'
);

-- Ajouter la colonne si elle n'existe pas
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `users` 
     ADD COLUMN `region_id` BIGINT UNSIGNED NULL AFTER `role_id`,
     ADD INDEX `idx_user_region` (`region_id`),
     ADD CONSTRAINT `fk_users_region` 
         FOREIGN KEY (`region_id`) 
         REFERENCES `regions` (`id`) 
         ON UPDATE CASCADE 
         ON DELETE SET NULL',
    'SELECT "La colonne region_id existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérification
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'users'
AND COLUMN_NAME = 'region_id';

