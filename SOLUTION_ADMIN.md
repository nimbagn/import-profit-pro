# Solution pour créer l'utilisateur admin

## Problème
L'utilisateur admin ne peut pas se connecter avec les identifiants `admin` / `admin123`.

## Solution : Exécuter ce script SQL directement dans MySQL

### Étape 1 : Connectez-vous à MySQL

```bash
mysql -u root -p madargn
```

### Étape 2 : Exécutez ce script SQL complet

```sql
USE madargn;

-- 1. S'assurer que le rôle admin existe
INSERT IGNORE INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW());

-- 2. Récupérer l'ID du rôle admin
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);

-- 3. Hash du mot de passe 'admin123' (généré avec Werkzeug)
SET @password_hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

-- 4. Supprimer l'ancien utilisateur admin s'il existe
DELETE FROM `users` WHERE `username` = 'admin';

-- 5. Créer le nouvel utilisateur admin
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

-- 7. Message de confirmation
SELECT '✅ Utilisateur admin créé avec succès!' as message;
SELECT 'Username: admin' as info;
SELECT 'Password: admin123' as info;
```

### Étape 3 : Vérifier que tout est correct

```sql
-- Vérifier que l'utilisateur existe
SELECT * FROM users WHERE username = 'admin';

-- Vérifier que le rôle existe
SELECT * FROM roles WHERE code = 'admin';

-- Vérifier la relation
SELECT u.username, u.email, r.name as role_name 
FROM users u 
LEFT JOIN roles r ON u.role_id = r.id 
WHERE u.username = 'admin';
```

### Étape 4 : Redémarrer Flask et tester

1. Redémarrez Flask
2. Allez sur http://localhost:5002/auth/login
3. Connectez-vous avec :
   - **Username** : `admin`
   - **Password** : `admin123`

## Si cela ne fonctionne toujours pas

Vérifiez les logs Flask dans le terminal. J'ai ajouté des messages de débogage qui indiqueront :
- Si l'utilisateur est trouvé
- Si le hash du mot de passe est valide
- Les erreurs exactes

Les messages de débogage commencent par `❌ DEBUG:` ou `✅ DEBUG:`.

## Alternative : Utiliser le fichier SQL

Si vous préférez, vous pouvez aussi exécuter le fichier directement :

```bash
mysql -u root -p madargn < CREATE_ADMIN_FINAL.sql
```

