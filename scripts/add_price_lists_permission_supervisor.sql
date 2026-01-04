-- =========================================================
-- Script pour ajouter les permissions price_lists au rôle superviseur
-- =========================================================
-- Date : 4 Janvier 2026
-- Description : Ajoute les permissions de gestion des listes de prix
--               au rôle superviseur (view, create, update, delete)
-- =========================================================

-- Pour MySQL
UPDATE roles 
SET permissions = JSON_SET(
    permissions, 
    '$.price_lists', 
    JSON_ARRAY('view', 'create', 'edit', 'delete')
) 
WHERE code = 'supervisor';

-- Vérification
SELECT 
    code, 
    name,
    JSON_EXTRACT(permissions, '$.price_lists') as price_lists_permissions 
FROM roles 
WHERE code = 'supervisor';

