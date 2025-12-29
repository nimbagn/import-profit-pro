-- =========================================================
-- Script SQL simple pour corriger les tables de promotion
-- Exécutez ce script avec: mysql -u root -p madargn < scripts/fix_promotion_simple.sql
-- =========================================================

USE madargn;

-- Vérifier et ajouter les colonnes manquantes dans promotion_members
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

-- Ajouter les index
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

-- Ajouter la contrainte FK
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

-- Créer la table promotion_gamme_articles si elle n'existe pas
CREATE TABLE IF NOT EXISTS `promotion_gamme_articles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `gamme_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_gamme_article` (`gamme_id`, `article_id`),
    INDEX `idx_promogammearticle_gamme` (`gamme_id`),
    INDEX `idx_promogammearticle_article` (`article_id`),
    CONSTRAINT `fk_gamme_articles_gamme` 
        FOREIGN KEY (`gamme_id`) REFERENCES `promotion_gammes` (`id`) 
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_gamme_articles_article` 
        FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) 
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT '✅ Script de migration terminé avec succès!' AS result;

