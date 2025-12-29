-- Script pour ajouter la permission 'update' aux rôles commercial et supervisor
-- pour permettre la modification des commandes

-- Ajouter 'update' au rôle commercial
UPDATE roles 
SET permissions = JSON_SET(
    permissions, 
    '$.orders', 
    JSON_ARRAY('read', 'create', 'update')
) 
WHERE code = 'commercial';

-- Ajouter 'update' au rôle supervisor
UPDATE roles 
SET permissions = JSON_SET(
    permissions, 
    '$.orders', 
    JSON_ARRAY('read', 'validate', 'update')
) 
WHERE code = 'supervisor';

-- Vérification
SELECT code, JSON_EXTRACT(permissions, '$.orders') as orders_permissions 
FROM roles 
WHERE code IN ('commercial', 'supervisor');

