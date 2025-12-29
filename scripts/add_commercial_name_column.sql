-- Script pour ajouter la colonne commercial_name à la table forecasts
-- Exécuter ce script pour activer la fonctionnalité multi-commerciaux

ALTER TABLE `forecasts` 
ADD COLUMN `commercial_name` VARCHAR(100) NULL AFTER `status`,
ADD INDEX `idx_forecast_commercial` (`commercial_name`);

