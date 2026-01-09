-- =========================================================
-- Script pour ajouter les permissions commercial_teams, sales et objectives
-- =========================================================
-- Date : 2026-01-03
-- Description : Ajoute les permissions pour la gestion des équipes commerciales,
--               la confirmation des ventes et les objectifs au rôle superviseur
-- Compatible PostgreSQL
-- =========================================================

DO $$
DECLARE
    supervisor_permissions JSONB;
    commercial_teams_perms JSONB := '["read", "write"]'::JSONB;
    sales_perms JSONB := '["confirm", "view_confirmed"]'::JSONB;
    objectives_perms JSONB := '["read", "write"]'::JSONB;
BEGIN
    -- Récupérer les permissions actuelles du superviseur
    SELECT permissions INTO supervisor_permissions
    FROM roles
    WHERE code = 'supervisor';
    
    -- Si le rôle existe
    IF supervisor_permissions IS NOT NULL THEN
        -- Ajouter les permissions commercial_teams
        supervisor_permissions := supervisor_permissions || jsonb_build_object('commercial_teams', commercial_teams_perms);
        
        -- Ajouter les permissions sales
        supervisor_permissions := supervisor_permissions || jsonb_build_object('sales', sales_perms);
        
        -- Ajouter les permissions objectives
        supervisor_permissions := supervisor_permissions || jsonb_build_object('objectives', objectives_perms);
        
        -- Mettre à jour le rôle
        UPDATE roles
        SET permissions = supervisor_permissions
        WHERE code = 'supervisor';
        
        RAISE NOTICE '✅ Permissions commercial_teams, sales et objectives ajoutées au rôle superviseur';
    ELSE
        RAISE WARNING '❌ Rôle superviseur non trouvé';
    END IF;
END $$;

-- Vérification
SELECT 
    code, 
    name,
    permissions->'commercial_teams' as commercial_teams_permissions,
    permissions->'sales' as sales_permissions,
    permissions->'objectives' as objectives_permissions
FROM roles 
WHERE code = 'supervisor';

