-- Migration: Ajout de la table user_activity_logs pour le suivi des interactions utilisateurs
-- Date: 2025-01-XX
-- Description: Table pour enregistrer toutes les activités et interactions des utilisateurs dans l'application

CREATE TABLE IF NOT EXISTS `user_activity_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `action` VARCHAR(100) NOT NULL,
    `module` VARCHAR(50) NULL,
    `activity_metadata` JSON NULL,
    `ip_address` VARCHAR(45) NULL,
    `user_agent` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_activity_user` (`user_id`),
    INDEX `idx_activity_action` (`action`),
    INDEX `idx_activity_module` (`module`),
    INDEX `idx_activity_created` (`created_at`),
    INDEX `idx_activity_user_action` (`user_id`, `action`),
    CONSTRAINT `fk_activity_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Commentaires
ALTER TABLE `user_activity_logs` COMMENT = 'Journal des activités et interactions des utilisateurs';

