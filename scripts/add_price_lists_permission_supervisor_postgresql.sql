-- =========================================================
-- Script pour ajouter les permissions price_lists au rôle superviseur
-- =========================================================
-- Date : 4 Janvier 2026
-- Description : Ajoute les permissions de gestion des listes de prix
--               au rôle superviseur (view, create, update, delete)
-- Compatible PostgreSQL
-- =========================================================

DO $$
DECLARE
    supervisor_permissions JSONB;
    price_lists_perms JSONB := '["view", "create", "edit", "delete"]'::JSONB;
BEGIN
    -- Récupérer les permissions actuelles du superviseur
    SELECT permissions INTO supervisor_permissions
    FROM roles
    WHERE code = 'supervisor';
    
    -- Si le rôle existe
    IF supervisor_permissions IS NOT NULL THEN
        -- Ajouter les permissions price_lists
        supervisor_permissions := supervisor_permissions || jsonb_build_object('price_lists', price_lists_perms);
        
        -- Mettre à jour le rôle
        UPDATE roles
        SET permissions = supervisor_permissions
        WHERE code = 'supervisor';
        
        RAISE NOTICE '✅ Permissions price_lists ajoutées au rôle superviseur';
    ELSE
        RAISE WARNING '❌ Rôle superviseur non trouvé';
    END IF;
END $$;

-- Vérification
SELECT 
    code, 
    name,
    permissions->'price_lists' as price_lists_permissions 
FROM roles 
WHERE code = 'supervisor';

