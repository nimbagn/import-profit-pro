-- =========================================================
-- Script pour ajouter les permissions flotte au rôle magasinier
-- =========================================================
-- Date : 2026-01-03
-- Description : Ajoute la permission 'create' pour les véhicules au rôle magasinier
--               pour permettre la création de documents, maintenances, assignations
-- Compatible MySQL
-- =========================================================

-- Vérifier et mettre à jour les permissions du magasinier
SET @warehouse_permissions = (
    SELECT permissions 
    FROM roles 
    WHERE code = 'warehouse' 
    LIMIT 1
);

-- Si le rôle existe
SET @warehouse_exists = (
    SELECT COUNT(*) 
    FROM roles 
    WHERE code = 'warehouse'
);

-- Si le rôle existe, mettre à jour les permissions
SET @sql = IF(@warehouse_exists > 0,
    CONCAT(
        'UPDATE roles SET permissions = JSON_SET(',
        'COALESCE(permissions, "{}"), ',
        '"$.vehicles", ',
        'CASE ',
        'WHEN JSON_EXTRACT(permissions, "$.vehicles") IS NULL THEN \'["read", "create", "update"]\' ',
        'WHEN JSON_SEARCH(JSON_EXTRACT(permissions, "$.vehicles"), "one", "create") IS NULL THEN ',
        'JSON_ARRAY_APPEND(JSON_EXTRACT(permissions, "$.vehicles"), "$", "create") ',
        'ELSE JSON_EXTRACT(permissions, "$.vehicles") ',
        'END',
        ') WHERE code = "warehouse"'
    ),
    'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Vérification
SELECT 
    code, 
    name,
    JSON_EXTRACT(permissions, '$.vehicles') as vehicles_permissions
FROM roles 
WHERE code = 'warehouse';

