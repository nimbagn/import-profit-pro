# 👥 Guide : Voir les Utilisateurs dans la Base de Données PostgreSQL sur Render

**Date :** 2025-01-XX  
**Base de données :** PostgreSQL (Render)

---

## 📋 Vue d'Ensemble

Ce guide vous explique **plusieurs méthodes** pour consulter les utilisateurs créés dans votre base de données PostgreSQL sur Render :

1. ✅ **Via un script Python** (Recommandé - le plus simple)
2. ✅ **Via l'interface web de l'application**
3. ✅ **Via SQL direct dans le Shell Render**

---

## 🎯 MÉTHODE 1 : Via le Script Python (Recommandé)

### Étape 1 : Accéder au Shell Render

1. Allez sur [Render Dashboard](https://dashboard.render.com)
2. Sélectionnez votre **service Web**
3. Cliquez sur **"Shell"** dans le menu de gauche
4. Un terminal s'ouvre dans votre navigateur

---

### Étape 2 : Lister Tous les Utilisateurs (Détaillé)

Exécutez le script pour voir tous les utilisateurs avec leurs informations complètes :

```bash
python3 list_users_postgresql.py
```

**Résultat attendu :**
```
================================================================================
📋 LISTE DES UTILISATEURS
================================================================================

📊 Statistiques:
   Total: 5 utilisateur(s)
   Actifs: 4
   Inactifs: 1

================================================================================

👤 Utilisateur #1
   ID: 1
   Username: admin
   Email: admin@example.com
   Nom complet: Administrateur
   Téléphone: +1234567890
   Rôle: Administrateur (admin)
   Région: Siège
   Statut: ✅ Actif
   Mot de passe: ✅ Hash présent (60 caractères)
   Dernière connexion: 2025-01-15 14:30:00
   Créé le: 2025-01-10 10:00:00

👤 Utilisateur #2
   ...
```

---

### Étape 3 : Liste Simplifiée (Tableau)

Pour une vue plus compacte :

```bash
python3 list_users_postgresql.py simple
```

**Résultat attendu :**
```
📋 LISTE DES UTILISATEURS (Format Tableau)
====================================================================================================
ID    Username             Email                          Rôle            Région          Statut
----------------------------------------------------------------------------------------------------
1     admin                admin@example.com              Administrateur  Siège           ✅ Actif
2     commercial1          commercial1@example.com        Commercial      Région Nord     ✅ Actif
3     manager1             manager1@example.com          Manager         Région Sud      ✅ Actif
====================================================================================================
Total: 3 utilisateur(s)
```

---

### Étape 4 : Liste par Rôle

Pour voir les utilisateurs groupés par rôle :

```bash
python3 list_users_postgresql.py by-role
```

**Résultat attendu :**
```
📋 UTILISATEURS PAR RÔLE
================================================================================

🔹 Administrateur (admin) - 1 utilisateur(s)
   ✅ admin (admin@example.com)

🔹 Commercial (commercial) - 2 utilisateur(s)
   ✅ commercial1 (commercial1@example.com)
   ✅ commercial2 (commercial2@example.com)

🔹 Manager (manager) - 1 utilisateur(s)
   ✅ manager1 (manager1@example.com)
```

---

## 🌐 MÉTHODE 2 : Via l'Interface Web

Si vous avez accès à l'application en ligne :

### Option 1 : Page Liste des Utilisateurs

1. Connectez-vous à votre application sur Render
2. Allez sur la route : `/auth/users`
3. Vous verrez la liste complète des utilisateurs avec filtres

**Note :** Cette page nécessite la permission `users.read`

### Option 2 : Module RH

1. Connectez-vous à l'application
2. Allez sur : `/rh/personnel`
3. Vous verrez la liste du personnel avec filtres par région, rôle, etc.

**Note :** Cette page nécessite un rôle RH ou la permission `users.read`

---

## 💻 MÉTHODE 3 : Via SQL Direct

### Étape 1 : Se Connecter à PostgreSQL

Dans le Shell Render, vous pouvez exécuter des requêtes SQL directement :

```bash
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('''
        SELECT 
            u.id,
            u.username,
            u.email,
            u.full_name,
            u.phone,
            r.name as role_name,
            reg.name as region_name,
            u.is_active,
            u.created_at
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        LEFT JOIN regions reg ON u.region_id = reg.id
        ORDER BY u.id
    '''))
    
    print('ID | Username | Email | Rôle | Région | Statut | Créé le')
    print('-' * 80)
    for row in result:
        status = 'Actif' if row.is_active else 'Inactif'
        print(f'{row.id} | {row.username} | {row.email} | {row.role_name or \"N/A\"} | {row.region_name or \"N/A\"} | {status} | {row.created_at}')
"
```

---

## 🔍 Requêtes SQL Utiles

### Voir Tous les Utilisateurs

```python
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('SELECT id, username, email, is_active FROM users ORDER BY id'))
    for row in result:
        print(f'ID: {row.id}, Username: {row.username}, Email: {row.email}, Actif: {row.is_active}')
"
```

### Compter les Utilisateurs

```python
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) as total FROM users'))
    total = result.scalar()
    print(f'Total utilisateurs: {total}')
    
    result = db.session.execute(db.text('SELECT COUNT(*) FROM users WHERE is_active = true'))
    active = result.scalar()
    print(f'Utilisateurs actifs: {active}')
"
```

### Voir un Utilisateur Spécifique

```python
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('''
        SELECT u.*, r.name as role_name 
        FROM users u 
        LEFT JOIN roles r ON u.role_id = r.id 
        WHERE u.username = :username
    '''), {'username': 'admin'})
    
    row = result.fetchone()
    if row:
        print(f'Username: {row.username}')
        print(f'Email: {row.email}')
        print(f'Rôle: {row.role_name}')
        print(f'Actif: {row.is_active}')
    else:
        print('Utilisateur non trouvé')
"
```

### Voir les Utilisateurs par Rôle

```python
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('''
        SELECT r.name as role_name, COUNT(u.id) as user_count
        FROM roles r
        LEFT JOIN users u ON r.id = u.role_id
        GROUP BY r.id, r.name
        ORDER BY user_count DESC
    '''))
    
    print('Rôle | Nombre d\'utilisateurs')
    print('-' * 40)
    for row in result:
        print(f'{row.role_name} | {row.user_count}')
"
```

### Voir les Utilisateurs par Région

```python
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('''
        SELECT reg.name as region_name, COUNT(u.id) as user_count
        FROM regions reg
        LEFT JOIN users u ON reg.id = u.region_id
        GROUP BY reg.id, reg.name
        ORDER BY user_count DESC
    '''))
    
    print('Région | Nombre d\'utilisateurs')
    print('-' * 40)
    for row in result:
        print(f'{row.region_name or \"Sans région\"} | {row.user_count}')
"
```

---

## 📊 Vérifications Utiles

### Vérifier l'Utilisateur Admin

```bash
python3 -c "
from app import app
from models import User, Role

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f'✅ Admin trouvé: {admin.username} ({admin.email})')
        print(f'   Rôle: {admin.role.name if admin.role else \"N/A\"}')
        print(f'   Actif: {admin.is_active}')
        print(f'   Mot de passe: {\"✅ Hash présent\" if admin.password_hash else \"❌ Aucun hash\"}')
    else:
        print('❌ Utilisateur admin non trouvé')
"
```

### Vérifier les Utilisateurs Sans Mot de Passe

```bash
python3 -c "
from app import app
from models import User

with app.app_context():
    users_no_pwd = User.query.filter(
        (User.password_hash == None) | (User.password_hash == '')
    ).all()
    
    if users_no_pwd:
        print(f'⚠️ {len(users_no_pwd)} utilisateur(s) sans mot de passe:')
        for u in users_no_pwd:
            print(f'   - {u.username} ({u.email})')
    else:
        print('✅ Tous les utilisateurs ont un mot de passe')
"
```

### Vérifier les Utilisateurs Inactifs

```bash
python3 -c "
from app import app
from models import User

with app.app_context():
    inactive = User.query.filter_by(is_active=False).all()
    
    if inactive:
        print(f'📋 {len(inactive)} utilisateur(s) inactif(s):')
        for u in inactive:
            print(f'   - {u.username} ({u.email})')
    else:
        print('✅ Tous les utilisateurs sont actifs')
"
```

---

## 🎯 Exemples Pratiques

### Exemple 1 : Voir Tous les Utilisateurs Actifs

```bash
python3 list_users_postgresql.py simple
```

Puis filtrez visuellement les lignes avec "✅ Actif"

### Exemple 2 : Trouver un Utilisateur par Email

```python
python3 -c "
from app import app
from models import User

with app.app_context():
    email = 'admin@example.com'  # Remplacez par l'email recherché
    user = User.query.filter_by(email=email).first()
    
    if user:
        print(f'✅ Utilisateur trouvé:')
        print(f'   Username: {user.username}')
        print(f'   Email: {user.email}')
        print(f'   Rôle: {user.role.name if user.role else \"N/A\"}')
        print(f'   Actif: {user.is_active}')
    else:
        print(f'❌ Aucun utilisateur avec l\'email: {email}')
"
```

### Exemple 3 : Statistiques Complètes

```python
python3 -c "
from app import app
from models import User, Role, Region

with app.app_context():
    total = User.query.count()
    active = User.query.filter_by(is_active=True).count()
    inactive = total - active
    
    print('📊 STATISTIQUES UTILISATEURS')
    print('=' * 50)
    print(f'Total: {total}')
    print(f'Actifs: {active}')
    print(f'Inactifs: {inactive}')
    print()
    
    # Par rôle
    print('Par rôle:')
    roles = Role.query.all()
    for role in roles:
        count = User.query.filter_by(role_id=role.id).count()
        print(f'  {role.name}: {count}')
    
    # Par région
    print()
    print('Par région:')
    regions = Region.query.all()
    for region in regions:
        count = User.query.filter_by(region_id=region.id).count()
        print(f'  {region.name}: {count}')
"
```

---

## ⚠️ Notes Importantes

- ✅ Le script `list_users_postgresql.py` fonctionne sur Render et en local
- ✅ Les mots de passe ne sont jamais affichés (seulement le hash)
- ✅ Les requêtes SQL sont sécurisées via SQLAlchemy
- ⚠️ Assurez-vous d'avoir les permissions nécessaires pour accéder à la base de données

---

## 🆘 Dépannage

### Erreur : "Module not found"

**Solution :**
```bash
pip install -r requirements.txt
```

### Erreur : "Can't connect to database"

**Solution :**
1. Vérifiez que `DATABASE_URL` est configurée dans Render Dashboard > Environment
2. Vérifiez que la base de données PostgreSQL est active

### Erreur : "No such table: users"

**Solution :**
La table `users` n'existe pas encore. Exécutez les migrations nécessaires.

---

## 📝 Checklist

- [ ] Script `list_users_postgresql.py` disponible
- [ ] Connexion à la base de données fonctionnelle
- [ ] Permissions d'accès à la base de données
- [ ] Compréhension des différentes méthodes de consultation

---

**🎉 Vous pouvez maintenant consulter facilement tous les utilisateurs de votre base de données !**

