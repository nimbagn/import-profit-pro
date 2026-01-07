-- =========================================================
-- FIX PERMISSIONS COMMERCIAL - ORDERS.CREATE
-- PostgreSQL Script pour Render
-- =========================================================
-- 
-- Ce script vérifie et corrige les permissions du rôle commercial
-- pour s'assurer que orders.create est bien présent
--
-- =========================================================

-- Vérification actuelle des permissions
SELECT 
    r.code,
    r.name,
    r.permissions->'orders' as orders_permissions
FROM roles r
WHERE r.code = 'commercial';

-- Fix: S'assurer que le rôle commercial a bien orders.create
DO $$
DECLARE
    commercial_role_id INTEGER;
    current_permissions JSONB;
    updated_permissions JSONB;
    orders_perms JSONB;
BEGIN
    -- Récupérer l'ID du rôle commercial
    SELECT id INTO commercial_role_id
    FROM roles
    WHERE code = 'commercial';
    
    IF commercial_role_id IS NOT NULL THEN
        -- Récupérer les permissions actuelles
        SELECT permissions INTO current_permissions
        FROM roles
        WHERE id = commercial_role_id;
        
        -- Initialiser si NULL
        IF current_permissions IS NULL THEN
            current_permissions := '{}'::JSONB;
        END IF;
        
        -- Récupérer les permissions orders actuelles
        orders_perms := current_permissions->'orders';
        
        -- Si orders n'existe pas, créer avec toutes les permissions nécessaires
        IF orders_perms IS NULL THEN
            updated_permissions := current_permissions || '{"orders": ["read", "create", "update"]}'::JSONB;
        ELSE
            -- Vérifier si 'create' est déjà dans la liste
            IF NOT (orders_perms @> '"create"') THEN
                -- Ajouter 'create' à la liste existante si pas déjà présent
                updated_permissions := jsonb_set(
                    current_permissions,
                    '{orders}',
                    orders_perms || '"create"'::JSONB
                );
            ELSE
                -- Vérifier aussi que 'read' et 'update' sont présents
                IF NOT (orders_perms @> '"read"') THEN
                    updated_permissions := jsonb_set(
                        current_permissions,
                        '{orders}',
                        orders_perms || '"read"'::JSONB
                    );
                END IF;
                IF NOT (orders_perms @> '"update"') THEN
                    updated_permissions := jsonb_set(
                        COALESCE(updated_permissions, current_permissions),
                        '{orders}',
                        (COALESCE(updated_permissions, current_permissions)->'orders') || '"update"'::JSONB
                    );
                END IF;
                
                -- Si toutes les permissions sont déjà présentes, ne rien changer
                IF updated_permissions IS NULL THEN
                    updated_permissions := current_permissions;
                END IF;
            END IF;
        END IF;
        
        -- Mettre à jour les permissions
        UPDATE roles
        SET permissions = updated_permissions
        WHERE id = commercial_role_id;
        
        RAISE NOTICE 'Permissions Commercial mises à jour : orders.create ajouté/vérifié';
    ELSE
        RAISE NOTICE 'Rôle commercial non trouvé';
    END IF;
END $$;

-- Vérification finale des permissions
SELECT 
    r.code,
    r.name,
    r.permissions->'orders' as orders_permissions,
    CASE 
        WHEN r.permissions->'orders' @> '"create"' THEN '✅ orders.create présent'
        ELSE '❌ orders.create manquant'
    END as status_create,
    CASE 
        WHEN r.permissions->'orders' @> '"read"' THEN '✅ orders.read présent'
        ELSE '❌ orders.read manquant'
    END as status_read,
    CASE 
        WHEN r.permissions->'orders' @> '"update"' THEN '✅ orders.update présent'
        ELSE '❌ orders.update manquant'
    END as status_update
FROM roles r
WHERE r.code = 'commercial';

