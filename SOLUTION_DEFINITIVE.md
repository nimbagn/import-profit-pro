# Solution Définitive - Problème de connexion admin

## Diagnostic
Le test montre que la connexion échoue (code 200 au lieu de redirection 302).

## Solution en 3 commandes

### 1. Vérifier l'utilisateur dans MySQL

```bash
mysql -u root -p madargn -e "SELECT id, username, email, role_id, is_active, CASE WHEN password_hash IS NULL THEN 'PAS DE HASH' WHEN password_hash = '' THEN 'HASH VIDÉ' ELSE CONCAT('Hash OK (', LENGTH(password_hash), ' chars)') END as password_status FROM users WHERE username = 'admin';"
```

### 2. Créer/Corriger l'utilisateur admin

```bash
mysql -u root -p madargn < CREER_ADMIN.sql
```

**OU** copiez-collez dans MySQL :

```sql
USE madargn;

INSERT IGNORE INTO roles (name, code, permissions, description, created_at)
VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet', NOW());

SET @hash = 'pbkdf2:sha256:600000$AYOXyCkIQvRjje91$4df498f7be51c9e51a50562282cd1783a413e0b7a607935ea07eadd706e33fd8';
SET @role_id = (SELECT id FROM roles WHERE code = 'admin');

DELETE FROM users WHERE username = 'admin';

INSERT INTO users (username, email, password_hash, full_name, role_id, is_active, created_at)
VALUES ('admin', 'admin@importprofit.pro', @hash, 'Administrateur', @role_id, 1, NOW());

SELECT '✅ Admin créé!' as message;
SELECT * FROM users WHERE username = 'admin';
```

### 3. Redémarrer Flask

```bash
pkill -f "python.*app.py"
cd /Users/dantawi/Documents/mini_flask_import_profitability
python3 app.py
```

## Tester la connexion

1. Allez sur http://localhost:5002/auth/login
2. Username : `admin`
3. Password : `admin123`
4. **Regardez le terminal Flask** - vous devriez voir des messages comme :

```
======================================================================
🔐 TENTATIVE DE CONNEXION - Username: 'admin'
======================================================================
✅ SUCCÈS: Utilisateur 'admin' trouvé et mot de passe VALIDE
   User ID: X, Email: admin@importprofit.pro, Role: admin
======================================================================
```

## Si vous ne voyez pas les messages de débogage

Les messages s'affichent dans le terminal où Flask tourne. Si vous ne les voyez pas :
1. Vérifiez que Flask a bien redémarré après la modification de `auth.py`
2. Les messages s'affichent sur `stderr`, donc ils devraient être visibles dans le terminal

## Vérification rapide

Pour vérifier rapidement si l'utilisateur existe :

```bash
mysql -u root -p madargn -e "SELECT COUNT(*) as admin_count FROM users WHERE username = 'admin';"
```

Si le résultat est `0`, l'utilisateur n'existe pas et vous devez exécuter `CREER_ADMIN.sql`.

