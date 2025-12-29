# Guide de Filtrage Automatique par Région

## 📋 Vue d'ensemble

Le système de filtrage automatique par région permet à chaque utilisateur de voir uniquement les données de sa région (stock, véhicules, équipes, membres). Les administrateurs voient toutes les données sans restriction.

---

## 🔧 Fonctionnement

### Principe

- **Utilisateurs normaux** : Voient uniquement les données de leur région
- **Administrateurs** : Voient toutes les données (pas de filtre)

### Associations par Région

1. **Dépôts** → Associés directement à une région (`depot.region_id`)
2. **Véhicules** → Associés à une région via leur conducteur (`vehicle.current_user.region_id`)
3. **Équipes de promotion** → Associées à une région via leur responsable (`team.team_leader.region_id`)
4. **Membres de promotion** → Associés à une région via leur équipe (`member.team.team_leader.region_id`)
5. **Stocks de dépôt** → Associés à une région via le dépôt (`depot_stock.depot.region_id`)
6. **Stocks de véhicule** → Associés à une région via le véhicule (`vehicle_stock.vehicle.current_user.region_id`)
7. **Mouvements de stock** → Associés à une région via les dépôts source/destination

---

## 📁 Fichier Utilitaire

### `utils_region_filter.py`

Ce fichier contient toutes les fonctions de filtrage :

#### Fonctions principales :

1. **`get_user_region_id()`**
   - Retourne l'ID de la région de l'utilisateur connecté
   - Retourne `None` pour les admins (pas de filtre)

2. **`filter_depots_by_region(query)`**
   - Filtre les dépôts selon la région de l'utilisateur

3. **`filter_vehicles_by_region(query)`**
   - Filtre les véhicules selon la région du conducteur

4. **`filter_teams_by_region(query)`**
   - Filtre les équipes selon la région du responsable

5. **`filter_members_by_region(query)`**
   - Filtre les membres selon la région de leur équipe

6. **`filter_depot_stocks_by_region(query)`**
   - Filtre les stocks de dépôt selon la région

7. **`filter_vehicle_stocks_by_region(query)`**
   - Filtre les stocks de véhicule selon la région

8. **`can_access_depot(depot_id)`**
   - Vérifie si l'utilisateur peut accéder à un dépôt

9. **`can_access_vehicle(vehicle_id)`**
   - Vérifie si l'utilisateur peut accéder à un véhicule

---

## 🔄 Routes Modifiées

### Référentiels (`referentiels.py`)

#### `/referentiels/depots`
- ✅ Filtrage automatique des dépôts par région
- Les admins voient tous les dépôts

#### `/referentiels/vehicles`
- ✅ Filtrage automatique des véhicules par région (via conducteur)
- Les admins voient tous les véhicules

### Stocks (`stocks.py`)

#### `/stocks/depot/<id>`
- ✅ Vérification d'accès avant affichage
- Redirection si l'utilisateur n'a pas accès

#### `/stocks/vehicle/<id>`
- ✅ Vérification d'accès avant affichage
- Redirection si l'utilisateur n'a pas accès

#### `get_movement_form_data()`
- ✅ Filtrage automatique des dépôts et véhicules dans les formulaires

#### `/stocks/summary`
- ✅ Filtrage automatique des dépôts et véhicules dans les filtres

#### `/stocks/history`
- ✅ Filtrage automatique des dépôts et véhicules dans les filtres

### Promotion (`promotion.py`)

#### `/promotion/workflow`
- ✅ Filtrage automatique des équipes et membres par région

#### `/promotion/members`
- ✅ Filtrage automatique des membres et équipes par région

---

## 🎯 Exemples d'Utilisation

### Dans une route Flask

```python
from utils_region_filter import filter_depots_by_region

@stocks_bp.route('/depots')
@login_required
def depots_list():
    query = Depot.query.filter_by(is_active=True)
    query = filter_depots_by_region(query)  # Filtrage automatique
    depots = query.all()
    return render_template('depots_list.html', depots=depots)
```

### Vérification d'accès

```python
from utils_region_filter import can_access_depot

@stocks_bp.route('/depot/<int:depot_id>')
@login_required
def depot_stock(depot_id):
    if not can_access_depot(depot_id):
        flash('Vous n\'avez pas accès à ce dépôt', 'error')
        return redirect(url_for('stocks.depots_list'))
    
    depot = Depot.query.get_or_404(depot_id)
    # ... reste du code
```

---

## ✅ Avantages

1. **Sécurité** : Les utilisateurs ne peuvent pas accéder aux données d'autres régions
2. **Performance** : Moins de données à charger pour chaque utilisateur
3. **Simplicité** : Filtrage automatique, pas besoin de le gérer manuellement dans chaque route
4. **Flexibilité** : Les admins gardent un accès complet à toutes les données

---

## 🔒 Sécurité

- ✅ Vérification systématique de l'authentification
- ✅ Filtrage au niveau de la requête SQL (efficace)
- ✅ Vérification d'accès avant affichage des détails
- ✅ Messages d'erreur clairs pour les accès refusés

---

## 📝 Notes Importantes

1. **Assignation des utilisateurs** : Assurez-vous que chaque utilisateur a une région assignée (sauf admins)
2. **Assignation des dépôts** : Chaque dépôt doit avoir une région
3. **Assignation des véhicules** : Les véhicules doivent avoir un conducteur avec une région
4. **Assignation des équipes** : Les équipes doivent avoir un responsable avec une région

---

## 🧪 Tests à Effectuer

1. **Créer un utilisateur avec une région**
2. **Se connecter avec cet utilisateur**
3. **Vérifier que seuls les dépôts de sa région sont visibles**
4. **Vérifier que seuls les véhicules de sa région sont visibles**
5. **Vérifier que seules les équipes de sa région sont visibles**
6. **Vérifier qu'un admin voit toutes les données**

---

## ✅ Statut

**Date d'implémentation** : {{ date }}
**Statut** : ✅ Implémenté et fonctionnel
**Version** : 1.0

