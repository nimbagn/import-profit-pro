# 🔧 Commande pour Créer les Rôles RH sur Render

**Pour exécuter directement dans le Shell Render**

---

## ✅ Commande Rapide (Créer Tous les Rôles RH)

Copiez-collez cette commande dans le Shell Render :

```bash
python3 -c "
from app import app
from models import db, Role
from datetime import datetime, UTC
import json

with app.app_context():
    roles_rh = [
        {
            'name': 'RH Manager',
            'code': 'rh_manager',
            'description': 'Gestion complète du personnel, contrats, formations, évaluations',
            'permissions': {
                'users': ['read', 'create', 'update', 'delete'],
                'employees': ['read', 'create', 'update', 'delete'],
                'contracts': ['read', 'create', 'update', 'delete'],
                'trainings': ['read', 'create', 'update', 'delete'],
                'evaluations': ['read', 'create', 'update', 'delete'],
                'absences': ['read', 'create', 'update', 'delete'],
                'reports': ['read', 'export'],
                'analytics': ['read', 'export']
            }
        },
        {
            'name': 'RH Assistant',
            'code': 'rh_assistant',
            'description': 'Assistance RH : saisie données, suivi formations, gestion absences',
            'permissions': {
                'users': ['read', 'create', 'update'],
                'employees': ['read', 'create', 'update'],
                'contracts': ['read', 'create', 'update'],
                'trainings': ['read', 'create', 'update'],
                'evaluations': ['read', 'create'],
                'absences': ['read', 'create', 'update', 'delete'],
                'reports': ['read']
            }
        },
        {
            'name': 'RH Recruiter',
            'code': 'rh_recruiter',
            'description': 'Recrutement et intégration du personnel',
            'permissions': {
                'users': ['read', 'create'],
                'employees': ['read', 'create', 'update'],
                'contracts': ['read', 'create'],
                'trainings': ['read', 'create'],
                'reports': ['read']
            }
        },
        {
            'name': 'RH Analyst',
            'code': 'rh_analyst',
            'description': 'Analyse et reporting RH, statistiques, tableaux de bord',
            'permissions': {
                'users': ['read'],
                'employees': ['read'],
                'contracts': ['read'],
                'trainings': ['read'],
                'evaluations': ['read'],
                'absences': ['read'],
                'reports': ['read', 'export'],
                'analytics': ['read', 'export']
            }
        },
        {
            'name': 'RH',
            'code': 'rh',
            'description': 'Gestion des utilisateurs plateforme, consultation des rapports',
            'permissions': {
                'users': ['read', 'create', 'update'],
                'reports': ['read']
            }
        }
    ]
    
    print('=' * 70)
    print('🔧 CRÉATION DES RÔLES RH')
    print('=' * 70)
    print()
    
    roles_crees = []
    roles_existants = []
    
    for role_data in roles_rh:
        role_existant = Role.query.filter_by(code=role_data['code']).first()
        
        if role_existant:
            roles_existants.append(role_data['code'])
            print(f'⚠️  {role_data[\"name\"]} ({role_data[\"code\"]}) existe déjà')
        else:
            try:
                new_role = Role(
                    name=role_data['name'],
                    code=role_data['code'],
                    description=role_data['description'],
                    permissions=json.dumps(role_data['permissions']),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                db.session.add(new_role)
                roles_crees.append(role_data['code'])
                print(f'✅ {role_data[\"name\"]} ({role_data[\"code\"]}) créé')
            except Exception as e:
                print(f'❌ Erreur pour {role_data[\"code\"]}: {e}')
                db.session.rollback()
    
    try:
        db.session.commit()
        print()
        print('=' * 70)
        print('📊 RÉSUMÉ')
        print('=' * 70)
        print(f'✅ Rôles créés: {len(roles_crees)}')
        print(f'⚠️  Rôles existants: {len(roles_existants)}')
        print()
        
        # Vérification finale
        tous_les_roles_rh = Role.query.filter(Role.code.like('rh%')).all()
        print(f'📋 Rôles RH dans la base: {len(tous_les_roles_rh)}/5')
        
        if len(tous_les_roles_rh) == 5:
            print()
            print('🎉 Tous les rôles RH ont été créés avec succès!')
        else:
            print()
            print(f'⚠️  {5 - len(tous_les_roles_rh)} rôle(s) manquant(s)')
    except Exception as e:
        print(f'❌ Erreur lors du commit: {e}')
        db.session.rollback()
"
```

---

## 📋 Alternative : Utiliser le Script (si disponible)

Si le fichier `create_roles_rh.py` est disponible sur Render :

```bash
python3 create_roles_rh.py
```

---

## ✅ Vérification Après Création

Après avoir créé les rôles, vérifiez qu'ils sont bien présents :

```bash
python3 -c "
from app import app
from models import Role

with app.app_context():
    roles_rh = Role.query.filter(Role.code.like('rh%')).all()
    print('📋 Rôles RH disponibles:')
    if roles_rh:
        for role in sorted(roles_rh, key=lambda x: x.code):
            print(f'   ✅ {role.name} ({role.code})')
    else:
        print('   ❌ Aucun rôle RH trouvé')
"
```

---

**💡 Astuce :** Copiez-collez la commande de création dans le Shell Render pour créer automatiquement tous les rôles RH !

