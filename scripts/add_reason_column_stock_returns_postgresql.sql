-- =========================================================
-- SCRIPT D'AJOUT : Colonne 'reason' dans stock_returns (PostgreSQL)
-- =========================================================
-- Date : 8 Janvier 2026
-- Description : Ajoute la colonne 'reason' à la table stock_returns
--                pour PostgreSQL (colonne déjà définie dans le modèle mais absente en DB)
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

BEGIN;

-- Ajouter la colonne si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
            AND table_name = 'stock_returns'
            AND column_name = 'reason'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN reason TEXT NULL;
        
        RAISE NOTICE '✅ Colonne reason ajoutée à stock_returns';
    ELSE
        RAISE NOTICE 'ℹ️  Colonne reason existe déjà';
    END IF;
END $$;

-- Vérification
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public'
    AND table_name = 'stock_returns'
    AND column_name = 'reason';

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

