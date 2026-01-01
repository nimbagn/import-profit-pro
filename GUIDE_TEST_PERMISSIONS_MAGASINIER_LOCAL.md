# Guide de Test Local - Permissions Magasinier

## 🎯 Objectif

Tester localement que le magasinier a accès à toutes les fonctionnalités du module `/stocks` après l'ajout des permissions `receptions` et `returns`.

## 📋 Prérequis

1. ✅ Serveur Flask démarré sur `http://localhost:5002`
2. ✅ Base de données connectée
3. ✅ Rôle magasinier existant dans la base de données

## 🧪 Étape 1 : Vérifier les Permissions dans la Base de Données

### Option A : Script Python de Test

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
python3 test_permissions_magasinier.py
```

Ce script va :
- ✅ Vérifier que le rôle magasinier existe
- ✅ Vérifier que toutes les permissions sont présentes
- ✅ Créer un utilisateur de test si nécessaire
- ✅ Tester les permissions avec `has_permission()`

### Option B : Vérification Manuelle SQL

**Pour PostgreSQL :**
```sql
-- Vérifier les permissions du rôle magasinier
SELECT id, name, code, permissions 
FROM roles 
WHERE code = 'warehouse';

-- Vérifier qu'un utilisateur magasinier existe
SELECT u.id, u.username, u.email, r.name as role_name, r.permissions
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE r.code = 'warehouse';
```

**Pour MySQL :**
```sql
-- Vérifier les permissions du rôle magasinier
SELECT id, name, code, permissions 
FROM roles 
WHERE code = 'warehouse';

-- Vérifier qu'un utilisateur magasinier existe
SELECT u.id, u.username, u.email, r.name as role_name, r.permissions
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE r.code = 'warehouse';
```

## 🔧 Étape 2 : Mettre à Jour les Permissions (si nécessaire)

Si les permissions `receptions` et `returns` manquent, exécutez le script SQL approprié :

### Pour PostgreSQL :
```bash
# Via psql
psql $DATABASE_URL -f scripts/ajouter_permissions_magasinier_postgresql.sql

# Ou via Python
python3 -c "
from app import app, db
from models import Role
import json

with app.app_context():
    role = Role.query.filter_by(code='warehouse').first()
    if role:
        perms = role.permissions or {}
        perms['receptions'] = ['read', 'create', 'update']
        perms['returns'] = ['read', 'create', 'update']
        role.permissions = perms
        db.session.commit()
        print('✅ Permissions mises à jour')
    else:
        print('❌ Rôle magasinier non trouvé')
"
```

### Pour MySQL :
```bash
mysql -u USERNAME -p DATABASE_NAME < scripts/ajouter_permissions_magasinier_mysql.sql
```

## 👤 Étape 3 : Créer/Utiliser un Utilisateur Magasinier

### Option A : Via le Script de Test

Le script `test_permissions_magasinier.py` crée automatiquement un utilisateur de test :
- **Username**: `test_warehouse`
- **Password**: `test123`

### Option B : Via l'Interface Web

1. Connectez-vous en tant qu'admin : `http://localhost:5002/auth/login`
   - Username: `admin`
   - Password: `admin123`

2. Créer un utilisateur magasinier :
   - Aller dans `/auth/users`
   - Cliquer sur "Nouvel Utilisateur"
   - Remplir le formulaire :
     - Username: `magasinier_test`
     - Email: `magasinier@test.com`
     - Rôle: **Magasinier**
     - Mot de passe: `test123`
   - Sauvegarder

### Option C : Via SQL Direct

```sql
-- Créer un utilisateur magasinier de test
INSERT INTO users (username, email, password_hash, full_name, role_id, is_active, created_at)
SELECT 
    'magasinier_test',
    'magasinier@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5K5vJ5K5vJ5K5',  -- Mot de passe: test123
    'Magasinier Test',
    (SELECT id FROM roles WHERE code = 'warehouse'),
    TRUE,
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE username = 'magasinier_test'
);
```

## 🌐 Étape 4 : Tester dans le Navigateur

### 1. Se Connecter en tant que Magasinier

1. Ouvrir : `http://localhost:5002/auth/login`
2. Se connecter avec :
   - Username: `test_warehouse` (ou celui créé)
   - Password: `test123`

### 2. Tester l'Accès aux Routes

Vérifiez que vous pouvez accéder à toutes ces routes **sans erreur de permission** :

#### ✅ Stocks de Base
- [ ] `http://localhost:5002/stocks/depot/1` - Stock d'un dépôt
- [ ] `http://localhost:5002/stocks/vehicle/1` - Stock d'un véhicule
- [ ] `http://localhost:5002/stocks/summary` - Récapitulatif de stock

#### ✅ Mouvements
- [ ] `http://localhost:5002/stocks/movements` - Liste des mouvements
- [ ] `http://localhost:5002/stocks/movements/new` - Créer un mouvement
- [ ] `http://localhost:5002/stocks/movements/export/excel` - Export Excel

#### ✅ Réceptions (NOUVELLES PERMISSIONS)
- [ ] `http://localhost:5002/stocks/receptions` - Liste des réceptions ✅
- [ ] `http://localhost:5002/stocks/receptions/new` - Créer une réception ✅
- [ ] `http://localhost:5002/stocks/receptions/export/excel` - Export Excel ✅

#### ✅ Sorties
- [ ] `http://localhost:5002/stocks/outgoings` - Liste des sorties
- [ ] `http://localhost:5002/stocks/outgoings/new` - Créer une sortie
- [ ] `http://localhost:5002/stocks/outgoings/export/excel` - Export Excel

#### ✅ Retours (NOUVELLES PERMISSIONS)
- [ ] `http://localhost:5002/stocks/returns` - Liste des retours ✅
- [ ] `http://localhost:5002/stocks/returns/new` - Créer un retour ✅
- [ ] `http://localhost:5002/stocks/returns/export/excel` - Export Excel ✅

#### ✅ Dashboard Magasinier
- [ ] `http://localhost:5002/stocks/warehouse/dashboard` - Dashboard magasinier
- [ ] `http://localhost:5002/stocks/warehouse/loading/1` - Détail chargement

#### ✅ Historique
- [ ] `http://localhost:5002/stocks/history` - Historique des mouvements

### 3. Vérifier les Messages d'Erreur

Si vous voyez un message comme :
```
❌ Vous n'avez pas la permission d'accéder à cette page
```

Cela signifie que les permissions ne sont pas correctement configurées dans la base de données.

## 🔍 Étape 5 : Vérifier les Logs

Si vous rencontrez des problèmes, vérifiez les logs du serveur Flask :

```bash
# Si le serveur tourne en arrière-plan
tail -f flask_output.log

# Ou si vous avez démarré avec python3 app.py
# Les logs s'affichent directement dans le terminal
```

## ✅ Checklist de Validation

- [ ] Le script `test_permissions_magasinier.py` passe tous les tests
- [ ] L'utilisateur magasinier peut se connecter
- [ ] Accès à `/stocks/receptions` sans erreur
- [ ] Accès à `/stocks/receptions/new` sans erreur
- [ ] Accès à `/stocks/returns` sans erreur
- [ ] Accès à `/stocks/returns/new` sans erreur
- [ ] Accès à `/stocks/outgoings` sans erreur
- [ ] Accès à `/stocks/movements` sans erreur
- [ ] Accès à `/stocks/summary` sans erreur
- [ ] Accès à `/stocks/warehouse/dashboard` sans erreur
- [ ] Les exports Excel fonctionnent pour tous les modules

## 🐛 Dépannage

### Problème : "Vous n'avez pas la permission d'accéder à cette page"

**Solution :**
1. Vérifiez que le script SQL a été exécuté
2. Vérifiez les permissions dans la base de données :
   ```sql
   SELECT permissions FROM roles WHERE code = 'warehouse';
   ```
3. Assurez-vous que les permissions contiennent `receptions` et `returns`
4. Redémarrez le serveur Flask

### Problème : L'utilisateur n'existe pas

**Solution :**
1. Créez un utilisateur via l'interface web (admin)
2. Ou utilisez le script de test qui crée automatiquement `test_warehouse`

### Problème : Le serveur ne démarre pas

**Solution :**
```bash
# Arrêter tous les processus Flask
pkill -f "python.*app.py"
lsof -ti:5002 | xargs kill -9

# Redémarrer
python3 app.py
```

## 📝 Notes

- Les permissions sont vérifiées par la fonction `has_permission()` dans `auth.py`
- L'admin a tous les droits et passe toutes les vérifications
- Les permissions sont stockées en JSON dans la colonne `permissions` de la table `roles`

## 🚀 Prochaines Étapes

Une fois les tests locaux validés :
1. Exécuter le script SQL sur Render (PostgreSQL)
2. Tester sur l'environnement de production
3. Vérifier que tous les magasiniers ont les bonnes permissions

