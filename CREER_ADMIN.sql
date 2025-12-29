-- =====================================================
-- SCRIPT SIMPLE POUR CRÉER L'UTILISATEUR ADMIN
-- Exécutez: mysql -u root -p madargn < CREER_ADMIN.sql
-- =====================================================

USE madargn;

-- 1. Créer le rôle admin
INSERT IGNORE INTO roles (name, code, permissions, description, created_at)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet', NOW());

-- 2. Hash du mot de passe 'admin123'
SET @hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

-- 3. Supprimer l'ancien admin
DELETE FROM users WHERE username = 'admin';

-- 4. Créer le nouvel admin
INSERT INTO users (username, email, password_hash, full_name, role_id, is_active, created_at)
SELECT 'admin', 'admin@importprofit.pro', @hash, 'Administrateur', 
       (SELECT id FROM roles WHERE code = 'admin' LIMIT 1), 1, NOW();

-- 5. Vérifier
SELECT '✅ Admin créé!' as message;
SELECT username, email, is_active FROM users WHERE username = 'admin';

