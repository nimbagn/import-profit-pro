-- Script SQL pour corriger les permissions du rôle rh_assistant
-- Ce script met à jour les permissions pour permettre la création d'employés externes

-- Pour MySQL
UPDATE roles 
SET permissions = JSON_OBJECT(
    'users', JSON_ARRAY('read', 'create', 'update'),
    'employees', JSON_ARRAY('read', 'create', 'update'),
    'contracts', JSON_ARRAY('read', 'create', 'update'),
    'trainings', JSON_ARRAY('read', 'create', 'update'),
    'evaluations', JSON_ARRAY('read', 'create'),
    'absences', JSON_ARRAY('read', 'create', 'update'),
    'reports', JSON_ARRAY('read')
)
WHERE code = 'rh_assistant';

-- Vérification
SELECT 
    id,
    name,
    code,
    permissions
FROM roles 
WHERE code = 'rh_assistant';

