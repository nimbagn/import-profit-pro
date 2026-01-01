# Guide : Mettre à Jour les Permissions du Magasinier sur Render

## 🎯 Objectif

Mettre à jour les permissions du rôle magasinier dans la base de données PostgreSQL sur Render.

## 🚀 Méthode 1 : Script Python (RECOMMANDÉ)

### Étape 1 : Accéder au Shell Render

1. **Connectez-vous à Render** : https://dashboard.render.com
2. **Allez dans votre service web** (Flask)
3. **Cliquez sur "Shell"** ou **"Console"** dans le menu

### Étape 2 : Exécuter le Script

Dans le shell Render, exécutez :

```bash
python3 scripts/mettre_a_jour_permissions_magasinier_render.py
```

### Étape 3 : Vérifier le Résultat

Vous devriez voir :
```
✅ PERMISSIONS MISES À JOUR AVEC SUCCÈS
📋 Nouvelles permissions:
   - movements: ['read', 'create']
   - receptions: ['read', 'create', 'update']
   - returns: ['read', 'create', 'update']
   ...
```

## 🔧 Méthode 2 : Script SQL Direct

### Étape 1 : Accéder à la Base de Données

1. Dans Render, **cliquez sur votre base de données PostgreSQL**
2. **Ouvrez l'onglet "SQL Editor"**

### Étape 2 : Copier-Coller le Script

1. **Ouvrez** le fichier `scripts/ajouter_permissions_magasinier_postgresql.sql`
2. **Copiez tout le contenu**
3. **Collez** dans l'éditeur SQL de Render
4. **Cliquez sur "Run"** ou "Execute"

### Étape 3 : Vérifier

Vous devriez voir :
```
NOTICE: Permissions du rôle magasinier mises à jour avec succès
```

## 📋 Méthode 3 : Via Python Interactif

### Dans le Shell Render

```python
python3
```

Puis exécutez :

```python
from app import app, db
from models import Role

with app.app_context():
    role = Role.query.filter_by(code='warehouse').first()
    if role:
        perms = role.permissions or {}
        perms['receptions'] = ['read', 'create', 'update']
        perms['outgoings'] = ['read', 'create', 'update']
        perms['returns'] = ['read', 'create', 'update']
        perms['orders'] = ['read']
        perms['stock_loading'] = ['read', 'verify', 'load']
        role.permissions = perms
        db.session.commit()
        print('✅ Permissions mises à jour')
        print(f'Nouvelles permissions: {role.permissions}')
    else:
        print('❌ Rôle magasinier non trouvé')
```

## ✅ Vérification

### Via SQL Editor

```sql
SELECT permissions FROM roles WHERE code = 'warehouse';
```

Vous devriez voir les permissions incluant :
- `receptions`
- `outgoings`
- `returns`
- `orders`
- `stock_loading`

### Via Python

```python
from app import app, db
from models import Role

with app.app_context():
    role = Role.query.filter_by(code='warehouse').first()
    if role:
        print(f"Permissions: {role.permissions}")
        # Vérifier les permissions spécifiques
        perms = role.permissions or {}
        print(f"receptions: {perms.get('receptions', [])}")
        print(f"outgoings: {perms.get('outgoings', [])}")
        print(f"returns: {perms.get('returns', [])}")
        print(f"orders: {perms.get('orders', [])}")
        print(f"stock_loading: {perms.get('stock_loading', [])}")
```

## 🐛 Dépannage

### Problème : "Le rôle magasinier n'existe pas"

**Solution :**
1. Vérifiez que le rôle existe :
   ```sql
   SELECT * FROM roles WHERE code = 'warehouse';
   ```
2. Si le rôle n'existe pas, créez-le d'abord via l'interface d'administration

### Problème : "Permission denied" ou Erreur de Connexion

**Solution :**
1. Vérifiez que vous êtes bien connecté à la bonne base de données
2. Vérifiez les variables d'environnement `DATABASE_URL` dans Render
3. Essayez de redémarrer le service web

### Problème : Les Permissions ne se Mettent pas à Jour

**Solution :**
1. Vérifiez que la transaction est bien commitée
2. Rechargez la page de l'application
3. Vérifiez les logs de l'application pour des erreurs
4. Redémarrez le service web si nécessaire

## 📝 Notes

1. **Idempotence** : Le script peut être exécuté plusieurs fois sans problème
2. **Sauvegarde** : Avant d'exécuter, assurez-vous d'avoir une sauvegarde de votre base de données
3. **Redémarrage** : Après la mise à jour, redémarrez l'application si nécessaire

## 🚀 Recommandation

**Utilisez la Méthode 1 (Script Python)** car elle est :
- ✅ Plus simple
- ✅ Plus sûre (gestion d'erreurs)
- ✅ Plus informative (messages détaillés)
- ✅ Idempotente (peut être exécutée plusieurs fois)

