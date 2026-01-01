-- Script SQL pour ajouter les permissions manquantes au rôle magasinier (MySQL)
-- Permissions à ajouter: receptions et returns

SET @warehouse_role_id = (SELECT id FROM roles WHERE code = 'warehouse');

-- Vérifier que le rôle existe
SELECT IF(@warehouse_role_id IS NULL, 
    CONCAT('ERREUR: Le rôle magasinier (warehouse) n''existe pas'), 
    CONCAT('Rôle trouvé avec ID: ', @warehouse_role_id)
) AS verification;

-- Récupérer les permissions actuelles
SET @current_permissions = (SELECT permissions FROM roles WHERE id = @warehouse_role_id);

-- Ajouter les permissions receptions
SET @current_permissions = JSON_SET(
    COALESCE(@current_permissions, '{}'),
    '$.receptions', 
    JSON_ARRAY('read', 'create', 'update')
);

-- Ajouter les permissions outgoings
SET @current_permissions = JSON_SET(
    @current_permissions,
    '$.outgoings', 
    JSON_ARRAY('read', 'create', 'update')
);

-- Ajouter les permissions returns
SET @current_permissions = JSON_SET(
    @current_permissions,
    '$.returns', 
    JSON_ARRAY('read', 'create', 'update')
);

-- Ajouter les permissions orders
SET @current_permissions = JSON_SET(
    @current_permissions,
    '$.orders', 
    JSON_ARRAY('read')
);

-- Ajouter les permissions stock_loading
SET @current_permissions = JSON_SET(
    @current_permissions,
    '$.stock_loading', 
    JSON_ARRAY('read', 'verify', 'load')
);

-- Mettre à jour les permissions
UPDATE roles
SET permissions = @current_permissions
WHERE id = @warehouse_role_id;

SELECT 'Permissions du rôle magasinier mises à jour avec succès' AS resultat;
SELECT @current_permissions AS nouvelles_permissions;

