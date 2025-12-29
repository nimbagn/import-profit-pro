-- =====================================================
-- SCRIPT COMPLET : VÉRIFIER ET CORRIGER L'UTILISATEUR ADMIN
-- Exécutez: mysql -u root -p madargn < VERIFIER_ET_CORRIGER.sql
-- =====================================================

USE madargn;

-- =====================================================
-- ÉTAPE 1 : VÉRIFICATION
-- =====================================================

SELECT '=== ÉTAPE 1 : VÉRIFICATION ===' as '';

-- Vérifier le rôle
SELECT 'Rôle admin:' as '';
SELECT * FROM roles WHERE code = 'admin';

-- Vérifier l'utilisateur
SELECT 'Utilisateur admin:' as '';
SELECT 
    id,
    username,
    email,
    full_name,
    role_id,
    is_active,
    CASE 
        WHEN password_hash IS NULL THEN '❌ NULL'
        WHEN password_hash = '' THEN '❌ VIDÉ'
        WHEN LENGTH(password_hash) < 20 THEN '❌ TROP COURT'
        ELSE CONCAT('✅ OK (', LENGTH(password_hash), ' caractères)')
    END as password_status,
    created_at
FROM users 
WHERE username = 'admin';

-- Vérifier la relation
SELECT 'Relation utilisateur-rôle:' as '';
SELECT 
    u.id,
    u.username,
    u.role_id,
    r.id as role_id_check,
    r.name as role_name,
    r.code as role_code
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

-- =====================================================
-- ÉTAPE 2 : CORRECTION SI NÉCESSAIRE
-- =====================================================

SELECT '=== ÉTAPE 2 : CORRECTION ===' as '';

-- Créer le rôle s'il n'existe pas
INSERT IGNORE INTO roles (name, code, permissions, description, created_at)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet', NOW());

-- Récupérer l'ID du rôle
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);

-- Hash valide pour 'admin123'
SET @password_hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

-- Supprimer l'ancien admin
DELETE FROM users WHERE username = 'admin';

-- Créer le nouvel admin avec toutes les colonnes
INSERT INTO users (
    username, 
    email, 
    password_hash, 
    full_name, 
    role_id, 
    is_active, 
    created_at
)
VALUES (
    'admin',
    'admin@importprofit.pro',
    @password_hash,
    'Administrateur',
    @admin_role_id,
    1,
    NOW()
);

-- =====================================================
-- ÉTAPE 3 : VÉRIFICATION FINALE
-- =====================================================

SELECT '=== ÉTAPE 3 : VÉRIFICATION FINALE ===' as '';

SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.role_id,
    r.name as role_name,
    r.code as role_code,
    u.is_active,
    CASE 
        WHEN u.password_hash IS NOT NULL AND u.password_hash != '' 
        THEN '✅ Hash présent'
        ELSE '❌ Hash manquant'
    END as password_status
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

SELECT '✅ Script terminé! Redémarrez Flask et essayez de vous connecter.' as '';



