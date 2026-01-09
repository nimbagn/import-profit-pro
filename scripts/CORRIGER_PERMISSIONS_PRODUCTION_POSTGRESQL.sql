-- =========================================================
-- Script pour Corriger les Permissions en Production
-- =========================================================
-- Date : 2026-01-09
-- Description : Corrige les permissions pour admin et magasinier
--               - Admin : Accès à messaging.read pour les rapports automatiques
--               - Magasinier : Permissions complètes pour outgoings
-- Compatible PostgreSQL
-- =========================================================

BEGIN;

-- =========================================================
-- 1. PERMISSIONS ADMIN - MESSAGING
-- =========================================================

DO $$ 
DECLARE
    admin_permissions JSONB;
    messaging_perms JSONB;
BEGIN
    -- Récupérer les permissions actuelles de l'admin
    SELECT permissions INTO admin_permissions
    FROM roles
    WHERE code = 'admin' OR code = 'superadmin';
    
    -- Si le rôle admin existe
    IF admin_permissions IS NOT NULL THEN
        -- Vérifier si messaging existe déjà
        messaging_perms := admin_permissions->'messaging';
        
        -- Si messaging n'existe pas ou ne contient pas 'read'
        IF messaging_perms IS NULL OR NOT (messaging_perms ? 'read' OR messaging_perms @> '["read"]'::jsonb) THEN
            -- Ajouter messaging avec read et update
            IF messaging_perms IS NULL THEN
                admin_permissions := jsonb_set(
                    admin_permissions,
                    '{messaging}',
                    '["read", "update", "send_sms", "send_whatsapp", "send_otp", "manage_contacts"]'::jsonb
                );
            ELSE
                -- Ajouter read s'il manque
                messaging_perms := messaging_perms || '["read"]'::jsonb;
                -- Supprimer les doublons
                messaging_perms := (
                    SELECT jsonb_agg(DISTINCT value)
                    FROM jsonb_array_elements(messaging_perms) AS value
                );
                admin_permissions := jsonb_set(
                    admin_permissions,
                    '{messaging}',
                    messaging_perms
                );
            END IF;
            
            -- Mettre à jour pour admin
            UPDATE roles
            SET permissions = admin_permissions
            WHERE code = 'admin';
            
            RAISE NOTICE '✅ Permissions messaging ajoutées au rôle admin';
        ELSE
            RAISE NOTICE 'ℹ️  Permissions messaging déjà présentes pour admin';
        END IF;
    ELSE
        RAISE WARNING '❌ Rôle admin non trouvé';
    END IF;
END $$;

-- =========================================================
-- 2. PERMISSIONS MAGASINIER - OUTGOINGS
-- =========================================================

DO $$ 
DECLARE
    warehouse_permissions JSONB;
    outgoings_perms JSONB;
BEGIN
    -- Récupérer les permissions actuelles du magasinier
    SELECT permissions INTO warehouse_permissions
    FROM roles
    WHERE code = 'warehouse';
    
    -- Si le rôle existe
    IF warehouse_permissions IS NOT NULL THEN
        -- Vérifier les permissions outgoings
        outgoings_perms := warehouse_permissions->'outgoings';
        
        -- Si outgoings n'existe pas ou ne contient pas toutes les permissions nécessaires
        IF outgoings_perms IS NULL OR NOT (
            (outgoings_perms ? 'read' OR outgoings_perms @> '["read"]'::jsonb) AND
            (outgoings_perms ? 'create' OR outgoings_perms @> '["create"]'::jsonb) AND
            (outgoings_perms ? 'update' OR outgoings_perms @> '["update"]'::jsonb)
        ) THEN
            -- Créer ou mettre à jour les permissions outgoings
            IF outgoings_perms IS NULL THEN
                outgoings_perms := '["read", "create", "update"]'::jsonb;
            ELSE
                -- Ajouter les permissions manquantes
                IF NOT (outgoings_perms ? 'read' OR outgoings_perms @> '["read"]'::jsonb) THEN
                    outgoings_perms := outgoings_perms || '["read"]'::jsonb;
                END IF;
                IF NOT (outgoings_perms ? 'create' OR outgoings_perms @> '["create"]'::jsonb) THEN
                    outgoings_perms := outgoings_perms || '["create"]'::jsonb;
                END IF;
                IF NOT (outgoings_perms ? 'update' OR outgoings_perms @> '["update"]'::jsonb) THEN
                    outgoings_perms := outgoings_perms || '["update"]'::jsonb;
                END IF;
                -- Supprimer les doublons
                outgoings_perms := (
                    SELECT jsonb_agg(DISTINCT value)
                    FROM jsonb_array_elements(outgoings_perms) AS value
                );
            END IF;
            
            -- Mettre à jour les permissions
            warehouse_permissions := jsonb_set(
                warehouse_permissions,
                '{outgoings}',
                outgoings_perms
            );
            
            UPDATE roles
            SET permissions = warehouse_permissions
            WHERE code = 'warehouse';
            
            RAISE NOTICE '✅ Permissions outgoings mises à jour pour le magasinier';
            RAISE NOTICE '   Permissions: %', outgoings_perms;
        ELSE
            RAISE NOTICE 'ℹ️  Permissions outgoings déjà complètes pour le magasinier';
        END IF;
    ELSE
        RAISE WARNING '❌ Rôle warehouse non trouvé';
    END IF;
END $$;

-- =========================================================
-- 3. VÉRIFICATION
-- =========================================================

-- Vérifier les permissions admin
SELECT 
    'Admin' as role,
    code,
    permissions->'messaging' as messaging_permissions
FROM roles
WHERE code IN ('admin', 'superadmin');

-- Vérifier les permissions magasinier
SELECT 
    'Magasinier' as role,
    code,
    permissions->'outgoings' as outgoings_permissions,
    permissions->'receptions' as receptions_permissions,
    permissions->'returns' as returns_permissions
FROM roles
WHERE code = 'warehouse';

COMMIT;

-- =========================================================
-- RÉSUMÉ
-- =========================================================
-- ✅ Admin : Permissions messaging ajoutées (read, update, send_sms, send_whatsapp, etc.)
-- ✅ Magasinier : Permissions outgoings complètes (read, create, update)
-- =========================================================

