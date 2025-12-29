-- =====================================================
-- VÉRIFICATION COMPLÈTE DE LA TABLE USERS
-- Exécutez: mysql -u root -p madargn < VERIFIER_TABLE_USERS.sql
-- =====================================================

USE madargn;

-- 1. Structure de la table users
SELECT '=== STRUCTURE DE LA TABLE USERS ===' as '';
DESCRIBE users;

-- 2. Tous les utilisateurs
SELECT '=== TOUS LES UTILISATEURS ===' as '';
SELECT 
    id,
    username,
    email,
    full_name,
    phone,
    role_id,
    is_active,
    CASE 
        WHEN password_hash IS NULL THEN '❌ NULL'
        WHEN password_hash = '' THEN '❌ VIDÉ'
        WHEN LENGTH(password_hash) < 20 THEN '❌ TROP COURT'
        ELSE CONCAT('✅ OK (', LENGTH(password_hash), ' caractères)')
    END as password_status,
    last_login,
    created_at,
    updated_at
FROM users
ORDER BY id;

-- 3. Utilisateur admin spécifiquement
SELECT '=== UTILISATEUR ADMIN ===' as '';
SELECT 
    id,
    username,
    email,
    full_name,
    role_id,
    is_active,
    CASE 
        WHEN password_hash IS NULL THEN '❌ PAS DE HASH'
        WHEN password_hash = '' THEN '❌ HASH VIDÉ'
        ELSE CONCAT('✅ Hash présent (', LEFT(password_hash, 40), '...)')
    END as password_hash_preview,
    LENGTH(password_hash) as password_hash_length,
    created_at
FROM users 
WHERE username = 'admin';

-- 4. Relation avec les rôles
SELECT '=== RELATION UTILISATEURS - RÔLES ===' as '';
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    u.role_id,
    r.id as role_id_check,
    r.name as role_name,
    r.code as role_code,
    u.is_active
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
ORDER BY u.id;

-- 5. Statistiques
SELECT '=== STATISTIQUES ===' as '';
SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN username = 'admin' THEN 1 ELSE 0 END) as admin_exists,
    SUM(CASE WHEN password_hash IS NOT NULL AND password_hash != '' THEN 1 ELSE 0 END) as users_with_password,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users
FROM users;

-- 6. Vérification des index
SELECT '=== INDEX SUR LA TABLE USERS ===' as '';
SHOW INDEX FROM users;

