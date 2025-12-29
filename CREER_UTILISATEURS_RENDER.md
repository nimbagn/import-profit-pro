# 👥 Créer les Utilisateurs sur Render

## ⚠️ Important

Sur Render, la base de données PostgreSQL est **vide** au démarrage. Il faut créer les tables et les utilisateurs.

## 🚀 Solution : Script Python Automatique

### Option 1 : Script Python (Recommandé)

Créez un script qui s'exécute automatiquement au démarrage ou manuellement :

```python
# create_users_render.py
from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash

def create_initial_users():
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Créer le rôle admin
        admin_role = Role.query.filter_by(code='admin').first()
        if not admin_role:
            admin_role = Role(
                name='Administrateur',
                code='admin',
                permissions={"all": ["*"]},
                description='Accès complet à toutes les fonctionnalités'
            )
            db.session.add(admin_role)
            db.session.commit()
        
        # Créer l'utilisateur admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@importprofit.pro',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrateur',
                role_id=admin_role.id,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Utilisateur admin créé!")
        else:
            print("ℹ️  Utilisateur admin existe déjà")
        
        print(f"Username: admin")
        print(f"Password: admin123")

if __name__ == '__main__':
    create_initial_users()
```

### Option 2 : Via l'Application Flask

Ajoutez une route d'initialisation dans `app.py` :

```python
@app.route('/init', methods=['GET'])
def init_database():
    """Initialise la base de données avec les utilisateurs de base"""
    from models import User, Role
    from werkzeug.security import generate_password_hash
    
    # Créer les tables
    db.create_all()
    
    # Créer le rôle admin
    admin_role = Role.query.filter_by(code='admin').first()
    if not admin_role:
        admin_role = Role(
            name='Administrateur',
            code='admin',
            permissions={"all": ["*"]},
            description='Accès complet'
        )
        db.session.add(admin_role)
        db.session.commit()
    
    # Créer l'utilisateur admin
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@importprofit.pro',
            password_hash=generate_password_hash('admin123'),
            full_name='Administrateur',
            role_id=admin_role.id,
            is_active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        return "✅ Base de données initialisée! Username: admin, Password: admin123"
    else:
        return "ℹ️  Base de données déjà initialisée"
```

## 📋 Étapes pour Render

### Méthode 1 : Via l'Application (Plus Simple) ⭐ RECOMMANDÉ

1. **Une fois l'application déployée**, allez sur :
   `https://votre-app.onrender.com/init`

2. **Cela créera automatiquement** :
   - ✅ Toutes les tables
   - ✅ Le rôle admin
   - ✅ L'utilisateur admin

3. **Vous verrez un message de confirmation** avec les identifiants

4. **Connectez-vous** avec :
   - Username : `admin`
   - Password : `admin123`

5. **⚠️ IMPORTANT** : Changez le mot de passe après la première connexion !

### Méthode 2 : Via Render Shell

1. **Dans Render Dashboard** → Votre service → **Shell**

2. **Exécutez** :
   ```bash
   python3 create_users_render.py
   ```

### Méthode 3 : Via Python Local (avec connexion Render)

1. **Récupérez DATABASE_URL** depuis Render Dashboard

2. **Configurez localement** :
   ```bash
   export DATABASE_URL="postgresql://..."
   python3 create_users_render.py
   ```

## ✅ Vérification

Après création, vérifiez :

1. **Connectez-vous** à l'application
2. **Testez** avec :
   - Username : `admin`
   - Password : `admin123`

## 🔐 Sécurité

**⚠️ Important :** Après la première connexion, changez le mot de passe admin !

---

**Les utilisateurs ne sont PAS créés automatiquement. Il faut les créer après le déploiement !**

