# 🔧 Guide : Résoudre la Redirection Automatique vers la Page de Login

**Problème :** Vous êtes redirigé automatiquement vers `/auth/login?next=%2F`  
**Date :** 2025-01-XX

---

## 📋 Comprendre le Problème

La redirection vers `/auth/login?next=%2F` est **normale** si vous n'êtes pas connecté. Cela signifie que :

1. ✅ Flask-Login fonctionne correctement
2. ✅ La protection des routes fonctionne
3. ⚠️ Vous devez vous connecter pour accéder à l'application

Le paramètre `next=%2F` indique que vous essayiez d'accéder à la page d'accueil (`/`) et que vous serez redirigé vers cette page après la connexion.

---

## 🔍 Diagnostic : Vérifier les Utilisateurs

### ⚡ Diagnostic Rapide (Recommandé)

Si l'admin existe déjà mais que vous ne pouvez pas vous connecter, exécutez le diagnostic complet :

```bash
python3 diagnostic_admin_render.py
```

Ce script vérifie automatiquement :
- ✅ La connexion à la base de données
- ✅ L'existence de l'utilisateur admin
- ✅ Le statut actif du compte
- ✅ La validité du mot de passe
- ✅ L'assignation du rôle
- ✅ La configuration SECRET_KEY

**Le script vous indiquera exactement quel est le problème et comment le résoudre.**

---

### Étape 1 : Vérifier s'il y a des Utilisateurs dans la Base de Données

Dans le **Shell Render**, exécutez :

```bash
python3 list_users_postgresql.py
```

**Si aucun utilisateur n'est trouvé :**
- ❌ Vous devez créer un utilisateur administrateur
- Voir la section "Créer un Utilisateur Administrateur" ci-dessous

**Si des utilisateurs existent :**
- ✅ Vérifiez qu'ils sont actifs (`is_active = True`)
- ✅ Vérifiez qu'ils ont un mot de passe valide

---

### Étape 2 : Vérifier l'Utilisateur Admin Spécifiquement

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
        print('   → Vous devez créer un utilisateur admin')
"
```

---

## 🛠️ Solution : Créer un Utilisateur Administrateur

### Méthode 1 : Via le Shell Render (Recommandé)

#### Étape 1 : Créer un Script de Création d'Admin

Créez un fichier `create_admin_render.py` dans votre projet :

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC

def create_admin():
    """Créer un utilisateur administrateur"""
    with app.app_context():
        try:
            # Vérifier si l'admin existe déjà
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print("⚠️  L'utilisateur 'admin' existe déjà")
                print(f"   ID: {admin_user.id}")
                print(f"   Email: {admin_user.email}")
                print(f"   Actif: {admin_user.is_active}")
                
                # Vérifier le mot de passe
                if not admin_user.password_hash:
                    print("   ❌ Pas de mot de passe - Réinitialisation...")
                    admin_user.password_hash = generate_password_hash('admin123')
                    db.session.commit()
                    print("   ✅ Mot de passe réinitialisé: admin123")
                else:
                    print("   ✅ Mot de passe présent")
                
                return admin_user
            
            # Récupérer le rôle admin
            admin_role = Role.query.filter_by(code='admin').first()
            if not admin_role:
                print("❌ Le rôle 'admin' n'existe pas")
                print("   → Créez d'abord les rôles dans la base de données")
                return None
            
            # Créer l'utilisateur admin
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrateur',
                role_id=admin_role.id,
                is_active=True,
                created_at=datetime.now(UTC)
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("=" * 60)
            print("✅ UTILISATEUR ADMIN CRÉÉ AVEC SUCCÈS")
            print("=" * 60)
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"Email: admin@example.com")
            print(f"Rôle: {admin_role.name}")
            print()
            print("⚠️  IMPORTANT: Changez le mot de passe après la première connexion!")
            print("=" * 60)
            
            return admin_user
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'admin: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None

if __name__ == '__main__':
    create_admin()
```

#### Étape 2 : Exécuter le Script dans le Shell Render

```bash
python3 create_admin_render.py
```

**Résultat attendu :**
```
============================================================
✅ UTILISATEUR ADMIN CRÉÉ AVEC SUCCÈS
============================================================
Username: admin
Password: admin123
Email: admin@example.com
Rôle: Administrateur

⚠️  IMPORTANT: Changez le mot de passe après la première connexion!
============================================================
```

---

### Méthode 2 : Via SQL Direct

Si vous préférez utiliser SQL directement :

```bash
python3 -c "
from app import app
from models import db, User, Role
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC

with app.app_context():
    # Récupérer le rôle admin
    admin_role = Role.query.filter_by(code='admin').first()
    if not admin_role:
        print('❌ Rôle admin non trouvé')
    else:
        # Vérifier si l'admin existe
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('⚠️  Admin existe déjà')
            if not admin.password_hash:
                admin.password_hash = generate_password_hash('admin123')
                db.session.commit()
                print('✅ Mot de passe réinitialisé: admin123')
        else:
            # Créer l'admin
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrateur',
                role_id=admin_role.id,
                is_active=True,
                created_at=datetime.now(UTC)
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin créé: admin / admin123')
"
```

---

## 🔐 Se Connecter

Une fois l'utilisateur admin créé :

1. Allez sur : `https://import-profit-pro.onrender.com/auth/login`
2. Entrez les identifiants :
   - **Username:** `admin`
   - **Password:** `admin123`
3. Cliquez sur "Se connecter"
4. Vous serez redirigé vers la page d'accueil

---

## ⚠️ Problèmes Courants

### Problème 1 : "Nom d'utilisateur ou mot de passe incorrect"

**Causes possibles :**
- L'utilisateur n'existe pas
- Le mot de passe est incorrect
- Le hash du mot de passe est corrompu

**Solution :**
```bash
# Réinitialiser le mot de passe de l'admin
python3 -c "
from app import app
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()
        print('✅ Mot de passe réinitialisé: admin123')
    else:
        print('❌ Admin non trouvé')
"
```

---

### Problème 2 : "Votre compte est désactivé"

**Cause :** L'utilisateur a `is_active = False`

**Solution :**
```bash
python3 -c "
from app import app
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.is_active = True
        db.session.commit()
        print('✅ Compte admin activé')
    else:
        print('❌ Admin non trouvé')
"
```

---

### Problème 3 : Le Rôle Admin n'Existe Pas

**Solution :**
```bash
python3 -c "
from app import app
from models import db, Role

with app.app_context():
    # Vérifier les rôles existants
    roles = Role.query.all()
    print('Rôles existants:')
    for r in roles:
        print(f'  - {r.name} ({r.code})')
    
    # Créer le rôle admin s'il n'existe pas
    admin_role = Role.query.filter_by(code='admin').first()
    if not admin_role:
        admin_role = Role(
            name='Administrateur',
            code='admin',
            description='Accès complet à toutes les fonctionnalités'
        )
        db.session.add(admin_role)
        db.session.commit()
        print('✅ Rôle admin créé')
    else:
        print('✅ Rôle admin existe déjà')
"
```

---

### Problème 4 : Erreur de Session / Cookie

**Symptômes :**
- Vous vous connectez mais êtes immédiatement redirigé vers login
- La session ne persiste pas

**Solutions :**

1. **Vérifier SECRET_KEY :**
   - Dans Render Dashboard > Environment
   - Assurez-vous que `SECRET_KEY` est défini et unique

2. **Vérifier les cookies :**
   - Ouvrez les outils de développement (F12)
   - Onglet Application > Cookies
   - Vérifiez que les cookies de session sont créés

3. **Vérifier SESSION_COOKIE_SECURE :**
   - Sur Render (HTTPS), cela devrait être `True`
   - Vérifiez dans `config.py`

---

## 🧪 Test de Connexion

Pour tester si la connexion fonctionne :

```bash
python3 -c "
from app import app
from models import User
from werkzeug.security import check_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f'✅ Utilisateur trouvé: {admin.username}')
        print(f'   Email: {admin.email}')
        print(f'   Actif: {admin.is_active}')
        
        if admin.password_hash:
            # Tester le mot de passe
            is_valid = check_password_hash(admin.password_hash, 'admin123')
            print(f'   Mot de passe \"admin123\": {\"✅ Valide\" if is_valid else \"❌ Invalide\"}')
        else:
            print('   ❌ Pas de mot de passe')
    else:
        print('❌ Admin non trouvé')
"
```

---

## 📝 Checklist de Résolution

- [ ] Vérifier qu'il y a des utilisateurs dans la base de données
- [ ] Vérifier que l'utilisateur admin existe
- [ ] Vérifier que l'utilisateur admin est actif (`is_active = True`)
- [ ] Vérifier que l'utilisateur admin a un mot de passe valide
- [ ] Vérifier que le rôle admin existe
- [ ] Tester la connexion avec les identifiants
- [ ] Vérifier que `SECRET_KEY` est configuré dans Render
- [ ] Vérifier les logs Render pour les erreurs

---

## 🆘 Si Rien ne Fonctionne

1. **Vérifier les logs Render :**
   - Dashboard > Service > Logs
   - Cherchez les erreurs liées à l'authentification

2. **Vérifier la connexion à la base de données :**
   ```bash
   python3 test_connection_postgresql.py
   ```

3. **Vérifier que les tables existent :**
   ```bash
   python3 -c "
   from app import app
   from models import db
   from sqlalchemy import inspect
   
   with app.app_context():
       inspector = inspect(db.engine)
       tables = inspector.get_table_names()
       required = ['users', 'roles']
       for table in required:
           if table in tables:
               print(f'✅ {table}')
           else:
               print(f'❌ {table} manquant')
   "
   ```

---

## ✅ Résumé

La redirection vers `/auth/login?next=%2F` est **normale** si vous n'êtes pas connecté. Pour résoudre le problème :

1. **Créez un utilisateur admin** si aucun n'existe
2. **Connectez-vous** avec les identifiants admin
3. **Changez le mot de passe** après la première connexion

**Identifiants par défaut après création :**
- Username: `admin`
- Password: `admin123`

---

**🎉 Une fois connecté, vous accéderez normalement à l'application !**

