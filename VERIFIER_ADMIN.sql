-- Script pour vérifier si l'utilisateur admin existe
-- Exécutez: mysql -u root -p madargn < VERIFIER_ADMIN.sql

USE madargn;

-- 1. Vérifier le rôle admin
SELECT '=== VÉRIFICATION DU RÔLE ADMIN ===' as '';
SELECT id, name, code, description FROM roles WHERE code = 'admin';

-- 2. Vérifier l'utilisateur admin
SELECT '=== VÉRIFICATION DE L''UTILISATEUR ADMIN ===' as '';
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
        ELSE CONCAT('✅ Hash présent (', LEFT(password_hash, 30), '...)')
    END as password_status,
    created_at
FROM users 
WHERE username = 'admin';

-- 3. Vérifier la relation
SELECT '=== VÉRIFICATION DE LA RELATION ===' as '';
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    r.id as role_id,
    r.name as role_name,
    r.code as role_code,
    u.is_active
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

-- 4. Résumé
SELECT '=== RÉSUMÉ ===' as '';
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM roles WHERE code = 'admin') 
        THEN '✅ Rôle admin existe'
        ELSE '❌ Rôle admin MANQUANT'
    END as role_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM users WHERE username = 'admin') 
        THEN '✅ Utilisateur admin existe'
        ELSE '❌ Utilisateur admin MANQUANT'
    END as user_status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM users u 
            WHERE u.username = 'admin' 
            AND u.password_hash IS NOT NULL 
            AND u.password_hash != ''
        )
        THEN '✅ Hash de mot de passe présent'
        ELSE '❌ Hash de mot de passe MANQUANT'
    END as password_status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM users u
            INNER JOIN roles r ON u.role_id = r.id
            WHERE u.username = 'admin' AND r.code = 'admin'
        )
        THEN '✅ Relation utilisateur-rôle OK'
        ELSE '❌ Relation utilisateur-rôle PROBLÉMATIQUE'
    END as relation_status;

