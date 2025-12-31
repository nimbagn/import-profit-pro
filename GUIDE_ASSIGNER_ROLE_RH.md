# 👥 Guide : Assigner un Rôle RH à un Utilisateur

**Date :** 2025-01-XX  
**Module :** Ressources Humaines

---

## 📋 Vue d'Ensemble

Il existe **5 rôles RH** différents que vous pouvez assigner aux utilisateurs :

1. **RH Manager** (`rh_manager`) - Gestion complète
2. **RH Assistant** (`rh_assistant`) - Saisie et modification
3. **RH Recruiter** (`rh_recruiter`) - Recrutement
4. **RH Analyst** (`rh_analyst`) - Consultation et rapports
5. **RH** (`rh`) - Rôle de base

---

## 🎯 Méthode 1 : Lors de la Création d'un Utilisateur

### Via le Module Auth (Recommandé pour les Admins)

1. **Connectez-vous** en tant qu'administrateur
2. Allez sur : **Utilisateurs** → **Créer un utilisateur**
   - URL : `/auth/register`
   - Ou via le menu : **Auth** → **Créer un utilisateur**

3. **Remplissez le formulaire** :
   - Nom d'utilisateur
   - Email
   - Mot de passe
   - **Rôle** : Sélectionnez un rôle RH dans le dropdown
     - Cherchez les rôles avec le code : `rh_manager`, `rh_assistant`, `rh_recruiter`, `rh_analyst`, ou `rh`
   - Nom complet
   - Téléphone (optionnel)
   - Région (optionnel)

4. **Cliquez sur "Créer l'Utilisateur"**

---

### Via le Module RH

1. **Connectez-vous** avec un rôle RH ou Admin
2. Allez sur : **RH** → **Personnel** → **Nouveau**
   - URL : `/rh/personnel/new`

3. **Remplissez le formulaire** :
   - Nom d'utilisateur
   - Email
   - Mot de passe
   - **Rôle** : Sélectionnez un rôle RH dans le dropdown
   - Nom complet
   - Téléphone
   - Région

4. **Cliquez sur "Enregistrer"**

---

## 🔄 Méthode 2 : Modifier le Rôle d'un Utilisateur Existant

### Via le Module Auth

1. **Connectez-vous** en tant qu'administrateur
2. Allez sur : **Utilisateurs** → **Liste des utilisateurs**
   - URL : `/auth/users`

3. **Trouvez l'utilisateur** dans la liste
4. **Cliquez sur "Modifier"** ou sur le nom de l'utilisateur
   - URL : `/auth/users/<id>/edit`

5. **Modifiez le champ "Rôle"** :
   - Sélectionnez un nouveau rôle RH dans le dropdown
   - Les rôles RH sont identifiables par leur code :
     - `rh_manager` - RH Manager
     - `rh_assistant` - RH Assistant
     - `rh_recruiter` - RH Recruiter
     - `rh_analyst` - RH Analyst
     - `rh` - RH (base)

6. **Cliquez sur "Enregistrer"**

---

### Via le Module RH

1. **Connectez-vous** avec un rôle RH ou Admin
2. Allez sur : **RH** → **Personnel**
   - URL : `/rh/personnel`

3. **Trouvez l'utilisateur** dans la liste
4. **Cliquez sur "Modifier"** ou sur le nom de l'utilisateur
   - URL : `/rh/personnel/<id>/edit`

5. **Modifiez le champ "Rôle"** :
   - Sélectionnez un nouveau rôle RH dans le dropdown

6. **Cliquez sur "Enregistrer"**

---

## 📊 Codes des Rôles RH

Dans le dropdown de sélection des rôles, vous verrez le format suivant :
```
Nom du Rôle (code)
```

**Exemples :**
- `RH Manager (rh_manager)`
- `RH Assistant (rh_assistant)`
- `RH Recruiter (rh_recruiter)`
- `RH Analyst (rh_analyst)`
- `RH (rh)`

---

## 🔍 Comment Identifier les Rôles RH dans le Dropdown

Les rôles RH sont facilement identifiables car :
- Leur **nom** commence par "RH" (ex: "RH Manager", "RH Assistant")
- Leur **code** commence par "rh" (ex: `rh_manager`, `rh_assistant`)

**Astuce :** Si vous ne voyez pas les rôles RH dans le dropdown, c'est qu'ils n'ont peut-être pas encore été créés dans la base de données. Voir la section "Vérifier les Rôles RH" ci-dessous.

---

## ✅ Vérifier les Rôles RH Disponibles

### Via l'Interface Web

1. Allez sur : **Auth** → **Rôles**
   - URL : `/auth/roles`

2. **Cherchez les rôles** avec le code commençant par `rh` :
   - `rh_manager`
   - `rh_assistant`
   - `rh_recruiter`
   - `rh_analyst`
   - `rh`

### Via le Shell Render (Base de Données)

```bash
python3 -c "
from app import app
from models import Role

with app.app_context():
    rh_roles = Role.query.filter(Role.code.like('rh%')).all()
    print('📋 Rôles RH disponibles:')
    for role in rh_roles:
        print(f'   - {role.name} ({role.code})')
    
    if not rh_roles:
        print('❌ Aucun rôle RH trouvé')
        print('   → Les rôles RH doivent être créés dans la base de données')
"
```

---

## 🆕 Créer les Rôles RH (si ils n'existent pas)

Si les rôles RH n'existent pas encore, vous pouvez les créer :

### Via l'Interface Web

1. Allez sur : **Auth** → **Rôles** → **Nouveau rôle**
   - URL : `/auth/roles/new`

2. **Créez chaque rôle RH** avec les informations suivantes :

#### RH Manager
- **Nom :** `RH Manager`
- **Code :** `rh_manager`
- **Description :** `Gestion complète du personnel, contrats, formations, évaluations`

#### RH Assistant
- **Nom :** `RH Assistant`
- **Code :** `rh_assistant`
- **Description :** `Assistance RH : saisie données, suivi formations, gestion absences`

#### RH Recruiter
- **Nom :** `RH Recruiter`
- **Code :** `rh_recruiter`
- **Description :** `Recrutement et intégration du personnel`

#### RH Analyst
- **Nom :** `RH Analyst`
- **Code :** `rh_analyst`
- **Description :** `Analyse et reporting RH, statistiques, tableaux de bord`

#### RH (Base)
- **Nom :** `RH`
- **Code :** `rh`
- **Description :** `Gestion des utilisateurs plateforme, consultation des rapports`

3. **Configurez les permissions** pour chaque rôle selon vos besoins

---

## 🔐 Permissions par Rôle RH

### RH Manager (`rh_manager`)
- ✅ Accès complet à tous les modules RH
- ✅ CRUD complet (Create, Read, Update, Delete) sur tout
- ✅ Rapports et exports

### RH Assistant (`rh_assistant`)
- ✅ Création et modification
- ✅ Gestion des absences
- ❌ Pas de suppression

### RH Recruiter (`rh_recruiter`)
- ✅ Création d'employés et contrats
- ✅ Formations d'intégration
- ❌ Accès limité aux autres modules

### RH Analyst (`rh_analyst`)
- ✅ Consultation seule (lecture)
- ✅ Rapports et exports
- ❌ Pas de création/modification

### RH (`rh`)
- ✅ Gestion des utilisateurs plateforme
- ✅ Consultation des rapports

---

## 📝 Exemple Pratique

### Scénario : Assigner le rôle RH Manager à un nouvel utilisateur

1. **Connectez-vous** en tant qu'admin
2. Allez sur `/auth/register`
3. Remplissez :
   - Username: `rh_manager1`
   - Email: `rh.manager@example.com`
   - Password: `MotDePasse123!`
   - **Rôle :** Sélectionnez `RH Manager (rh_manager)` dans le dropdown
   - Full Name: `Jean Dupont`
   - Phone: `+1234567890`
   - Région: (optionnel)

4. Cliquez sur **"Créer l'Utilisateur"**

5. ✅ L'utilisateur a maintenant le rôle RH Manager et peut accéder à tous les modules RH

---

## ⚠️ Notes Importantes

- **Seuls les administrateurs** peuvent créer/modifier des utilisateurs via `/auth/register` et `/auth/users`
- **Les utilisateurs avec des rôles RH** peuvent créer/modifier des utilisateurs via `/rh/personnel`
- **Un utilisateur ne peut pas modifier son propre rôle** (sauf admin)
- **Un utilisateur non-admin ne peut pas modifier un admin**

---

## 🆘 Dépannage

### Problème : Les rôles RH n'apparaissent pas dans le dropdown

**Solution :**
1. Vérifiez que les rôles RH existent dans la base de données (voir section "Vérifier les Rôles RH")
2. Si ils n'existent pas, créez-les (voir section "Créer les Rôles RH")
3. Rafraîchissez la page

### Problème : Je ne peux pas modifier le rôle d'un utilisateur

**Vérifiez :**
- Vous êtes connecté en tant qu'administrateur
- L'utilisateur que vous essayez de modifier n'est pas un admin (sauf si vous êtes admin)
- Vous avez les permissions nécessaires (`users.update`)

### Problème : L'utilisateur avec un rôle RH ne peut pas accéder au module RH

**Vérifiez :**
- Le rôle a bien été assigné (vérifiez dans `/auth/users/<id>`)
- Le code du rôle est correct (`rh_manager`, `rh_assistant`, etc.)
- L'utilisateur est actif (`is_active = True`)

---

## ✅ Checklist

Avant d'assigner un rôle RH :

- [ ] Les rôles RH existent dans la base de données
- [ ] Vous avez les permissions pour créer/modifier des utilisateurs
- [ ] Vous connaissez le code du rôle à assigner
- [ ] L'utilisateur cible est identifié

Après avoir assigné le rôle :

- [ ] Vérifiez que le rôle est bien assigné dans la liste des utilisateurs
- [ ] Testez l'accès au module RH avec le nouvel utilisateur
- [ ] Vérifiez que les permissions fonctionnent correctement

---

**🎉 Vous savez maintenant comment assigner un rôle RH à un utilisateur !**

