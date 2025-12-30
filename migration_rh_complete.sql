-- Migration complète RH : Tables pour gestion du personnel et activités
-- Date: 2025-01-XX
-- Base de données: madargn

-- =========================================================
-- 1. TABLE user_activity_logs (si elle n'existe pas)
-- =========================================================
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

ALTER TABLE `user_activity_logs` COMMENT = 'Journal des activités et interactions des utilisateurs';

-- =========================================================
-- 2. TABLE employees (employés externes)
-- =========================================================
CREATE TABLE IF NOT EXISTS `employees` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_number` VARCHAR(50) NOT NULL,
    `first_name` VARCHAR(100) NOT NULL,
    `last_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NULL,
    `phone` VARCHAR(20) NULL,
    `phone_secondary` VARCHAR(20) NULL,
    `gender` ENUM('M', 'F') NULL,
    `date_of_birth` DATE NULL,
    `national_id` VARCHAR(50) NULL,
    `address` VARCHAR(500) NULL,
    `city` VARCHAR(100) NULL,
    `emergency_contact_name` VARCHAR(200) NULL,
    `emergency_contact_phone` VARCHAR(20) NULL,
    `emergency_contact_relation` VARCHAR(50) NULL,
    `department` VARCHAR(100) NULL,
    `position` VARCHAR(100) NULL,
    `manager_id` BIGINT UNSIGNED NULL,
    `region_id` BIGINT UNSIGNED NULL,
    `depot_id` BIGINT UNSIGNED NULL,
    `employment_status` ENUM('active', 'inactive', 'suspended', 'terminated', 'on_leave') NOT NULL DEFAULT 'active',
    `hire_date` DATE NULL,
    `termination_date` DATE NULL,
    `termination_reason` TEXT NULL,
    `user_id` BIGINT UNSIGNED NULL,
    `notes` TEXT NULL,
    `photo_path` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` BIGINT UNSIGNED NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_employee_number` (`employee_number`),
    UNIQUE KEY `uk_employee_user` (`user_id`),
    INDEX `idx_employee_number` (`employee_number`),
    INDEX `idx_employee_name` (`last_name`, `first_name`),
    INDEX `idx_employee_status` (`employment_status`),
    INDEX `idx_employee_department` (`department`),
    INDEX `idx_employee_position` (`position`),
    INDEX `idx_employee_national_id` (`national_id`),
    INDEX `idx_employee_hire_date` (`hire_date`),
    CONSTRAINT `fk_employee_manager` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_employee_region` FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_employee_depot` FOREIGN KEY (`depot_id`) REFERENCES `depots` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_employee_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_employee_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `employees` COMMENT = 'Employés sans accès à la plateforme mais suivis par le service RH';

-- =========================================================
-- 3. TABLE employee_contracts
-- =========================================================
CREATE TABLE IF NOT EXISTS `employee_contracts` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_id` BIGINT UNSIGNED NOT NULL,
    `contract_number` VARCHAR(50) NOT NULL,
    `contract_type` ENUM('cdi', 'cdd', 'stage', 'consultant', 'freelance') NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NULL,
    `salary` DECIMAL(18,2) NULL,
    `currency` VARCHAR(8) NOT NULL DEFAULT 'GNF',
    `position` VARCHAR(100) NULL,
    `department` VARCHAR(100) NULL,
    `status` ENUM('draft', 'active', 'expired', 'terminated') NOT NULL DEFAULT 'draft',
    `termination_date` DATE NULL,
    `termination_reason` TEXT NULL,
    `notes` TEXT NULL,
    `document_path` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` BIGINT UNSIGNED NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_contract_number` (`contract_number`),
    INDEX `idx_contract_employee` (`employee_id`),
    INDEX `idx_contract_status` (`status`),
    INDEX `idx_contract_dates` (`start_date`, `end_date`),
    CONSTRAINT `fk_contract_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_contract_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `employee_contracts` COMMENT = 'Contrats des employés';

-- =========================================================
-- 4. TABLE employee_trainings
-- =========================================================
CREATE TABLE IF NOT EXISTS `employee_trainings` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_id` BIGINT UNSIGNED NOT NULL,
    `training_name` VARCHAR(200) NOT NULL,
    `training_type` ENUM('internal', 'external', 'online', 'certification') NOT NULL,
    `provider` VARCHAR(200) NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NULL,
    `duration_hours` INT NULL,
    `status` ENUM('planned', 'in_progress', 'completed', 'cancelled') NOT NULL DEFAULT 'planned',
    `cost` DECIMAL(18,2) NULL,
    `currency` VARCHAR(8) NOT NULL DEFAULT 'GNF',
    `certificate_obtained` TINYINT(1) NOT NULL DEFAULT 0,
    `certificate_path` VARCHAR(500) NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` BIGINT UNSIGNED NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_training_employee` (`employee_id`),
    INDEX `idx_training_status` (`status`),
    INDEX `idx_training_dates` (`start_date`, `end_date`),
    CONSTRAINT `fk_training_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_training_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `employee_trainings` COMMENT = 'Formations suivies par les employés';

-- =========================================================
-- 5. TABLE employee_evaluations
-- =========================================================
CREATE TABLE IF NOT EXISTS `employee_evaluations` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_id` BIGINT UNSIGNED NOT NULL,
    `evaluation_type` ENUM('annual', 'probation', 'mid_year', 'project', 'custom') NOT NULL,
    `evaluation_date` DATE NOT NULL,
    `evaluator_id` BIGINT UNSIGNED NULL,
    `overall_rating` ENUM('excellent', 'very_good', 'good', 'satisfactory', 'needs_improvement', 'unsatisfactory') NULL,
    `overall_score` DECIMAL(18,2) NULL,
    `strengths` TEXT NULL,
    `areas_for_improvement` TEXT NULL,
    `goals` TEXT NULL,
    `comments` TEXT NULL,
    `status` ENUM('draft', 'submitted', 'reviewed', 'approved') NOT NULL DEFAULT 'draft',
    `document_path` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` BIGINT UNSIGNED NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_evaluation_employee` (`employee_id`),
    INDEX `idx_evaluation_date` (`evaluation_date`),
    INDEX `idx_evaluation_status` (`status`),
    CONSTRAINT `fk_evaluation_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_evaluation_evaluator` FOREIGN KEY (`evaluator_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_evaluation_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `employee_evaluations` COMMENT = 'Évaluations de performance des employés';

-- =========================================================
-- 6. TABLE employee_absences
-- =========================================================
CREATE TABLE IF NOT EXISTS `employee_absences` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_id` BIGINT UNSIGNED NOT NULL,
    `absence_type` ENUM('vacation', 'sick_leave', 'personal', 'maternity', 'paternity', 'unpaid', 'other') NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `days_count` INT NOT NULL,
    `status` ENUM('pending', 'approved', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending',
    `reason` TEXT NULL,
    `approved_by_id` BIGINT UNSIGNED NULL,
    `approved_at` DATETIME NULL,
    `rejection_reason` TEXT NULL,
    `medical_certificate_path` VARCHAR(500) NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` BIGINT UNSIGNED NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_absence_employee` (`employee_id`),
    INDEX `idx_absence_dates` (`start_date`, `end_date`),
    INDEX `idx_absence_status` (`status`),
    INDEX `idx_absence_type` (`absence_type`),
    CONSTRAINT `fk_absence_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_absence_approved_by` FOREIGN KEY (`approved_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_absence_created_by` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `employee_absences` COMMENT = 'Absences des employés (congés, maladie, etc.)';

-- =========================================================
-- FIN DE LA MIGRATION
-- =========================================================
SELECT 'Migration RH complète terminée avec succès!' AS message;

