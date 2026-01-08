-- =========================================================
-- SCRIPT D'AJOUT : Colonne 'reason' dans stock_returns (MySQL)
-- =========================================================
-- Date : 8 Janvier 2026
-- Description : Ajoute la colonne 'reason' à la table stock_returns
--                pour MySQL (colonne déjà définie dans le modèle mais absente en DB)
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

-- Vérifier si la colonne existe déjà
SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'stock_returns'
        AND COLUMN_NAME = 'reason'
);

-- Ajouter la colonne si elle n'existe pas
SET @sql = IF(@column_exists = 0,
    'ALTER TABLE stock_returns ADD COLUMN reason TEXT NULL COMMENT "Raison du retour" AFTER notes',
    'SELECT "La colonne reason existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérification
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'stock_returns'
    AND COLUMN_NAME = 'reason';

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

