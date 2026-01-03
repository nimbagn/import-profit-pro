-- Migration: Permettre NULL pour unit_price_gnf dans reception_details
-- Date: 2026-01-02
-- Description: Aligne la base de données avec le modèle Python (nullable=True)

-- Étape 1: Mettre à jour les valeurs NULL existantes avec 0
-- (Si des enregistrements NULL existent déjà, on les met à 0)
UPDATE reception_details
SET unit_price_gnf = 0
WHERE unit_price_gnf IS NULL;

-- Étape 2: Modifier la colonne pour permettre NULL
-- Pour MySQL
ALTER TABLE reception_details
MODIFY COLUMN unit_price_gnf DECIMAL(18,2) NULL;

-- Vérification
SELECT 
    COLUMN_NAME,
    IS_NULLABLE,
    COLUMN_TYPE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'reception_details'
  AND COLUMN_NAME = 'unit_price_gnf';

