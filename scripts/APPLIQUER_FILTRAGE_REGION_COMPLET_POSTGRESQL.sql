-- =========================================================
-- Script pour S'assurer que TOUS les Utilisateurs ont une Région
-- =========================================================
-- Date : 2026-01-09
-- Description : Assure que tous les utilisateurs (sauf admins/superviseurs) 
--               ont une région assignée pour le filtrage automatique
-- Compatible PostgreSQL
-- =========================================================

BEGIN;

-- =========================================================
-- 1. VÉRIFIER LES UTILISATEURS SANS RÉGION
-- =========================================================

-- Afficher les utilisateurs sans région (sauf admins/superviseurs)
SELECT 
    u.id,
    u.username,
    u.email,
    r.code as role_code,
    r.name as role_name,
    u.region_id
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.region_id IS NULL
  AND r.code NOT IN ('admin', 'superadmin', 'supervisor')
ORDER BY r.name, u.username;

-- =========================================================
-- 2. ASSIGNER UNE RÉGION PAR DÉFAUT (OPTIONNEL)
-- =========================================================

-- ⚠️ ATTENTION : Cette section est commentée par défaut
-- Décommentez et modifiez selon vos besoins si vous voulez assigner automatiquement une région

-- Exemple : Assigner la première région disponible aux utilisateurs sans région
-- UPDATE users u
-- SET region_id = (SELECT id FROM regions WHERE is_active = TRUE ORDER BY id LIMIT 1)
-- WHERE u.region_id IS NULL
--   AND u.role_id IN (
--       SELECT id FROM roles WHERE code NOT IN ('admin', 'superadmin', 'supervisor')
--   );

-- =========================================================
-- 3. VÉRIFIER LES RÉGIONS DISPONIBLES
-- =========================================================

SELECT 
    id,
    name,
    code,
    is_active,
    created_at
FROM regions
WHERE is_active = TRUE
ORDER BY name;

-- =========================================================
-- 4. STATISTIQUES PAR RÉGION
-- =========================================================

SELECT 
    r.name as region_name,
    r.code as region_code,
    COUNT(u.id) as user_count,
    COUNT(DISTINCT CASE WHEN ro.code = 'commercial' THEN u.id END) as commercial_count,
    COUNT(DISTINCT CASE WHEN ro.code = 'warehouse' THEN u.id END) as warehouse_count,
    COUNT(DISTINCT CASE WHEN ro.code = 'supervisor' THEN u.id END) as supervisor_count
FROM regions r
LEFT JOIN users u ON u.region_id = r.id
LEFT JOIN roles ro ON u.role_id = ro.id
WHERE r.is_active = TRUE
GROUP BY r.id, r.name, r.code
ORDER BY r.name;

COMMIT;

-- =========================================================
-- RÉSUMÉ
-- =========================================================
-- ✅ Ce script permet de :
--   1. Identifier les utilisateurs sans région assignée
--   2. Voir les régions disponibles
--   3. Voir les statistiques par région
-- 
-- ⚠️ IMPORTANT :
--   - Les admins et superviseurs peuvent avoir region_id = NULL (voient tout)
--   - TOUS les autres utilisateurs DOIVENT avoir une région assignée
--   - Le filtrage automatique s'applique à tous les utilisateurs sauf admins/superviseurs
-- =========================================================

