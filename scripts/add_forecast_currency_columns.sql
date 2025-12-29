-- =========================================================
-- AJOUT DES COLONNES MULTI-DEVISES À LA TABLE FORECASTS
-- =========================================================

-- Note: MySQL ne supporte pas IF NOT EXISTS pour ALTER TABLE ADD COLUMN
-- Vérifiez d'abord si les colonnes existent avant d'exécuter

-- Ajouter la colonne currency
ALTER TABLE `forecasts` 
ADD COLUMN `currency` VARCHAR(8) NOT NULL DEFAULT 'GNF' AFTER `status`;

-- Ajouter les colonnes de taux de change
ALTER TABLE `forecasts` 
ADD COLUMN `rate_usd` DECIMAL(18,2) NULL AFTER `currency`,
ADD COLUMN `rate_eur` DECIMAL(18,2) NULL AFTER `rate_usd`,
ADD COLUMN `rate_xof` DECIMAL(18,2) NULL AFTER `rate_eur`;

-- Vérification
SELECT 'Colonnes multi-devises ajoutées avec succès à la table forecasts!' AS message;

