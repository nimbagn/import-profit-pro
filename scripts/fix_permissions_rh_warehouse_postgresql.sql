-- =========================================================
-- FIX PERMISSIONS RH ASSISTANT ET MAGASINIER
-- PostgreSQL Script pour Render
-- =========================================================
-- 
-- Ce script corrige les permissions pour :
-- 1. RH Assistant : Ajoute analytics.read pour accès aux statistiques
-- 2. Magasinier : Ajoute vehicles.update pour accès à l'odomètre
--
-- =========================================================

-- Fix 1: Ajouter analytics.read au rôle RH Assistant
DO $$
DECLARE
    rh_assistant_role_id INTEGER;
    current_permissions JSONB;
    updated_permissions JSONB;
BEGIN
    -- Récupérer l'ID du rôle rh_assistant
    SELECT id INTO rh_assistant_role_id
    FROM roles
    WHERE code = 'rh_assistant';
    
    IF rh_assistant_role_id IS NOT NULL THEN
        -- Récupérer les permissions actuelles
        SELECT permissions INTO current_permissions
        FROM roles
        WHERE id = rh_assistant_role_id;
        
        -- Initialiser si NULL
        IF current_permissions IS NULL THEN
            current_permissions := '{}'::JSONB;
        END IF;
        
        -- Ajouter analytics.read si pas déjà présent
        IF NOT (current_permissions ? 'analytics') THEN
            updated_permissions := current_permissions || '{"analytics": ["read"]}'::JSONB;
        ELSIF current_permissions->'analytics' IS NULL THEN
            updated_permissions := current_permissions || '{"analytics": ["read"]}'::JSONB;
        ELSE
            -- Vérifier si 'read' est déjà dans la liste
            IF NOT (current_permissions->'analytics' @> '"read"') THEN
                updated_permissions := jsonb_set(
                    current_permissions,
                    '{analytics}',
                    (current_permissions->'analytics') || '"read"'::JSONB
                );
            ELSE
                updated_permissions := current_permissions;
            END IF;
        END IF;
        
        -- Mettre à jour les permissions
        UPDATE roles
        SET permissions = updated_permissions
        WHERE id = rh_assistant_role_id;
        
        RAISE NOTICE 'Permissions RH Assistant mises à jour : analytics.read ajouté';
    ELSE
        RAISE NOTICE 'Rôle rh_assistant non trouvé';
    END IF;
END $$;

-- Fix 2: Ajouter vehicles.update au rôle Magasinier (warehouse)
DO $$
DECLARE
    warehouse_role_id INTEGER;
    current_permissions JSONB;
    updated_permissions JSONB;
    vehicles_perms JSONB;
BEGIN
    -- Récupérer l'ID du rôle warehouse
    SELECT id INTO warehouse_role_id
    FROM roles
    WHERE code = 'warehouse';
    
    IF warehouse_role_id IS NOT NULL THEN
        -- Récupérer les permissions actuelles
        SELECT permissions INTO current_permissions
        FROM roles
        WHERE id = warehouse_role_id;
        
        -- Initialiser si NULL
        IF current_permissions IS NULL THEN
            current_permissions := '{}'::JSONB;
        END IF;
        
        -- Récupérer les permissions vehicles actuelles
        vehicles_perms := current_permissions->'vehicles';
        
        -- Si vehicles n'existe pas, créer avec ['read', 'update']
        IF vehicles_perms IS NULL THEN
            updated_permissions := current_permissions || '{"vehicles": ["read", "update"]}'::JSONB;
        ELSE
            -- Vérifier si 'update' est déjà dans la liste
            IF NOT (vehicles_perms @> '"update"') THEN
                -- Ajouter 'update' à la liste existante
                updated_permissions := jsonb_set(
                    current_permissions,
                    '{vehicles}',
                    vehicles_perms || '"update"'::JSONB
                );
            ELSE
                updated_permissions := current_permissions;
            END IF;
        END IF;
        
        -- Mettre à jour les permissions
        UPDATE roles
        SET permissions = updated_permissions
        WHERE id = warehouse_role_id;
        
        RAISE NOTICE 'Permissions Magasinier mises à jour : vehicles.update ajouté';
    ELSE
        RAISE NOTICE 'Rôle warehouse non trouvé';
    END IF;
END $$;

-- Vérification des permissions mises à jour
SELECT 
    r.code,
    r.name,
    r.permissions->'analytics' as analytics_perms,
    r.permissions->'vehicles' as vehicles_perms
FROM roles r
WHERE r.code IN ('rh_assistant', 'warehouse')
ORDER BY r.code;

