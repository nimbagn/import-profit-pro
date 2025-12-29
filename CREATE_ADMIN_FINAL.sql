-- =====================================================
-- SCRIPT FINAL POUR CRÉER L'UTILISATEUR ADMIN
-- À exécuter dans MySQL: mysql -u root -p madargn < CREATE_ADMIN_FINAL.sql
-- OU connectez-vous et copiez-collez ces commandes
-- =====================================================

USE madargn;

-- 1. S'assurer que le rôle admin existe
INSERT IGNORE INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW());

-- 2. Récupérer l'ID du rôle admin
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);

-- 3. Hash du mot de passe 'admin123' généré avec Werkzeug
-- Ce hash est valide pour le mot de passe 'admin123'
SET @password_hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

-- 4. Supprimer l'utilisateur admin s'il existe (pour repartir à zéro)
DELETE FROM `users` WHERE `username` = 'admin';

-- 5. Créer l'utilisateur admin
INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`)
VALUES ('admin', 'admin@importprofit.pro', @password_hash, 'Administrateur', @admin_role_id, 1, NOW());

-- 6. Vérifier la création
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    r.name as role_name,
    r.code as role_code,
    u.is_active,
    u.created_at
FROM `users` u
LEFT JOIN `roles` r ON u.role_id = r.id
WHERE u.username = 'admin';

-- 7. Afficher un message de confirmation
SELECT '✅ Utilisateur admin créé avec succès!' as message;
SELECT 'Username: admin' as info;
SELECT 'Password: admin123' as info;

