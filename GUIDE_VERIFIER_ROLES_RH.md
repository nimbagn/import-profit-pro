# 🔍 Guide : Vérifier les Rôles RH dans la Base de Données

**Date :** 2025-01-XX  
**Base de données :** PostgreSQL (Render)

---

## 🎯 Vérification Rapide

Pour vérifier si les rôles RH existent dans votre base de données sur Render :

### Méthode 1 : Via le Shell Render (Recommandé)

1. **Accédez au Shell Render** :
   - Dashboard Render → Service Web → **Shell**

2. **Exécutez le script de vérification** :
   ```bash
   python3 verifier_roles_rh.py
   ```

**Résultat attendu :**
```
======================================================================
🔍 VÉRIFICATION DES RÔLES RH
======================================================================

📋 RÔLES RH TROUVÉS DANS LA BASE DE DONNÉES:
----------------------------------------------------------------------
✅ RH Manager (rh_manager)
   Description: Gestion complète du personnel, contrats, formations, évaluations

✅ RH Assistant (rh_assistant)
   Description: Assistance RH : saisie données, suivi formations, gestion absences

✅ RH Recruiter (rh_recruiter)
   Description: Recrutement et intégration du personnel

✅ RH Analyst (rh_analyst)
   Description: Analyse et reporting RH, statistiques, tableaux de bord

✅ RH (rh)
   Description: Gestion des utilisateurs plateforme, consultation des rapports

======================================================================
📊 COMPARAISON AVEC LES RÔLES ATTENDUS
======================================================================

✅ RH Manager (rh_manager) - PRÉSENT
✅ RH Assistant (rh_assistant) - PRÉSENT
✅ RH Recruiter (rh_recruiter) - PRÉSENT
✅ RH Analyst (rh_analyst) - PRÉSENT
✅ RH (rh) - PRÉSENT

======================================================================
📈 RÉSUMÉ
======================================================================
Rôles présents: 5/5
Rôles manquants: 0/5

✅ Tous les rôles RH sont présents dans la base de données!
```

---

### Méthode 2 : Via une Requête SQL Directe

Dans le Shell Render :

```bash
python3 -c "
from app import app
from models import Role

with app.app_context():
    # Rôles RH attendus
    codes_rh = ['rh_manager', 'rh_assistant', 'rh_recruiter', 'rh_analyst', 'rh']
    
    print('📋 VÉRIFICATION DES RÔLES RH')
    print('=' * 60)
    print()
    
    for code in codes_rh:
        role = Role.query.filter_by(code=code).first()
        if role:
            print(f'✅ {role.name} ({code})')
        else:
            print(f'❌ {code} - MANQUANT')
    
    print()
    print('📊 TOUS LES RÔLES:')
    print('-' * 60)
    tous = Role.query.order_by(Role.code).all()
    for role in tous:
        est_rh = role.code.startswith('rh')
        prefixe = '🔹' if est_rh else '  '
        print(f'{prefixe} {role.name} ({role.code})')
"
```

---

## 📋 Rôles RH Attendus

Les 5 rôles RH suivants doivent exister :

| Code | Nom | Description |
|------|-----|-------------|
| `rh_manager` | RH Manager | Gestion complète du personnel, contrats, formations, évaluations |
| `rh_assistant` | RH Assistant | Assistance RH : saisie données, suivi formations, gestion absences |
| `rh_recruiter` | RH Recruiter | Recrutement et intégration du personnel |
| `rh_analyst` | RH Analyst | Analyse et reporting RH, statistiques, tableaux de bord |
| `rh` | RH | Gestion des utilisateurs plateforme, consultation des rapports |

---

## ⚠️ Si des Rôles Manquent

Si le script indique que des rôles sont manquants, vous pouvez les créer :

### Option 1 : Via l'Interface Web

1. **Connectez-vous** en tant qu'administrateur
2. Allez sur : **Auth** → **Rôles** → **Nouveau rôle**
   - URL : `/auth/roles/new`

3. **Créez chaque rôle manquant** avec les informations du tableau ci-dessus

### Option 2 : Via un Script SQL

Créez un fichier `create_roles_rh.sql` :

```sql
-- Créer les rôles RH s'ils n'existent pas
INSERT INTO roles (name, code, description, permissions, created_at, updated_at)
VALUES 
    ('RH Manager', 'rh_manager', 'Gestion complète du personnel, contrats, formations, évaluations', '{}', NOW(), NOW()),
    ('RH Assistant', 'rh_assistant', 'Assistance RH : saisie données, suivi formations, gestion absences', '{}', NOW(), NOW()),
    ('RH Recruiter', 'rh_recruiter', 'Recrutement et intégration du personnel', '{}', NOW(), NOW()),
    ('RH Analyst', 'rh_analyst', 'Analyse et reporting RH, statistiques, tableaux de bord', '{}', NOW(), NOW()),
    ('RH', 'rh', 'Gestion des utilisateurs plateforme, consultation des rapports', '{}', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

Puis exécutez-le dans le Shell Render :

```bash
python3 -c "
from app import app
from models import db

with app.app_context():
    with open('create_roles_rh.sql', 'r') as f:
        sql = f.read()
    db.session.execute(db.text(sql))
    db.session.commit()
    print('✅ Rôles RH créés')
"
```

---

## ✅ Vérification dans l'Interface

Vous pouvez aussi vérifier visuellement :

1. **Connectez-vous** en tant qu'administrateur
2. Allez sur : **Auth** → **Rôles**
   - URL : `/auth/roles`

3. **Cherchez les rôles** avec le code commençant par `rh` :
   - `rh_manager`
   - `rh_assistant`
   - `rh_recruiter`
   - `rh_analyst`
   - `rh`

---

## 🎯 Vérifier qu'un Utilisateur a un Rôle RH

Pour vérifier si un utilisateur spécifique a un rôle RH :

```bash
python3 -c "
from app import app
from models import User, Role

with app.app_context():
    username = 'nom_utilisateur'  # Remplacez par le nom d'utilisateur
    
    user = User.query.filter_by(username=username).first()
    if user:
        print(f'👤 Utilisateur: {user.username}')
        if user.role:
            est_rh = user.role.code.startswith('rh')
            print(f'   Rôle: {user.role.name} ({user.role.code})')
            if est_rh:
                print('   ✅ A un rôle RH')
            else:
                print('   ❌ N\'a pas de rôle RH')
        else:
            print('   ❌ Aucun rôle assigné')
    else:
        print(f'❌ Utilisateur {username} non trouvé')
"
```

---

## 📊 Liste Tous les Utilisateurs avec Rôles RH

Pour voir tous les utilisateurs qui ont un rôle RH :

```bash
python3 -c "
from app import app
from models import User

with app.app_context():
    users_rh = User.query.join(Role).filter(Role.code.like('rh%')).all()
    
    print(f'📋 Utilisateurs avec rôle RH: {len(users_rh)}')
    print('=' * 60)
    
    for user in users_rh:
        print(f'👤 {user.username} ({user.email})')
        print(f'   Rôle: {user.role.name} ({user.role.code})')
        print(f'   Actif: {\"✅\" if user.is_active else \"❌\"}')
        print()
"
```

---

## 🆘 Dépannage

### Problème : Le script ne peut pas se connecter à la base de données

**Solution :**
- Exécutez le script dans le Shell Render (pas en local)
- Vérifiez que `DATABASE_URL` est configurée dans Render Dashboard > Environment

### Problème : Aucun rôle RH trouvé

**Solution :**
- Créez les rôles manquants (voir section "Si des Rôles Manquent")
- Vérifiez que les codes des rôles sont exactement : `rh_manager`, `rh_assistant`, etc.

### Problème : Les rôles RH n'apparaissent pas dans le dropdown

**Solution :**
1. Vérifiez que les rôles existent (exécutez `verifier_roles_rh.py`)
2. Rafraîchissez la page
3. Vérifiez que vous avez les permissions pour voir les rôles

---

## ✅ Checklist

- [ ] Script `verifier_roles_rh.py` exécuté
- [ ] Tous les 5 rôles RH sont présents
- [ ] Les rôles ont les bons noms et codes
- [ ] Les utilisateurs peuvent être assignés aux rôles RH
- [ ] Les rôles RH apparaissent dans les dropdowns de sélection

---

**🎉 Une fois vérifié, vous pouvez assigner les rôles RH aux utilisateurs !**

