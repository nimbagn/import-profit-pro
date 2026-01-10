# 📋 Guide Complet : Filtrage Automatique par Région

## 🎯 Objectif

**TOUS les utilisateurs** (sauf admins et superviseurs) voient **uniquement les données de leur région assignée**. Le filtrage s'applique automatiquement aux utilisateurs actuels et futurs.

## 🔧 Règles de Filtrage

### Utilisateurs Filtrés par Région

Les utilisateurs suivants voient **uniquement** les données de leur région :
- ✅ **Magasiniers** (`warehouse`)
- ✅ **Commerciaux** (`commercial`)
- ✅ **Tous les autres rôles** (sauf admin/supervisor)

### Utilisateurs NON Filtrés

Les utilisateurs suivants voient **TOUTES** les données (toutes régions) :
- 🔓 **Administrateurs** (`admin`, `superadmin`)
- 🔓 **Superviseurs** (`supervisor`)

## 📊 Données Filtrées

Le filtrage s'applique automatiquement à :

### 1. Stocks
- ✅ Stocks de dépôt (`DepotStock`)
- ✅ Stocks de véhicule (`VehicleStock`)
- ✅ Mouvements de stock (`StockMovement`)
- ✅ Réceptions (`Reception`)
- ✅ Sorties (`StockOutgoing`)
- ✅ Retours (`StockReturn`)
- ✅ Sessions d'inventaire (`InventorySession`)

### 2. Commandes et Ventes
- ✅ Commandes commerciales (`CommercialOrder`)
- ✅ Ventes commerciales (`CommercialSale`)
- ✅ Objectifs de vente (`SalesObjective`)

### 3. Équipes Commerciales
- ✅ Équipes promotion (`PromotionTeam`)
- ✅ Équipes lockistes (`LockisteTeam`)
- ✅ Équipes vendeurs (`VendeurTeam`)
- ✅ Membres d'équipes (`PromotionMember`, `LockisteMember`, `VendeurMember`)

### 4. Référentiels
- ✅ Dépôts (`Depot`)
- ✅ Véhicules (`Vehicle`)
- ✅ Utilisateurs (`User`)
- ✅ Employés externes (`Employee`)

## 🔍 Fonctionnement Technique

### Fonction Principale : `get_user_region_id()`

```python
def get_user_region_id():
    """
    Retourne l'ID de la région de l'utilisateur connecté
    Retourne None si l'utilisateur n'a pas de région ou est admin/superviseur
    
    IMPORTANT: 
    - Les admins et superviseurs voient TOUT (pas de filtre par région)
    - TOUS les autres utilisateurs voient uniquement leur région
    """
    # Seuls admin et supervisor voient toutes les régions
    if role_code in ['admin', 'superadmin', 'supervisor']:
        return None  # Pas de filtre
    
    # Retourner la région de l'utilisateur
    return current_user.region_id
```

### Fonctions de Filtrage Disponibles

Toutes les fonctions suivantes sont disponibles dans `utils_region_filter.py` :

```python
# Stocks
filter_depots_by_region(query)
filter_vehicles_by_region(query)
filter_stock_movements_by_region(query)
filter_depot_stocks_by_region(query)
filter_vehicle_stocks_by_region(query)
filter_receptions_by_region(query)
filter_outgoings_by_region(query)
filter_returns_by_region(query)
filter_inventory_sessions_by_region(query)

# Commandes et Ventes
filter_commercial_orders_by_region(query)
filter_commercial_sales_by_region(query)
filter_sales_objectives_by_region(query)

# Équipes
filter_teams_by_region(query)  # Promotion
filter_lockiste_teams_by_region(query)
filter_vendeur_teams_by_region(query)
filter_members_by_region(query)

# Référentiels
filter_users_by_region(query)
filter_employees_by_region(query)
```

### Utilisation dans les Routes

```python
from utils_region_filter import filter_depots_by_region

@blueprint.route('/depots')
@login_required
def depots_list():
    # Filtrer automatiquement par région
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.all()
    
    return render_template('depots/list.html', depots=depots)
```

## 📝 Configuration des Utilisateurs

### Assigner une Région à un Utilisateur

1. **Via l'interface** : `/auth/users/<id>/edit`
   - Sélectionner la région dans le champ "Région"

2. **Via SQL** :
```sql
UPDATE users 
SET region_id = 1  -- ID de la région
WHERE id = 123;     -- ID de l'utilisateur
```

### Vérifier les Utilisateurs sans Région

Exécuter le script SQL :
```bash
psql $DATABASE_URL -f scripts/APPLIQUER_FILTRAGE_REGION_COMPLET_POSTGRESQL.sql
```

## ⚠️ Points Importants

### 1. Utilisateurs Nouveaux

**TOUS les nouveaux utilisateurs** (sauf admins/superviseurs) **DOIVENT** avoir une région assignée lors de leur création.

### 2. Utilisateurs Existants

Vérifiez que tous les utilisateurs existants ont une région assignée :
- Les magasiniers doivent avoir une région
- Les commerciaux doivent avoir une région
- Seuls les admins et superviseurs peuvent avoir `region_id = NULL`

### 3. Superviseurs

Les superviseurs voient **toutes les données** (pas de filtre par région) pour pouvoir superviser plusieurs régions si nécessaire.

### 4. Magasiniers

Les magasiniers sont maintenant filtrés par région, mais peuvent toujours accéder à tous les véhicules (pour gestion de flotte).

## 🔄 Migration

### Pour les Utilisateurs Existants

1. **Identifier les utilisateurs sans région** :
```sql
SELECT u.id, u.username, r.code as role_code
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.region_id IS NULL
  AND r.code NOT IN ('admin', 'superadmin', 'supervisor');
```

2. **Assigner une région** :
```sql
UPDATE users 
SET region_id = <region_id>
WHERE id = <user_id>;
```

### Script SQL Complet

Utiliser le script `scripts/APPLIQUER_FILTRAGE_REGION_COMPLET_POSTGRESQL.sql` pour :
- Vérifier les utilisateurs sans région
- Voir les statistiques par région
- Assigner des régions si nécessaire

## ✅ Vérification

Après la configuration, vérifiez que :

1. ✅ Les magasiniers voient uniquement les stocks de leur région
2. ✅ Les commerciaux voient uniquement les commandes de leur région
3. ✅ Les admins voient toutes les données
4. ✅ Les superviseurs voient toutes les données
5. ✅ Les nouveaux utilisateurs sont automatiquement filtrés

## 📞 Support

Si un utilisateur ne voit pas les bonnes données :
1. Vérifier que l'utilisateur a une région assignée
2. Vérifier que la région est active
3. Vérifier que le rôle de l'utilisateur n'est pas admin/supervisor
4. Vérifier les logs de l'application pour les erreurs de filtrage

