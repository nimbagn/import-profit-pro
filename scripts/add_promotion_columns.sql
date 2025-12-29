-- =========================================================
-- MIGRATION : Ajout des colonnes pour géolocalisation et intermédiaire
-- Date : 24 Novembre 2025
-- =========================================================

-- Ajouter les colonnes de géolocalisation à promotion_members
ALTER TABLE `promotion_members` 
ADD COLUMN `latitude` DECIMAL(10, 8) NULL AFTER `address`,
ADD COLUMN `longitude` DECIMAL(11, 8) NULL AFTER `latitude`,
ADD COLUMN `intermediary_id` BIGINT UNSIGNED NULL AFTER `longitude`;

-- Ajouter l'index pour l'intermédiaire
ALTER TABLE `promotion_members`
ADD INDEX `idx_promomember_intermediary` (`intermediary_id`),
ADD INDEX `idx_promomember_location` (`latitude`, `longitude`);

-- Ajouter la contrainte de clé étrangère pour l'intermédiaire
ALTER TABLE `promotion_members`
ADD CONSTRAINT `fk_promomember_intermediary` 
FOREIGN KEY (`intermediary_id`) REFERENCES `promotion_members` (`id`) 
ON UPDATE CASCADE ON DELETE SET NULL;

-- =========================================================
-- Création de la table de liaison promotion_gamme_articles
-- =========================================================

CREATE TABLE IF NOT EXISTS `promotion_gamme_articles` (
    `gamme_id` BIGINT UNSIGNED NOT NULL,
    `article_id` BIGINT UNSIGNED NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`gamme_id`, `article_id`),
    INDEX `idx_gamme_article` (`gamme_id`, `article_id`),
    CONSTRAINT `fk_gamme_articles_gamme` 
        FOREIGN KEY (`gamme_id`) REFERENCES `promotion_gammes` (`id`) 
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_gamme_articles_article` 
        FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) 
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

