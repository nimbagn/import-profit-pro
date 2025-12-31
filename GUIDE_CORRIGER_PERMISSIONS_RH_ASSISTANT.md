# Guide : Corriger les permissions du rôle RH Assistant

## 🔍 Problème

L'assistante RH ne parvient pas à créer d'employés externes alors qu'elle devrait avoir cette permission.

## ✅ Solution

Les permissions du rôle `rh_assistant` doivent inclure `employees.create`. Voici comment les corriger :

### Option 1 : Via Script SQL (Recommandé)

#### Pour PostgreSQL (Render)

1. **Connectez-vous à votre base de données PostgreSQL sur Render**
   - Allez dans votre dashboard Render
   - Ouvrez votre base de données PostgreSQL
   - Cliquez sur "Connect" ou utilisez psql

2. **Exécutez le script SQL** :
   ```sql
   UPDATE roles 
   SET permissions = '{
       "users": ["read", "create", "update"],
       "employees": ["read", "create", "update"],
       "contracts": ["read", "create", "update"],
       "trainings": ["read", "create", "update"],
       "evaluations": ["read", "create"],
       "absences": ["read", "create", "update"],
       "reports": ["read"]
   }'::jsonb
   WHERE code = 'rh_assistant';
   ```

3. **Vérifiez que la mise à jour a fonctionné** :
   ```sql
   SELECT id, name, code, permissions
   FROM roles 
   WHERE code = 'rh_assistant';
   ```

#### Pour MySQL (Local)

1. **Connectez-vous à MySQL** :
   ```bash
   mysql -u root -p madargn
   ```

2. **Exécutez le script SQL** :
   ```sql
   UPDATE roles 
   SET permissions = JSON_OBJECT(
       'users', JSON_ARRAY('read', 'create', 'update'),
       'employees', JSON_ARRAY('read', 'create', 'update'),
       'contracts', JSON_ARRAY('read', 'create', 'update'),
       'trainings', JSON_ARRAY('read', 'create', 'update'),
       'evaluations', JSON_ARRAY('read', 'create'),
       'absences', JSON_ARRAY('read', 'create', 'update'),
       'reports', JSON_ARRAY('read')
   )
   WHERE code = 'rh_assistant';
   ```

3. **Vérifiez** :
   ```sql
   SELECT id, name, code, permissions
   FROM roles 
   WHERE code = 'rh_assistant';
   ```

### Option 2 : Via Python (Script)

Si vous avez accès à l'environnement Python :

```python
from app import app, db
from models import Role
import json

with app.app_context():
    role = Role.query.filter_by(code='rh_assistant').first()
    if role:
        role.permissions = {
            'users': ['read', 'create', 'update'],
            'employees': ['read', 'create', 'update'],
            'contracts': ['read', 'create', 'update'],
            'trainings': ['read', 'create', 'update'],
            'evaluations': ['read', 'create'],
            'absences': ['read', 'create', 'update'],
            'reports': ['read']
        }
        db.session.commit()
        print("✅ Permissions mises à jour avec succès!")
    else:
        print("❌ Le rôle rh_assistant n'existe pas")
```

### Option 3 : Via l'interface Web (Admin)

1. **Connectez-vous en tant qu'administrateur**
2. Allez sur : **Auth** → **Utilisateurs** → **Liste des utilisateurs**
3. Trouvez l'utilisateur avec le rôle `rh_assistant`
4. Cliquez sur **Modifier**
5. Vérifiez que le rôle est bien `RH Assistant`
6. Si le rôle n'existe pas ou est incorrect, créez-le d'abord avec :
   ```bash
   python3 create_roles_rh.py
   ```

## 📋 Permissions attendues pour rh_assistant

Le rôle `rh_assistant` doit avoir les permissions suivantes :

```json
{
    "users": ["read", "create", "update"],
    "employees": ["read", "create", "update"],
    "contracts": ["read", "create", "update"],
    "trainings": ["read", "create", "update"],
    "evaluations": ["read", "create"],
    "absences": ["read", "create", "update"],
    "reports": ["read"]
}
```

**Important** : La permission `employees.create` doit être présente dans la liste `employees`.

## 🔍 Vérification

Après la correction, l'assistante RH devrait pouvoir :

1. ✅ Accéder à la liste des employés : `/rh/employees`
2. ✅ Créer un nouvel employé : `/rh/employees/new`
3. ✅ Modifier un employé existant : `/rh/employees/<id>/edit`
4. ✅ Voir les détails d'un employé : `/rh/employees/<id>`

## ⚠️ Si le problème persiste

1. **Vérifiez que l'utilisateur a bien le rôle `rh_assistant`** :
   ```sql
   SELECT u.id, u.username, u.full_name, r.name, r.code
   FROM users u
   JOIN roles r ON u.role_id = r.id
   WHERE r.code = 'rh_assistant';
   ```

2. **Vérifiez les permissions supplémentaires** :
   - Si l'utilisateur a des `additional_permissions`, elles peuvent interférer
   - Vérifiez dans `/auth/users/<id>/edit`

3. **Videz le cache** (si applicable) :
   - Redémarrez l'application
   - Videz le cache du navigateur

4. **Vérifiez les logs** :
   - Regardez les logs de l'application pour voir les erreurs exactes
   - Cherchez les messages "Accès refusé" dans les logs

## 📝 Notes

- Les permissions sont stockées en JSON dans la colonne `permissions` de la table `roles`
- Le format est différent entre MySQL (JSON_OBJECT) et PostgreSQL (JSONB)
- Les permissions sont vérifiées par la fonction `has_rh_permission()` dans `rh.py`

