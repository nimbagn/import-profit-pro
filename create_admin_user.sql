-- Script SQL pour créer l'utilisateur admin dans la base de données madargn
-- À exécuter directement dans MySQL: 
-- mysql -u root -p madargn < create_admin_user.sql
-- OU connectez-vous à MySQL et exécutez ces commandes manuellement

USE madargn;

-- 1. Créer le rôle admin s'il n'existe pas
INSERT IGNORE INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW());

-- 2. Récupérer l'ID du rôle admin (pour référence)
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);

-- 3. Générer un hash de mot de passe pour 'admin123'
-- Note: Ce hash est généré avec Werkzeug. Si cela ne fonctionne pas,
-- vous devrez le générer via Python ou utiliser l'application Flask
SET @password_hash = 'pbkdf2:sha256:600000$YourSaltHere$YourHashHere';

-- 4. Créer ou mettre à jour l'utilisateur admin
-- Si l'utilisateur existe, on le met à jour
UPDATE `users` 
SET 
    `email` = COALESCE(`email`, 'admin@importprofit.pro'),
    `password_hash` = @password_hash,
    `role_id` = @admin_role_id,
    `is_active` = 1,
    `full_name` = COALESCE(`full_name`, 'Administrateur')
WHERE `username` = 'admin';

-- Si l'utilisateur n'existe pas, on le crée
INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`)
SELECT 'admin', 'admin@importprofit.pro', @password_hash, 'Administrateur', @admin_role_id, 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM `users` WHERE `username` = 'admin');

-- Afficher le résultat
SELECT 'Utilisateur admin créé/mis à jour!' as message;
SELECT id, username, email, role_id, is_active FROM users WHERE username = 'admin';
