-- =========================================================
-- Script pour ajouter les permissions flotte au rôle magasinier
-- =========================================================
-- Date : 2026-01-03
-- Description : Ajoute la permission 'create' pour les véhicules au rôle magasinier
--               pour permettre la création de documents, maintenances, assignations
-- Compatible PostgreSQL
-- =========================================================

DO $$
DECLARE
    warehouse_permissions JSONB;
    vehicles_perms JSONB;
BEGIN
    -- Récupérer les permissions actuelles du magasinier
    SELECT permissions INTO warehouse_permissions
    FROM roles
    WHERE code = 'warehouse';
    
    -- Si le rôle existe
    IF warehouse_permissions IS NOT NULL THEN
        -- Récupérer les permissions véhicules actuelles
        vehicles_perms := warehouse_permissions->'vehicles';
        
        -- Si les permissions véhicules existent déjà
        IF vehicles_perms IS NOT NULL THEN
            -- Vérifier si 'create' n'est pas déjà présent
            IF NOT (vehicles_perms ? 'create') THEN
                -- Ajouter 'create' aux permissions existantes
                vehicles_perms := vehicles_perms || '["create"]'::JSONB;
                -- Supprimer les doublons en convertissant en array, puis en JSONB
                vehicles_perms := (
                    SELECT jsonb_agg(DISTINCT value)
                    FROM jsonb_array_elements(vehicles_perms) AS value
                );
            END IF;
        ELSE
            -- Créer les permissions véhicules avec read, create, update
            vehicles_perms := '["read", "create", "update"]'::JSONB;
        END IF;
        
        -- Mettre à jour les permissions véhicules
        warehouse_permissions := warehouse_permissions || jsonb_build_object('vehicles', vehicles_perms);
        
        -- Mettre à jour le rôle
        UPDATE roles
        SET permissions = warehouse_permissions
        WHERE code = 'warehouse';
        
        RAISE NOTICE '✅ Permissions flotte (vehicles.create) ajoutées au rôle magasinier';
        RAISE NOTICE '   Permissions véhicules: %', vehicles_perms;
    ELSE
        RAISE WARNING '❌ Rôle magasinier (warehouse) non trouvé';
    END IF;
END $$;

-- Vérification
SELECT 
    code, 
    name,
    permissions->'vehicles' as vehicles_permissions
FROM roles 
WHERE code = 'warehouse';

