-- =========================================================
-- Script pour Corriger TOUTES les Permissions STOCKS du Magasinier
-- =========================================================
-- Date : 2026-01-09
-- Description : Garantit que le magasinier a TOUTES les permissions STOCKS
--               nécessaires pour travailler sur /stocks
-- Compatible PostgreSQL
-- =========================================================

BEGIN;

-- =========================================================
-- 1. PERMISSIONS STOCKS COMPLÈTES POUR MAGASINIER
-- =========================================================

DO $$ 
DECLARE
    warehouse_permissions JSONB;
    required_permissions JSONB;
BEGIN
    -- Récupérer les permissions actuelles du magasinier
    SELECT permissions INTO warehouse_permissions
    FROM roles
    WHERE code = 'warehouse';
    
    -- Si le rôle existe
    IF warehouse_permissions IS NOT NULL THEN
        -- Permissions requises pour le magasinier
        required_permissions := '{
            "stocks": ["read", "create", "update"],
            "movements": ["read", "create", "update"],
            "inventory": ["read", "create", "update"],
            "receptions": ["read", "create", "update"],
            "outgoings": ["read", "create", "update"],
            "returns": ["read", "create", "update"],
            "vehicles": ["read", "create", "update"],
            "regions": ["read"],
            "depots": ["read"],
            "families": ["read"],
            "stock_items": ["read"],
            "orders": ["read"],
            "stock_loading": ["read", "verify", "load"]
        }'::jsonb;
        
        -- Fusionner les permissions (les nouvelles remplacent les anciennes)
        warehouse_permissions := warehouse_permissions || required_permissions;
        
        -- Mettre à jour les permissions
        UPDATE roles
        SET permissions = warehouse_permissions
        WHERE code = 'warehouse';
        
        RAISE NOTICE '✅ Permissions STOCKS complètes mises à jour pour le magasinier';
        RAISE NOTICE '   Permissions: %', warehouse_permissions;
    ELSE
        RAISE WARNING '❌ Rôle warehouse non trouvé';
    END IF;
END $$;

-- =========================================================
-- 2. VÉRIFICATION DES PERMISSIONS
-- =========================================================

-- Vérifier les permissions du magasinier
SELECT 
    'Magasinier' as role,
    code,
    permissions->'stocks' as stocks_permissions,
    permissions->'movements' as movements_permissions,
    permissions->'receptions' as receptions_permissions,
    permissions->'outgoings' as outgoings_permissions,
    permissions->'returns' as returns_permissions,
    permissions->'inventory' as inventory_permissions
FROM roles
WHERE code = 'warehouse';

COMMIT;

-- =========================================================
-- RÉSUMÉ
-- =========================================================
-- ✅ Magasinier : Toutes les permissions STOCKS garanties
--   - stocks: read, create, update
--   - movements: read, create, update
--   - receptions: read, create, update
--   - outgoings: read, create, update
--   - returns: read, create, update
--   - inventory: read, create, update
-- =========================================================

