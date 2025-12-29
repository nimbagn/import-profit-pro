# Instructions pour créer l'utilisateur admin

## Problème
Vous recevez "Nom d'utilisateur ou mot de passe incorrect" lors de la connexion.

## Solution

### Étape 1 : Vérifier que les colonnes existent

Exécutez d'abord le script pour ajouter les colonnes manquantes :

```bash
mysql -u root -p madargn < fix_missing_columns.sql
```

### Étape 2 : Créer l'utilisateur admin

**Option A : Via fichier SQL**
```bash
mysql -u root -p madargn < CREATE_ADMIN_FINAL.sql
```

**Option B : Manuellement dans MySQL**

1. Connectez-vous à MySQL :
```bash
mysql -u root -p madargn
```

2. Copiez et exécutez ce script :

```sql
USE madargn;

-- Créer le rôle admin
INSERT IGNORE INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW());

-- Récupérer l'ID du rôle
SET @admin_role_id = (SELECT id FROM roles WHERE code = 'admin' LIMIT 1);

-- Hash du mot de passe 'admin123'
SET @password_hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

-- Supprimer l'ancien admin s'il existe
DELETE FROM `users` WHERE `username` = 'admin';

-- Créer le nouvel admin
INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`)
VALUES ('admin', 'admin@importprofit.pro', @password_hash, 'Administrateur', @admin_role_id, 1, NOW());

-- Vérifier
SELECT id, username, email, role_id, is_active FROM users WHERE username = 'admin';
```

### Étape 3 : Vérifier la connexion

1. Redémarrez l'application Flask si nécessaire
2. Allez sur http://localhost:5002/auth/login
3. Connectez-vous avec :
   - **Username** : `admin`
   - **Password** : `admin123`

## Dépannage

Si cela ne fonctionne toujours pas :

1. **Vérifier que les colonnes existent** :
```sql
DESCRIBE users;
DESCRIBE roles;
```

2. **Vérifier que l'utilisateur existe** :
```sql
SELECT * FROM users WHERE username = 'admin';
```

3. **Vérifier que le rôle existe** :
```sql
SELECT * FROM roles WHERE code = 'admin';
```

4. **Vérifier les logs Flask** pour voir les erreurs exactes

## Identifiants par défaut

- **Username** : `admin`
- **Password** : `admin123`

⚠️ **Important** : Changez ce mot de passe en production !

