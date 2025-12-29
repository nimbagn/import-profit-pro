-- Migration: Création de la table password_reset_tokens
-- Date: 2024
-- Description: Table pour stocker les tokens de réinitialisation de mot de passe

-- Créer la table password_reset_tokens
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `used` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_token_hash` (`token_hash`),
  KEY `idx_reset_token_hash` (`token_hash`),
  KEY `idx_reset_token_expires` (`expires_at`),
  KEY `idx_reset_token_user` (`user_id`),
  KEY `idx_reset_token_used` (`used`),
  CONSTRAINT `fk_reset_token_user` 
    FOREIGN KEY (`user_id`) 
    REFERENCES `users` (`id`) 
    ON DELETE CASCADE 
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Index supplémentaire pour les requêtes de nettoyage
CREATE INDEX `idx_reset_token_expires_used` ON `password_reset_tokens` (`expires_at`, `used`);

-- Commentaires
ALTER TABLE `password_reset_tokens` 
  COMMENT = 'Tokens de réinitialisation de mot de passe - Expiration 30 minutes, utilisation unique';

