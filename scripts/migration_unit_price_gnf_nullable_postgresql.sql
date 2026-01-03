-- Migration: Permettre NULL pour unit_price_gnf dans reception_details
-- Date: 2026-01-02
-- Description: Aligne la base de données avec le modèle Python (nullable=True)

-- Étape 1: Mettre à jour les valeurs NULL existantes avec 0
-- (Si des enregistrements NULL existent déjà, on les met à 0)
UPDATE reception_details
SET unit_price_gnf = 0
WHERE unit_price_gnf IS NULL;

-- Étape 2: Modifier la colonne pour permettre NULL
-- Pour PostgreSQL
ALTER TABLE reception_details
ALTER COLUMN unit_price_gnf DROP NOT NULL;

-- Vérification
SELECT 
    column_name,
    is_nullable,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'reception_details'
  AND column_name = 'unit_price_gnf';

