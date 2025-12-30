# 🔐 DOCUMENTATION DES AUTORISATIONS - MODULE RH

**Date :** 2025-01-XX  
**Version :** 1.0

---

## 📋 RÔLES RH ET PERMISSIONS

### 1. **Admin** (`admin`)
- ✅ **Accès complet** à tous les modules (y compris RH)
- ✅ Peut tout faire sans restriction

---

### 2. **RH Manager** (`rh_manager`)
- ✅ **Accès complet** à tous les modules RH
- ✅ **Permissions :**
  - `users`: read, create, update, **delete**
  - `employees`: read, create, update, **delete**
  - `contracts`: read, create, update, **delete**
  - `trainings`: read, create, update, **delete**
  - `evaluations`: read, create, update, **delete**
  - `absences`: read, create, update, **delete**
  - `reports`: read, **export**
  - `analytics`: read, **export**

---

### 3. **RH Assistant** (`rh_assistant`)
- ✅ Saisie et modification des données
- ✅ Gestion des absences
- ❌ **Ne peut pas supprimer**
- ✅ **Permissions :**
  - `users`: read, create, update
  - `employees`: read, create, update
  - `contracts`: read, create, update
  - `trainings`: read, create, update
  - `evaluations`: read, create
  - `absences`: read, create, update
  - `reports`: read

---

### 4. **RH Recruiter** (`rh_recruiter`)
- ✅ Recrutement et intégration
- ✅ Création d'employés et contrats
- ✅ Formations d'intégration
- ❌ **Accès limité** aux autres modules
- ✅ **Permissions :**
  - `users`: read, create
  - `employees`: read, create, update
  - `contracts`: read, create
  - `trainings`: read, create
  - `reports`: read

---

### 5. **RH Analyst** (`rh_analyst`)
- ✅ **Consultation seule** (lecture)
- ✅ Rapports et exports
- ✅ Analytics
- ❌ **Ne peut pas créer/modifier**
- ✅ **Permissions :**
  - `users`: **read**
  - `employees`: **read**
  - `contracts`: **read**
  - `trainings`: **read**
  - `evaluations`: **read**
  - `absences`: **read**
  - `reports`: read, **export**
  - `analytics`: read, **export**

---

### 6. **RH** (`rh`) - Rôle de base
- ✅ Gestion des utilisateurs plateforme
- ✅ Consultation des rapports
- ✅ **Permissions :**
  - `users`: read, create, update
  - `employees`: **read**
  - `contracts`: **read**
  - `trainings`: **read**
  - `evaluations`: **read**
  - `absences`: **read**
  - `reports`: read
  - `analytics`: read

---

## 🔍 FONCTIONS DE VÉRIFICATION

### `has_rh_permission(user, permission)`
Vérifie si un utilisateur a une permission RH spécifique.

**Format de permission :** `module.action`
- Exemples : `employees.read`, `contracts.create`, `trainings.update`

**Logique :**
1. Admin → ✅ Toujours autorisé
2. RH Manager → ✅ Toujours autorisé pour les modules RH
3. Autres rôles RH → Vérifie les permissions dans `role.permissions`

**Exemple d'utilisation :**
```python
if not has_rh_permission(current_user, 'employees.create'):
    flash('Accès refusé', 'error')
    return redirect(url_for('rh.employees_list'))
```

---

### `is_rh_user(user)`
Vérifie si un utilisateur a un rôle RH (ou admin).

**Retourne :**
- `True` si l'utilisateur est admin ou a un rôle RH
- `False` sinon

**Exemple d'utilisation :**
```python
if not is_rh_user(current_user):
    flash('Accès refusé', 'error')
    return redirect(url_for('index'))
```

---

## 📊 MATRICE DES PERMISSIONS

| Module | Action | RH | RH Manager | RH Assistant | RH Recruiter | RH Analyst |
|--------|--------|----|----|----|----|----|
| **users** | read | ✅ | ✅ | ✅ | ✅ | ✅ |
| **users** | create | ✅ | ✅ | ✅ | ✅ | ❌ |
| **users** | update | ✅ | ✅ | ✅ | ❌ | ❌ |
| **users** | delete | ❌ | ✅ | ❌ | ❌ | ❌ |
| **employees** | read | ✅ | ✅ | ✅ | ✅ | ✅ |
| **employees** | create | ❌ | ✅ | ✅ | ✅ | ❌ |
| **employees** | update | ❌ | ✅ | ✅ | ✅ | ❌ |
| **employees** | delete | ❌ | ✅ | ❌ | ❌ | ❌ |
| **contracts** | read | ✅ | ✅ | ✅ | ✅ | ✅ |
| **contracts** | create | ❌ | ✅ | ✅ | ✅ | ❌ |
| **contracts** | update | ❌ | ✅ | ✅ | ❌ | ❌ |
| **contracts** | delete | ❌ | ✅ | ❌ | ❌ | ❌ |
| **trainings** | read | ✅ | ✅ | ✅ | ✅ | ✅ |
| **trainings** | create | ❌ | ✅ | ✅ | ✅ | ❌ |
| **trainings** | update | ❌ | ✅ | ✅ | ❌ | ❌ |
| **trainings** | delete | ❌ | ✅ | ❌ | ❌ | ❌ |
| **evaluations** | read | ✅ | ✅ | ✅ | ❌ | ✅ |
| **evaluations** | create | ❌ | ✅ | ✅ | ❌ | ❌ |
| **evaluations** | update | ❌ | ✅ | ❌ | ❌ | ❌ |
| **evaluations** | delete | ❌ | ✅ | ❌ | ❌ | ❌ |
| **absences** | read | ✅ | ✅ | ✅ | ❌ | ✅ |
| **absences** | create | ❌ | ✅ | ✅ | ❌ | ❌ |
| **absences** | update | ❌ | ✅ | ✅ | ❌ | ❌ |
| **absences** | delete | ❌ | ✅ | ❌ | ❌ | ❌ |
| **reports** | read | ✅ | ✅ | ✅ | ✅ | ✅ |
| **reports** | export | ❌ | ✅ | ❌ | ❌ | ✅ |
| **analytics** | read | ✅ | ✅ | ❌ | ❌ | ✅ |
| **analytics** | export | ❌ | ✅ | ❌ | ❌ | ✅ |

---

## 🔧 ROUTES ET PERMISSIONS

### Personnel Plateforme
- `/rh/personnel` → `users.read`
- `/rh/personnel/<id>` → `users.read`
- `/rh/personnel/new` → `users.create`
- `/rh/personnel/<id>/edit` → `users.update`

### Employés Externes
- `/rh/employees` → `employees.read`
- `/rh/employees/<id>` → `employees.read`
- `/rh/employees/new` → `employees.create`
- `/rh/employees/<id>/edit` → `employees.update`

### Contrats
- `/rh/employees/<id>/contracts` → `contracts.read`
- `/rh/employees/<id>/contracts/new` → `contracts.create`
- `/rh/contracts/<id>` → `contracts.read`
- `/rh/contracts/<id>/edit` → `contracts.update`

### Formations
- `/rh/employees/<id>/trainings` → `trainings.read`
- `/rh/employees/<id>/trainings/new` → `trainings.create`
- `/rh/trainings/<id>/edit` → `trainings.update`

### Évaluations
- `/rh/employees/<id>/evaluations` → `evaluations.read`
- `/rh/employees/<id>/evaluations/new` → `evaluations.create`
- `/rh/evaluations/<id>/edit` → `evaluations.update`

### Absences
- `/rh/employees/<id>/absences` → `absences.read`
- `/rh/employees/<id>/absences/new` → `absences.create`
- `/rh/absences/<id>/edit` → `absences.update`
- `/rh/absences/<id>/approve` → `absences.update`
- `/rh/absences/<id>/reject` → `absences.update`

### Suivi et Statistiques
- `/rh/activites` → `users.read`
- `/rh/statistiques` → `analytics.read`

---

## ✅ AMÉLIORATIONS APPORTÉES

1. ✅ **Harmonisation des vérifications**
   - Toutes les routes utilisent maintenant `has_rh_permission()` ou `is_rh_user()`
   - Suppression des vérifications redondantes

2. ✅ **Messages d'erreur améliorés**
   - Messages plus explicites pour les refus d'accès
   - Indication claire de la permission manquante

3. ✅ **Fonction `is_rh_user()` ajoutée**
   - Vérification simplifiée pour les accès généraux RH

4. ✅ **Permissions du rôle RH de base mises à jour**
   - Ajout des permissions de lecture pour employees, contracts, trainings, etc.

5. ✅ **Logique de vérification améliorée**
   - Support des permissions avec `*` (toutes les actions)
   - Vérification des permissions globales `all`

---

## 🧪 TEST DES PERMISSIONS

Pour tester les permissions :

1. **Créer des utilisateurs avec différents rôles RH**
2. **Se connecter avec chaque rôle**
3. **Tester l'accès aux différentes routes**
4. **Vérifier que les restrictions sont bien appliquées**

---

**Documentation mise à jour ! ✅**

