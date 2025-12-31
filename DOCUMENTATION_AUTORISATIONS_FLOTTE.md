# 🔐 Documentation des Autorisations - Module Flotte

**Date :** 2025-01-XX  
**Statut :** ✅ **RÉVISÉ ET SÉCURISÉ**

---

## 📋 Vue d'Ensemble

Le module flotte gère les véhicules, leurs documents, maintenances, odomètres et assignations. Toutes les routes sont protégées et vérifient les permissions appropriées.

---

## 🔒 Routes et Permissions

### Dashboard et Navigation

| Route | Permission | Description |
|-------|------------|-------------|
| `/vehicles/operations-guide` | `vehicles.read` | Guide des opérations véhicules |
| `/vehicles/dashboard` | `vehicles.read` | Dashboard avec statistiques et alertes |

### Documents Véhicule

| Route | Permission | Vérification Région | Description |
|-------|------------|---------------------|-------------|
| `/vehicles/<id>/documents` | `vehicles.read` | ✅ `can_access_vehicle()` | Liste des documents |
| `/vehicles/<id>/documents/new` | `vehicles.update` | ✅ `can_access_vehicle()` | Créer un document |
| `/vehicles/<id>/documents/<doc_id>/edit` | `vehicles.update` | ✅ `can_access_vehicle()` | Modifier un document |

### Maintenances Véhicule

| Route | Permission | Vérification Région | Description |
|-------|------------|---------------------|-------------|
| `/vehicles/<id>/maintenances` | `vehicles.read` | ✅ `can_access_vehicle()` | Liste des maintenances |
| `/vehicles/<id>/maintenances/new` | `vehicles.update` | ✅ `can_access_vehicle()` | Planifier une maintenance |
| `/vehicles/<id>/maintenances/<maint_id>/complete` | `vehicles.update` | ✅ `can_access_vehicle()` | Marquer comme réalisée |

### Odomètre Véhicule

| Route | Permission | Vérification Région | Description |
|-------|------------|---------------------|-------------|
| `/vehicles/<id>/odometer` | `vehicles.read` | ✅ `can_access_vehicle()` | Historique des relevés |
| `/vehicles/<id>/odometer/new` | `vehicles.update` | ✅ `can_access_vehicle()` | Ajouter un relevé |

### Fiche Véhicule

| Route | Permission | Vérification Région | Description |
|-------|------------|---------------------|-------------|
| `/vehicles/<id>` | `vehicles.read` | ✅ `can_access_vehicle()` | Fiche complète du véhicule |

### Assignations Véhicule

| Route | Permission | Vérification Région | Description |
|-------|------------|---------------------|-------------|
| `/vehicles/<id>/assignments` | `vehicles.read` | ✅ `can_access_vehicle()` | Historique des assignations |
| `/vehicles/<id>/assignments/new` | `vehicles.update` | ✅ `can_access_vehicle()` | Créer une assignation |
| `/vehicles/<id>/assignments/<assignment_id>/end` | `vehicles.update` | ✅ `can_access_vehicle()` | Terminer une assignation |

### Véhicules par Utilisateur

| Route | Permission | Vérification Région | Description |
|-------|------------|---------------------|-------------|
| `/vehicles/users/<user_id>/vehicles` | `vehicles.read` | ❌ (à vérifier) | Véhicules assignés à un utilisateur |

---

## ✅ Sécurité Implémentée

### 1. **Protection par Authentification**
- ✅ Toutes les routes utilisent `@login_required`
- ✅ Aucune route publique

### 2. **Vérification des Permissions**
- ✅ `vehicles.read` pour toutes les consultations
- ✅ `vehicles.update` pour toutes les modifications
- ✅ Messages d'erreur explicites

### 3. **Filtrage par Région**
- ✅ Dashboard : Filtrage automatique par région
- ✅ Routes spécifiques : Vérification `can_access_vehicle(vehicle_id)`
- ✅ Les admins voient tous les véhicules

### 4. **Fonction `can_access_vehicle()`**
```python
def can_access_vehicle(vehicle_id):
    """
    Vérifie si l'utilisateur connecté peut accéder à un véhicule spécifique
    Les admins peuvent accéder à tous les véhicules
    """
    # Admin → ✅ Accès autorisé
    # Autres utilisateurs → Vérifie que le conducteur du véhicule est dans leur région
```

---

## 🔍 Routes avec Vérification Région

Toutes les routes suivantes vérifient maintenant l'accès au véhicule :

1. ✅ `/vehicles/<id>/documents`
2. ✅ `/vehicles/<id>/documents/new`
3. ✅ `/vehicles/<id>/documents/<doc_id>/edit`
4. ✅ `/vehicles/<id>/maintenances`
5. ✅ `/vehicles/<id>/maintenances/new`
6. ✅ `/vehicles/<id>/maintenances/<maint_id>/complete`
7. ✅ `/vehicles/<id>/odometer`
8. ✅ `/vehicles/<id>/odometer/new`
9. ✅ `/vehicles/<id>`
10. ✅ `/vehicles/<id>/assignments`
11. ✅ `/vehicles/<id>/assignments/new`
12. ✅ `/vehicles/<id>/assignments/<assignment_id>/end`

---

## ⚠️ Points d'Attention

### Route `/vehicles/users/<user_id>/vehicles`

Cette route affiche les véhicules assignés à un utilisateur. Elle devrait peut-être vérifier :
- Que l'utilisateur demandé appartient à la même région (sauf admin)
- Ou que l'utilisateur connecté peut voir les véhicules de cet utilisateur

**Recommandation :** Ajouter une vérification si nécessaire selon les besoins métier.

---

## 📊 Matrice des Permissions

| Action | Permission Requise | Admin | Superviseur | Commercial | Autres |
|--------|-------------------|-------|-------------|-------------|--------|
| Voir dashboard | `vehicles.read` | ✅ | ✅ | ✅ | ❌ |
| Voir véhicule | `vehicles.read` | ✅ | ✅ | ✅ | ❌ |
| Voir documents | `vehicles.read` | ✅ | ✅ | ✅ | ❌ |
| Voir maintenances | `vehicles.read` | ✅ | ✅ | ✅ | ❌ |
| Voir odomètre | `vehicles.read` | ✅ | ✅ | ✅ | ❌ |
| Créer document | `vehicles.update` | ✅ | ✅ | ❌ | ❌ |
| Modifier document | `vehicles.update` | ✅ | ✅ | ❌ | ❌ |
| Planifier maintenance | `vehicles.update` | ✅ | ✅ | ❌ | ❌ |
| Ajouter relevé odomètre | `vehicles.update` | ✅ | ✅ | ❌ | ❌ |
| Créer assignation | `vehicles.update` | ✅ | ✅ | ❌ | ❌ |

---

## 🎯 Règles de Sécurité

### Règle 1 : Admin a Tous les Droits
- ✅ L'admin passe toutes les vérifications de permissions
- ✅ L'admin voit tous les véhicules (pas de filtre par région)
- ✅ L'admin peut accéder à tous les véhicules via `can_access_vehicle()`

### Règle 2 : Filtrage par Région
- ✅ Les utilisateurs non-admin voient uniquement les véhicules de leur région
- ✅ Un véhicule appartient à une région via son conducteur (`vehicle.current_user.region_id`)
- ✅ Les véhicules sans conducteur ne sont pas accessibles aux utilisateurs non-admin

### Règle 3 : Vérification d'Accès
- ✅ Toutes les routes avec `vehicle_id` vérifient `can_access_vehicle()`
- ✅ Message d'erreur clair : "Vous n'avez pas accès à ce véhicule"
- ✅ Redirection vers l'index en cas d'accès refusé

---

## 🔧 Améliorations Apportées

### 1. **Ajout Vérifications Région**
- ✅ Toutes les routes avec `vehicle_id` vérifient maintenant `can_access_vehicle()`
- ✅ Protection contre l'accès non autorisé aux véhicules d'autres régions

### 2. **Filtrage Dashboard**
- ✅ Dashboard filtre automatiquement par région
- ✅ Statistiques, alertes et listes respectent le filtrage

### 3. **Cohérence des Permissions**
- ✅ Toutes les consultations utilisent `vehicles.read`
- ✅ Toutes les modifications utilisent `vehicles.update`
- ✅ Messages d'erreur cohérents

---

## 📝 Résumé

| Aspect | Statut |
|--------|--------|
| Routes protégées | ✅ Toutes |
| Vérifications permissions | ✅ Toutes |
| Vérifications région | ✅ Toutes (sauf `/users/<id>/vehicles`) |
| Filtrage dashboard | ✅ Implémenté |
| Messages d'erreur | ✅ Clairs et explicites |
| Admin tous droits | ✅ Confirmé |

---

## ✅ Conclusion

Le module flotte est maintenant **sécurisé** avec :
- ✅ Toutes les routes protégées
- ✅ Vérifications de permissions appropriées
- ✅ Filtrage par région pour les utilisateurs non-admin
- ✅ Vérification d'accès aux véhicules spécifiques
- ✅ Admin a accès à tous les véhicules

**Aucune route n'est accessible sans authentification et toutes les routes vérifient les permissions appropriées.**

