-- Script pour ajouter les colonnes manquantes dans la base de données madargn
-- À exécuter directement dans MySQL: mysql -u root -p madargn < fix_missing_columns.sql

USE madargn;

-- Ajouter les colonnes manquantes dans la table 'roles'
-- Note: Si les colonnes existent déjà, ces commandes échoueront mais ce n'est pas grave
ALTER TABLE `roles` ADD COLUMN `code` VARCHAR(20) NULL AFTER `name`;
ALTER TABLE `roles` ADD COLUMN `permissions` JSON NULL;
ALTER TABLE `roles` ADD COLUMN `description` TEXT NULL;
ALTER TABLE `roles` ADD COLUMN `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE `roles` ADD COLUMN `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP;

-- Ajouter les colonnes manquantes dans la table 'users'
ALTER TABLE `users` ADD COLUMN `username` VARCHAR(80) NULL AFTER `id`;
ALTER TABLE `users` ADD COLUMN `email` VARCHAR(120) NULL AFTER `username`;
ALTER TABLE `users` ADD COLUMN `password_hash` VARCHAR(255) NULL AFTER `email`;
ALTER TABLE `users` ADD COLUMN `full_name` VARCHAR(120) NULL AFTER `password_hash`;
ALTER TABLE `users` ADD COLUMN `phone` VARCHAR(20) NULL AFTER `full_name`;
ALTER TABLE `users` ADD COLUMN `role_id` BIGINT UNSIGNED NULL AFTER `phone`;
ALTER TABLE `users` ADD COLUMN `is_active` TINYINT(1) NOT NULL DEFAULT 1 AFTER `role_id`;
ALTER TABLE `users` ADD COLUMN `last_login` DATETIME NULL AFTER `is_active`;
ALTER TABLE `users` ADD COLUMN `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE `users` ADD COLUMN `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP;

-- Ajouter les index uniques
CREATE UNIQUE INDEX `idx_user_username` ON `users`(`username`);
CREATE UNIQUE INDEX `idx_user_email` ON `users`(`email`);
CREATE INDEX `idx_user_role` ON `users`(`role_id`);
CREATE INDEX `idx_role_code` ON `roles`(`code`);

SELECT 'Colonnes ajoutées avec succès!' as message;
