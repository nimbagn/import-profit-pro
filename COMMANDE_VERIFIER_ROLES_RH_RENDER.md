# 🔍 Commande pour Vérifier les Rôles RH sur Render

**Pour exécuter directement dans le Shell Render**

---

## ✅ Commande Rapide

Copiez-collez cette commande dans le Shell Render :

```bash
python3 -c "
from app import app
from models import Role

with app.app_context():
    # Rôles RH attendus
    codes_rh = {
        'rh_manager': 'RH Manager',
        'rh_assistant': 'RH Assistant',
        'rh_recruiter': 'RH Recruiter',
        'rh_analyst': 'RH Analyst',
        'rh': 'RH'
    }
    
    print('=' * 70)
    print('🔍 VÉRIFICATION DES RÔLES RH')
    print('=' * 70)
    print()
    
    roles_presents = []
    roles_manquants = []
    
    for code, nom in codes_rh.items():
        role = Role.query.filter_by(code=code).first()
        if role:
            roles_presents.append(code)
            print(f'✅ {role.name} ({code})')
            if role.description:
                print(f'   Description: {role.description}')
        else:
            roles_manquants.append(code)
            print(f'❌ {nom} ({code}) - MANQUANT')
        print()
    
    print('=' * 70)
    print('📊 RÉSUMÉ')
    print('=' * 70)
    print(f'Rôles présents: {len(roles_presents)}/5')
    print(f'Rôles manquants: {len(roles_manquants)}/5')
    print()
    
    if roles_manquants:
        print('⚠️  RÔLES MANQUANTS:')
        for code in roles_manquants:
            print(f'   - {codes_rh[code]} ({code})')
    else:
        print('✅ Tous les rôles RH sont présents!')
    
    print()
    print('=' * 70)
    print('📋 TOUS LES RÔLES DANS LA BASE DE DONNÉES')
    print('=' * 70)
    print()
    
    tous_les_roles = Role.query.order_by(Role.code).all()
    if tous_les_roles:
        print(f'Total: {len(tous_les_roles)} rôle(s)')
        print()
        for role in tous_les_roles:
            est_rh = role.code.startswith('rh')
            prefixe = '🔹' if est_rh else '  '
            print(f'{prefixe} {role.name} ({role.code})')
    else:
        print('❌ Aucun rôle trouvé')
"
```

---

## 📋 Version Simplifiée (Juste la Liste)

Si vous voulez juste voir rapidement les rôles RH :

```bash
python3 -c "
from app import app
from models import Role

with app.app_context():
    roles_rh = Role.query.filter(Role.code.like('rh%')).all()
    print('📋 Rôles RH disponibles:')
    if roles_rh:
        for role in roles_rh:
            print(f'   ✅ {role.name} ({role.code})')
    else:
        print('   ❌ Aucun rôle RH trouvé')
"
```

---

## 🔍 Vérifier un Rôle Spécifique

Pour vérifier un rôle spécifique :

```bash
python3 -c "
from app import app
from models import Role

with app.app_context():
    code = 'rh_manager'  # Changez le code si nécessaire
    role = Role.query.filter_by(code=code).first()
    
    if role:
        print(f'✅ Rôle trouvé: {role.name} ({role.code})')
        if role.description:
            print(f'   Description: {role.description}')
    else:
        print(f'❌ Rôle {code} non trouvé')
"
```

---

## 👥 Vérifier les Utilisateurs avec Rôles RH

Pour voir tous les utilisateurs qui ont un rôle RH :

```bash
python3 -c "
from app import app
from models import User, Role

with app.app_context():
    users_rh = User.query.join(Role).filter(Role.code.like('rh%')).all()
    
    print(f'📋 Utilisateurs avec rôle RH: {len(users_rh)}')
    print('=' * 60)
    
    if users_rh:
        for user in users_rh:
            print(f'👤 {user.username} ({user.email})')
            print(f'   Rôle: {user.role.name} ({user.role.code})')
            print(f'   Actif: {\"✅\" if user.is_active else \"❌\"}')
            print()
    else:
        print('   Aucun utilisateur avec rôle RH trouvé')
"
```

---

**💡 Astuce :** Copiez-collez directement la commande dans le Shell Render pour vérifier les rôles RH !

