-- Migration: Ajouter la colonne reference à stock_movements
-- Date: 2026-01-02
-- Description: Ajoute la colonne reference manquante dans stock_movements pour correspondre au modèle Python

-- Vérifier si la colonne existe déjà
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'stock_movements'
      AND COLUMN_NAME = 'reference'
);

-- Ajouter la colonne si elle n'existe pas
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE stock_movements ADD COLUMN reference VARCHAR(50) NULL UNIQUE AFTER id',
    'SELECT "La colonne reference existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ajouter l'index si la colonne vient d'être créée
SET @sql = IF(@col_exists = 0,
    'CREATE INDEX idx_movement_reference ON stock_movements(reference)',
    'SELECT "Index déjà présent" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérification
SELECT 
    COLUMN_NAME,
    IS_NULLABLE,
    COLUMN_TYPE,
    COLUMN_KEY
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'stock_movements'
  AND COLUMN_NAME = 'reference';

