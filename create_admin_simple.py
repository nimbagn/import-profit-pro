#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour créer l'utilisateur admin
Génère le hash du mot de passe et affiche les commandes SQL à exécuter
"""

from werkzeug.security import generate_password_hash

# Générer le hash pour 'admin123'
password = 'admin123'
password_hash = generate_password_hash(password)

print("=" * 60)
print("CRÉATION DE L'UTILISATEUR ADMIN")
print("=" * 60)
print("\n1. Connectez-vous à MySQL:")
print("   mysql -u root -p madargn")
print("\n2. Exécutez ces commandes SQL:")
print("=" * 60)
print(f"""
USE madargn;

-- Créer le rôle admin s'il n'existe pas
INSERT IGNORE INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`)
VALUES ('Administrateur', 'admin', '{{"all": ["*"]}}', 'Accès complet à toutes les fonctionnalités', NOW());

-- Récupérer l'ID du rôle
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);

-- Créer ou mettre à jour l'utilisateur admin
-- Hash du mot de passe 'admin123':
SET @password_hash = '{password_hash}';

-- Mettre à jour si existe
UPDATE `users` 
SET 
    `email` = 'admin@importprofit.pro',
    `password_hash` = @password_hash,
    `role_id` = @admin_role_id,
    `is_active` = 1,
    `full_name` = 'Administrateur'
WHERE `username` = 'admin';

-- Créer si n'existe pas
INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`)
SELECT 'admin', 'admin@importprofit.pro', @password_hash, 'Administrateur', @admin_role_id, 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM `users` WHERE `username` = 'admin');

-- Vérifier
SELECT id, username, email, role_id, is_active FROM users WHERE username = 'admin';
""")
print("=" * 60)
print("\n✅ Identifiants:")
print(f"   Username: admin")
print(f"   Password: admin123")
print("=" * 60)

