-- Script de création de la table vehicle_assignments
-- Historique des assignations de conducteurs aux véhicules

CREATE TABLE IF NOT EXISTS `vehicle_assignments` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vehicle_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NULL,
    `reason` VARCHAR(255) NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_by_id` BIGINT UNSIGNED NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_vehicleassignment_vehicle` (`vehicle_id`),
    INDEX `idx_vehicleassignment_user` (`user_id`),
    INDEX `idx_vehicleassignment_dates` (`start_date`, `end_date`),
    CONSTRAINT `fk_vehicleassignment_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_vehicleassignment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_vehicleassignment_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Si des véhicules ont déjà un conducteur assigné, créer une assignation initiale
INSERT INTO `vehicle_assignments` (`vehicle_id`, `user_id`, `start_date`, `reason`, `created_at`)
SELECT 
    `id` as `vehicle_id`,
    `current_user_id` as `user_id`,
    COALESCE(`acquisition_date`, `created_at`) as `start_date`,
    'Assignation initiale' as `reason`,
    NOW() as `created_at`
FROM `vehicles`
WHERE `current_user_id` IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM `vehicle_assignments` 
    WHERE `vehicle_assignments`.`vehicle_id` = `vehicles`.`id`
);

