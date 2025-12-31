-- Script pour ajouter la colonne additional_permissions à la table users
-- Permet d'attribuer des permissions supplémentaires aux utilisateurs RH
-- Base de données: PostgreSQL
-- Compatible avec PostgreSQL 12+
-- Date: 2025-01-XX

-- =========================================================
-- AJOUT DE LA COLONNE additional_permissions
-- =========================================================

-- Vérifier si la colonne existe déjà avant de l'ajouter
DO $$
BEGIN
    -- Vérifier si la colonne existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'additional_permissions'
    ) THEN
        -- Ajouter la colonne additional_permissions de type JSONB
        -- JSONB est recommandé pour PostgreSQL (meilleures performances que JSON)
        ALTER TABLE users 
        ADD COLUMN additional_permissions JSONB NULL;
        
        -- Ajouter un commentaire pour documenter la colonne
        COMMENT ON COLUMN users.additional_permissions IS 
        'Permissions supplémentaires attribuées individuellement à un utilisateur (ex: stocks.read pour RH). Format JSON: {"module": ["action1", "action2"]}';
        
        RAISE NOTICE '✅ Colonne additional_permissions ajoutée avec succès!';
    ELSE
        RAISE NOTICE 'ℹ️  La colonne additional_permissions existe déjà.';
    END IF;
END $$;

-- =========================================================
-- VÉRIFICATION
-- =========================================================

-- Vérifier que la colonne a été créée
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'additional_permissions'
    ) THEN
        RAISE NOTICE '✅ Vérification réussie: La colonne additional_permissions existe dans la table users.';
    ELSE
        RAISE WARNING '⚠️  La colonne additional_permissions n''a pas été créée.';
    END IF;
END $$;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

