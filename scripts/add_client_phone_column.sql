-- Script pour ajouter la colonne client_phone à la table stock_outgoings
-- Si la colonne n'existe pas déjà

-- Pour MySQL
ALTER TABLE `stock_outgoings` 
ADD COLUMN IF NOT EXISTS `client_phone` VARCHAR(20) NULL AFTER `client_name`;

-- Vérification
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'stock_outgoings' 
  AND COLUMN_NAME = 'client_phone';

