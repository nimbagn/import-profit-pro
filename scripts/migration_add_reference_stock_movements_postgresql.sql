-- Migration: Ajouter la colonne reference à stock_movements
-- Date: 2026-01-02
-- Description: Ajoute la colonne reference manquante dans stock_movements pour correspondre au modèle Python

-- Vérifier si la colonne existe déjà et l'ajouter si nécessaire
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
          AND table_name = 'stock_movements'
          AND column_name = 'reference'
    ) THEN
        -- Ajouter la colonne
        ALTER TABLE stock_movements 
        ADD COLUMN reference VARCHAR(50) NULL;
        
        -- Ajouter la contrainte unique
        CREATE UNIQUE INDEX idx_movement_reference ON stock_movements(reference);
        
        RAISE NOTICE 'Colonne reference ajoutée avec succès';
    ELSE
        RAISE NOTICE 'La colonne reference existe déjà';
    END IF;
END $$;

-- Vérification
SELECT 
    column_name,
    is_nullable,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'stock_movements'
  AND column_name = 'reference';

