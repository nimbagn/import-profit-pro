# Guide de résolution - Problème de connexion admin

## 🔍 Diagnostic

Quand vous essayez de vous connecter avec `admin` / `admin123`, vous recevez "Nom d'utilisateur ou mot de passe incorrect".

## ✅ Solution en 3 étapes

### Étape 1 : Vérifier les colonnes

Assurez-vous que les colonnes `username` et `password_hash` existent dans la table `users` :

```bash
mysql -u root -p madargn
```

```sql
DESCRIBE users;
```

Si les colonnes `username` ou `password_hash` n'existent pas, exécutez d'abord :
```bash
mysql -u root -p madargn < fix_missing_columns.sql
```

### Étape 2 : Créer l'utilisateur admin

Exécutez le script SQL :

```bash
mysql -u root -p madargn < CREER_ADMIN.sql
```

**OU** copiez-collez directement dans MySQL :

```sql
USE madargn;

INSERT IGNORE INTO roles (name, code, permissions, description, created_at)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet', NOW());

SET @hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';

DELETE FROM users WHERE username = 'admin';

INSERT INTO users (username, email, password_hash, full_name, role_id, is_active, created_at)
SELECT 'admin', 'admin@importprofit.pro', @hash, 'Administrateur', 
       (SELECT id FROM roles WHERE code = 'admin' LIMIT 1), 1, NOW();

SELECT username, email, is_active FROM users WHERE username = 'admin';
```

### Étape 3 : Tester la connexion

1. Allez sur http://localhost:5002/auth/login
2. Utilisez :
   - **Username** : `admin`
   - **Password** : `admin123`

## 🔍 Vérification des logs

Si cela ne fonctionne toujours pas, regardez les logs Flask dans le terminal. Vous devriez voir des messages comme :

- `❌ DEBUG: Utilisateur 'admin' non trouvé` → L'utilisateur n'existe pas
- `❌ DEBUG: Hash du mot de passe invalide` → Le hash est incorrect
- `✅ DEBUG: Utilisateur 'admin' trouvé et mot de passe valide` → Tout est OK

## 📝 Identifiants

- **Username** : `admin`
- **Password** : `admin123`

