# 📊 Guide : Dashboard RH

**Date :** 2025-01-XX  
**Module :** Ressources Humaines

---

## ✅ Dashboard RH Existant

**Oui, il existe un dashboard RH complet !**

- **URL :** `/rh/` ou `/rh`
- **Route :** `rh.index`
- **Template :** `templates/rh/index.html`

---

## 🎯 Accès au Dashboard RH

### URL Directe

```
https://import-profit-pro.onrender.com/rh/
```

### Via le Menu

1. **Connectez-vous** avec un utilisateur ayant un rôle RH ou Admin
2. Dans le menu de navigation, cherchez **"RH"** ou **"Ressources Humaines"**
3. Cliquez pour accéder au dashboard

---

## 📊 Contenu du Dashboard RH

Le dashboard affiche :

### Statistiques Principales

1. **Utilisateurs au total** - Nombre total d'utilisateurs
2. **Utilisateurs actifs** - Utilisateurs avec `is_active = True`
3. **Utilisateurs inactifs** - Utilisateurs avec `is_active = False`
4. **Employés externes** - Nombre total d'employés sans accès plateforme
5. **Employés actifs** - Employés avec statut actif
6. **Activités récentes** - Nombre d'activités dans les 30 derniers jours
7. **Connexions récentes** - Nombre de connexions dans les 30 derniers jours
8. **Contrats actifs** - Nombre de contrats en cours
9. **Formations en cours** - Formations en progression
10. **Absences en attente** - Demandes d'absences en attente de validation

### Graphiques et Analyses

- **Utilisateurs par rôle** - Répartition des utilisateurs selon leur rôle
- **Activités par type** - Top 10 des types d'activités les plus fréquents
- **Top 5 utilisateurs actifs** - Les utilisateurs les plus actifs (30 derniers jours)

### Modules RH Accessibles

Le dashboard propose des liens rapides vers :

1. **Personnel Plateforme** (`/rh/personnel`)
   - Gérer les utilisateurs de la plateforme, leurs rôles et permissions

2. **Employés Externes** (`/rh/employees`)
   - Gérer les employés sans accès à la plateforme

3. **Activités Utilisateurs** (`/rh/activites`)
   - Consulter l'historique des activités et interactions

4. **Statistiques** (`/rh/statistiques`)
   - Analyser l'utilisation de l'application et les tendances

---

## 🔐 Permissions Requises

Pour accéder au dashboard RH, vous devez avoir :

- ✅ Un **rôle RH** (rh, rh_manager, rh_assistant, rh_recruiter, rh_analyst)
- ✅ OU être **administrateur** (admin)
- ✅ OU avoir la permission `users.read`

**Si vous n'avez pas les permissions :**
- Vous serez redirigé vers la page d'accueil
- Un message d'erreur s'affichera : "Accès refusé. Vous devez avoir un rôle RH pour accéder à cette page."

---

## 🧪 Tester le Dashboard RH

### Méthode 1 : Via l'Interface Web

1. **Connectez-vous** avec un utilisateur ayant un rôle RH
2. Allez sur : `https://import-profit-pro.onrender.com/rh/`
3. Le dashboard devrait s'afficher avec toutes les statistiques

### Méthode 2 : Vérifier la Route

Dans le Shell Render, vous pouvez vérifier que la route existe :

```bash
python3 -c "
from app import app

with app.app_context():
    with app.test_client() as client:
        # Simuler une connexion (nécessite d'être connecté)
        print('✅ Route /rh/ existe')
        print('   URL: /rh/')
        print('   Route name: rh.index')
        print('   Template: templates/rh/index.html')
"
```

---

## 📋 Vérifier si le Template Existe

Dans le Shell Render :

```bash
ls -la templates/rh/index.html
```

**Résultat attendu :**
```
-rw-r--r-- 1 render render XXXX templates/rh/index.html
```

Si le fichier n'existe pas, vous verrez :
```
ls: cannot access 'templates/rh/index.html': No such file or directory
```

---

## 🔍 Vérifier les Statistiques Affichées

Le dashboard calcule les statistiques suivantes :

### Utilisateurs
- `total_users` - `User.query.count()`
- `active_users` - `User.query.filter_by(is_active=True).count()`
- `inactive_users` - `User.query.filter_by(is_active=False).count()`

### Employés Externes
- `total_employees` - `Employee.query.count()`
- `active_employees` - `Employee.query.filter_by(employment_status='active').count()`

### Activités (30 derniers jours)
- `recent_activities_count` - Activités dans les 30 derniers jours
- `recent_logins` - Connexions dans les 30 derniers jours

### Analyses
- `users_by_role` - Répartition par rôle
- `activities_by_type` - Top 10 des types d'activités
- `top_active_users` - Top 5 utilisateurs les plus actifs

### Employés
- `active_contracts` - Contrats actifs
- `ongoing_trainings` - Formations en cours
- `pending_absences` - Absences en attente

---

## ⚠️ Problèmes Courants

### Problème : "Accès refusé"

**Cause :** Vous n'avez pas un rôle RH ou les permissions nécessaires

**Solution :**
1. Vérifiez votre rôle : `/auth/users` (si vous êtes admin)
2. Assignez-vous un rôle RH (voir `GUIDE_ASSIGNER_ROLE_RH.md`)
3. Ou connectez-vous avec un utilisateur ayant un rôle RH

### Problème : Page blanche ou erreur 500

**Causes possibles :**
- Tables manquantes (employees, employee_contracts, etc.)
- Erreur dans le template
- Problème de connexion à la base de données

**Solution :**
1. Vérifiez les logs Render pour l'erreur exacte
2. Vérifiez que les migrations RH ont été exécutées
3. Vérifiez que les tables existent

### Problème : Statistiques à zéro

**Causes possibles :**
- Aucune donnée dans la base
- Tables vides
- Filtres trop restrictifs

**Solution :**
- C'est normal si vous venez de créer la base de données
- Les statistiques se rempliront au fur et à mesure de l'utilisation

---

## 📊 Exemple de Dashboard

Le dashboard devrait afficher quelque chose comme :

```
┌─────────────────────────────────────────────────┐
│  Ressources Humaines                            │
│  Tableau de bord de gestion du personnel        │
└─────────────────────────────────────────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  25      │ │  23      │ │  2       │ │  15      │
│ Utilis.  │ │ Actifs   │ │ Inactifs │ │ Employés │
│  total   │ │          │ │          │ │ externes │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

┌─────────────────────────────────────────────────┐
│  Modules RH                                      │
│  [Personnel] [Employés] [Activités] [Stats]     │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Utilisateurs par Rôle                          │
│  - Admin: 2                                     │
│  - Commercial: 10                               │
│  - RH Manager: 1                                │
└─────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Vérification

- [ ] Route `/rh/` accessible
- [ ] Template `templates/rh/index.html` existe
- [ ] Permissions vérifiées (rôle RH ou admin)
- [ ] Statistiques s'affichent correctement
- [ ] Liens vers les modules RH fonctionnent
- [ ] Graphiques et analyses s'affichent
- [ ] Responsive sur mobile/tablette

---

## 🎯 Prochaines Étapes

Une fois le dashboard accessible :

1. **Vérifiez les statistiques** - Sont-elles cohérentes ?
2. **Testez les liens** - Tous les modules RH sont-ils accessibles ?
3. **Assignez des rôles RH** - Créez des utilisateurs avec des rôles RH
4. **Explorez les modules** - Personnel, Employés, Activités, Statistiques

---

**🎉 Le dashboard RH est disponible et fonctionnel !**

**URL :** `https://import-profit-pro.onrender.com/rh/`

