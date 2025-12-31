-- Script SQL pour corriger les permissions du rôle rh_assistant (PostgreSQL)
-- Ce script met à jour les permissions pour permettre la création d'employés externes

-- Pour PostgreSQL
UPDATE roles 
SET permissions = '{
    "users": ["read", "create", "update"],
    "employees": ["read", "create", "update"],
    "contracts": ["read", "create", "update"],
    "trainings": ["read", "create", "update"],
    "evaluations": ["read", "create"],
    "absences": ["read", "create", "update"],
    "reports": ["read"]
}'::jsonb
WHERE code = 'rh_assistant';

-- Vérification
SELECT 
    id,
    name,
    code,
    permissions
FROM roles 
WHERE code = 'rh_assistant';

