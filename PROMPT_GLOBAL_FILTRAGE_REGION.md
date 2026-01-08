# PROMPT GLOBAL : SYSTÈME DE FILTRAGE PAR RÉGION

## 📋 OBJECTIF GLOBAL

L'application web doit s'afficher **exclusivement en fonction de la région** de l'utilisateur connecté. Chaque utilisateur (magasinier, commercial, superviseur, etc.) ne doit voir que les données de **sa région assignée**.

### Exemple concret :
- **Magasinier de Kankan** → Voit uniquement :
  - Commerciaux de Kankan
  - Dépôts de Kankan
  - Véhicules de Kankan
  - Commandes de Kankan
  - Stocks de Kankan
  - Mouvements de stock de Kankan
  - Inventaires de Kankan
  - Personnel de Kankan
  - etc.

- **Magasinier de Labé** → Voit uniquement les données de Labé
- **Admin/Superadmin** → Voit **TOUTES** les données de toutes les régions (exception)

---

## 🗄️ STRUCTURE DE LA BASE DE DONNÉES

### 1. Table `regions`
```sql
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Colonne `region_id` dans toutes les tables concernées

Les tables suivantes **DOIVENT** avoir une colonne `region_id` :

#### Tables utilisateurs et accès
- ✅ `users` → `region_id` (FK vers `regions.id`)
  - Chaque utilisateur est assigné à une région
  - Les admins peuvent avoir `region_id = NULL` (voient tout)

#### Tables opérationnelles
- ✅ `depots` → `region_id` (FK vers `regions.id`)
  - Chaque dépôt appartient à une région

- ✅ `vehicles` → Pas de `region_id` directe
  - La région est déterminée via `current_user_id` (conducteur)
  - Le véhicule appartient à la région du conducteur

- ✅ `commercial_orders` → `region_id` (FK vers `regions.id`)
  - La commande appartient à la région du commercial qui l'a créée

- ✅ `employees` → `region_id` (FK vers `regions.id`)
  - Chaque employé externe appartient à une région

#### Tables de stock
- ✅ `depot_stocks` → Pas de `region_id` directe
  - Filtrage via `depot_id` → `depots.region_id`

- ✅ `vehicle_stocks` → Pas de `region_id` directe
  - Filtrage via `vehicle_id` → `vehicles.current_user_id` → `users.region_id`

- ✅ `stock_movements` → Pas de `region_id` directe
  - Filtrage via `from_depot_id`, `to_depot_id`, `from_vehicle_id`, `to_vehicle_id`

- ✅ `inventory_sessions` → Pas de `region_id` directe
  - Filtrage via `depot_id` → `depots.region_id`

- ✅ `receptions` → Pas de `region_id` directe
  - Filtrage via `depot_id` → `depots.region_id`

- ✅ `stock_outgoings` → Pas de `region_id` directe
  - Filtrage via `depot_id` ou `vehicle_id`

- ✅ `stock_returns` → Pas de `region_id` directe
  - Filtrage via `depot_id` ou `vehicle_id`

- ✅ `stock_loading_summaries` → Pas de `region_id` directe
  - Filtrage via `order_id` → `commercial_orders.region_id`

---

## 🔧 MODULE `utils_region_filter.py`

### Fonction principale : `get_user_region_id()`

```python
def get_user_region_id():
    """
    Retourne l'ID de la région de l'utilisateur connecté
    Retourne None si l'utilisateur n'a pas de région ou est admin
    
    IMPORTANT: Les admins voient TOUT (pas de filtre par région).
    Cette fonction retourne None pour les admins, ce qui désactive tous les filtres de région.
    """
    if not current_user or not current_user.is_authenticated:
        return None
    
    # ⚠️ RÈGLE FONDAMENTALE : Les admins voient TOUT (pas de filtre par région)
    if hasattr(current_user, 'role') and current_user.role:
        role_code = getattr(current_user.role, 'code', None)
        if role_code in ['admin', 'superadmin']:
            return None  # Admin voit toutes les régions - aucun filtre appliqué
    
    # Retourner la région de l'utilisateur
    region_id = getattr(current_user, 'region_id', None)
    return region_id
```

### Fonctions de filtrage par type de données

#### 1. Dépôts
```python
def filter_depots_by_region(query):
    """Filtre les dépôts selon la région de l'utilisateur connecté"""
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter_by(region_id=region_id)
    return query
```

#### 2. Véhicules
```python
def filter_vehicles_by_region(query):
    """
    Filtre les véhicules selon la région de l'utilisateur connecté
    Un véhicule appartient à une région si son conducteur appartient à cette région
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.join(User, Vehicle.current_user_id == User.id).filter(
            User.region_id == region_id
        )
    return query
```

#### 3. Utilisateurs
```python
def filter_users_by_region(query):
    """Filtre les utilisateurs selon la région de l'utilisateur connecté"""
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter_by(region_id=region_id)
    return query
```

#### 4. Commandes commerciales
```python
def filter_commercial_orders_by_region(query):
    """
    Filtre les commandes commerciales selon la région de l'utilisateur connecté
    Les admins voient toutes les commandes
    Les commerciaux voient uniquement leurs propres commandes (géré ailleurs)
    Les superviseurs voient les commandes de leur région
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter(CommercialOrder.region_id == region_id)
    return query
```

#### 5. Mouvements de stock
```python
def filter_stock_movements_by_region(query):
    """
    Filtre les mouvements de stock selon la région de l'utilisateur connecté
    Un mouvement est inclus s'il est lié à un dépôt OU véhicule de la région
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts accessibles
        accessible_depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        # Récupérer les IDs des véhicules accessibles (via leur conducteur)
        accessible_vehicle_ids = []
        vehicles = Vehicle.query.join(User, Vehicle.current_user_id == User.id).filter(
            User.region_id == region_id
        ).all()
        accessible_vehicle_ids = [v.id for v in vehicles]
        
        # Filtrer les mouvements liés aux dépôts OU véhicules accessibles
        if accessible_depot_ids or accessible_vehicle_ids:
            query = query.filter(
                or_(
                    StockMovement.from_depot_id.in_(accessible_depot_ids) if accessible_depot_ids else False,
                    StockMovement.to_depot_id.in_(accessible_depot_ids) if accessible_depot_ids else False,
                    StockMovement.from_vehicle_id.in_(accessible_vehicle_ids) if accessible_vehicle_ids else False,
                    StockMovement.to_vehicle_id.in_(accessible_vehicle_ids) if accessible_vehicle_ids else False
                )
            )
        else:
            # Aucun dépôt/véhicule accessible, retourner une requête vide
            query = query.filter(False)
    
    return query
```

#### 6. Stocks de dépôt
```python
def filter_depot_stocks_by_region(query):
    """
    Filtre les stocks de dépôt selon la région de l'utilisateur connecté
    """
    region_id = get_user_region_id()
    if region_id is not None:
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        if depot_ids:
            query = query.filter(DepotStock.depot_id.in_(depot_ids))
        else:
            query = query.filter(False)
    return query
```

#### 7. Stocks de véhicule
```python
def filter_vehicle_stocks_by_region(query):
    """
    Filtre les stocks de véhicule selon la région de l'utilisateur connecté
    """
    region_id = get_user_region_id()
    if region_id is not None:
        vehicle_ids = []
        vehicles = Vehicle.query.join(User, Vehicle.current_user_id == User.id).filter(
            User.region_id == region_id
        ).all()
        vehicle_ids = [v.id for v in vehicles]
        if vehicle_ids:
            query = query.filter(VehicleStock.vehicle_id.in_(vehicle_ids))
        else:
            query = query.filter(False)
    return query
```

#### 8. Sessions d'inventaire
```python
def filter_inventory_sessions_by_region(query):
    """
    Filtre les sessions d'inventaire selon la région de l'utilisateur connecté
    Une session appartient à une région si le dépôt appartient à cette région
    """
    region_id = get_user_region_id()
    if region_id is not None:
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        if depot_ids:
            query = query.filter(InventorySession.depot_id.in_(depot_ids))
        else:
            query = query.filter(False)
    return query
```

#### 9. Réceptions
```python
def filter_receptions_by_region(query):
    """
    Filtre les réceptions selon la région de l'utilisateur connecté
    """
    region_id = get_user_region_id()
    if region_id is not None:
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        if depot_ids:
            query = query.filter(Reception.depot_id.in_(depot_ids))
        else:
            query = query.filter(False)
    return query
```

#### 10. Employés
```python
def filter_employees_by_region(query):
    """
    Filtre les employés externes selon la région de l'utilisateur connecté
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter_by(region_id=region_id)
    return query
```

---

## 📝 IMPLÉMENTATION DANS LES ROUTES

### Règle d'or : TOUJOURS filtrer les requêtes par région

#### Exemple 1 : Liste des dépôts
```python
@referentiels_bp.route('/depots')
@login_required
def depots_list():
    from utils_region_filter import filter_depots_by_region
    
    query = Depot.query
    query = filter_depots_by_region(query)  # ⚠️ OBLIGATOIRE
    depots = query.order_by(Depot.name).all()
    
    return render_template('referentiels/depots_list.html', depots=depots)
```

#### Exemple 2 : Liste des commandes
```python
@orders_bp.route('/')
@login_required
def orders_list():
    from utils_region_filter import filter_commercial_orders_by_region
    
    query = CommercialOrder.query
    query = filter_commercial_orders_by_region(query)  # ⚠️ OBLIGATOIRE
    orders = query.order_by(CommercialOrder.created_at.desc()).all()
    
    return render_template('orders/list.html', orders=orders)
```

#### Exemple 3 : Dashboard avec statistiques
```python
@app.route('/')
@login_required
def index():
    from utils_region_filter import (
        filter_depots_by_region,
        filter_vehicles_by_region,
        filter_stock_movements_by_region,
        filter_inventory_sessions_by_region,
        filter_commercial_orders_by_region
    )
    
    # Statistiques filtrées par région
    depots_query = Depot.query
    depots_query = filter_depots_by_region(depots_query)
    stats['depots_count'] = depots_query.count()
    
    vehicles_query = Vehicle.query
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    stats['vehicles_count'] = vehicles_query.count()
    
    # etc.
```

---

## 🎨 AFFICHAGE VISUEL DANS L'INTERFACE

### 1. Bannière de région (dans `base_modern_complete.html`)

```html
{% if region_info.is_filtered_by_region %}
<div class="region-filter-banner">
    <i class="fas fa-filter"></i>
    <span><strong>Vue filtrée par région :</strong> Vous ne voyez que les données de la région <strong>{{ region_info.user_region_name }}</strong></span>
</div>
{% elif region_info.is_admin %}
<div class="region-filter-banner">
    <i class="fas fa-shield-alt"></i>
    <span><strong>Vue globale :</strong> En tant qu'administrateur, vous voyez toutes les données de toutes les régions</span>
</div>
{% endif %}
```

### 2. Badge de région dans le header

```html
{% if current_user.region %}
<div class="region-badge-header">
    <i class="fas fa-map-marker-alt"></i>
    <span>{{ current_user.region.name }}{% if current_user.region.code %} ({{ current_user.region.code }}){% endif %}</span>
</div>
{% elif current_user.role and current_user.role.code in ['admin', 'superadmin'] %}
<div class="region-badge-header">
    <i class="fas fa-shield-alt"></i>
    <span>Vue Globale</span>
</div>
{% endif %}
```

### 3. Context Processor (dans `app.py`)

```python
@app.context_processor
def inject_region_info():
    """Injecte l'information de région dans tous les templates"""
    from utils_region_filter import get_user_region_id
    from models import Region
    
    region_info = {
        'user_region_id': None,
        'user_region_name': None,
        'is_admin': False,
        'is_filtered_by_region': False
    }
    
    if current_user.is_authenticated:
        if hasattr(current_user, 'role') and current_user.role:
            if current_user.role.code in ['admin', 'superadmin']:
                region_info['is_admin'] = True
                region_info['is_filtered_by_region'] = False
            else:
                region_id = get_user_region_id()
                if region_id:
                    region = Region.query.get(region_id)
                    if region:
                        region_info['user_region_id'] = region_id
                        region_info['user_region_name'] = region.name
                        region_info['is_filtered_by_region'] = True
    
    return {'region_info': region_info}
```

---

## 🔍 CHECKLIST DE VÉRIFICATION

### Pour chaque nouvelle route/fonction, vérifier :

- [ ] Les requêtes sont-elles filtrées par région ?
- [ ] Les statistiques sont-elles filtrées par région ?
- [ ] Les listes sont-elles filtrées par région ?
- [ ] Les formulaires de sélection (dépôts, véhicules, etc.) sont-ils filtrés par région ?
- [ ] Les exports (Excel, PDF) sont-ils filtrés par région ?
- [ ] Les graphiques/tableaux de bord sont-ils filtrés par région ?

### Modules à vérifier :

- [x] **Stocks** (`stocks.py`)
  - [x] Liste des mouvements
  - [x] Dashboard magasinier
  - [x] Récapitulatif stock
  - [x] Réceptions
  - [x] Sorties
  - [x] Retours
  - [x] Commandes validées en attente

- [x] **Commandes** (`orders.py`)
  - [x] Liste des commandes
  - [x] Détail commande
  - [x] Statistiques

- [x] **Référentiels** (`referentiels.py`)
  - [x] Liste des dépôts
  - [x] Liste des véhicules
  - [x] Liste des articles

- [x] **Inventaires** (`inventaires.py`)
  - [x] Liste des sessions
  - [x] Détail session

- [x] **RH** (`rh.py`)
  - [x] Liste des employés
  - [x] Contrats
  - [x] Formations
  - [x] Évaluations
  - [x] Absences

- [x] **Flotte** (`flotte.py`)
  - [x] Liste des véhicules
  - [x] Documents véhicules
  - [x] Maintenances

- [x] **Dashboard principal** (`app.py`)
  - [x] Statistiques globales
  - [x] Inventaires récents
  - [x] Mouvements récents
  - [x] Commandes récentes

---

## 📱 RESPONSIVITÉ ET ADAPTATION MOBILE

### 1. CSS Responsive Global

Le système de filtrage par région doit être **visible et clair** sur tous les appareils :

```css
/* Bannière de région responsive */
.region-filter-banner {
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

@media (max-width: 768px) {
    .region-filter-banner {
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        flex-direction: column;
        align-items: flex-start;
    }
}

/* Badge de région dans le header */
.region-badge-header {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
}

@media (max-width: 768px) {
    .region-badge-header {
        font-size: 0.75rem;
        padding: 0.3rem 0.6rem;
    }
}
```

### 2. Adaptation pour tablettes et mobiles

- La bannière de région doit rester visible même sur petits écrans
- Le badge de région peut être simplifié sur mobile (icône seule)
- Les filtres de région dans les formulaires doivent être adaptés pour le tactile

---

## 🗃️ SCRIPTS SQL POUR MISE À JOUR DE LA BASE DE DONNÉES

### Script PostgreSQL complet (Render)

Voir le fichier : `scripts/verify_and_update_region_data_postgresql.sql`

Ce script :
1. Vérifie l'existence de la table `regions`
2. Ajoute `region_id` aux tables si manquant
3. Assigne une région par défaut aux enregistrements sans région
4. Vérifie la cohérence des données

### Guide d'exécution

Voir le fichier : `EXECUTER_VERIFICATION_REGIONS_RENDER.md`

---

## ⚠️ RÈGLES IMPORTANTES

### 1. Exception Admin/Superadmin
- Les admins et superadmins **VOIENT TOUT** (pas de filtre)
- `get_user_region_id()` retourne `None` pour les admins
- Tous les filtres vérifient `if region_id is not None` avant d'appliquer

### 2. Rôles spéciaux
- **Commercial** : Voit uniquement SES commandes (géré dans `orders.py`)
- **Magasinier** : Voit uniquement les données de sa région
- **Superviseur** : Voit uniquement les données de sa région
- **RH Assistant** : Voit uniquement les données de sa région

### 3. Relations indirectes
Certaines tables n'ont pas de `region_id` directe :
- `depot_stocks` → Filtrage via `depot_id` → `depots.region_id`
- `vehicle_stocks` → Filtrage via `vehicle_id` → `vehicles.current_user_id` → `users.region_id`
- `stock_movements` → Filtrage via dépôts/véhicules impliqués
- `inventory_sessions` → Filtrage via `depot_id` → `depots.region_id`

### 4. Performance
- Utiliser `joinedload()` pour éviter les requêtes N+1
- Utiliser `load_only()` pour limiter les colonnes chargées
- Éviter de charger toutes les données en mémoire avant de filtrer

---

## 🧪 TESTS À EFFECTUER

### Test 1 : Utilisateur de Kankan
1. Se connecter avec un utilisateur de Kankan
2. Vérifier que seules les données de Kankan sont visibles :
   - Dépôts de Kankan uniquement
   - Véhicules de Kankan uniquement
   - Commandes de Kankan uniquement
   - Stocks de Kankan uniquement
   - Mouvements de Kankan uniquement

### Test 2 : Utilisateur de Labé
1. Se connecter avec un utilisateur de Labé
2. Vérifier que seules les données de Labé sont visibles
3. Vérifier qu'aucune donnée de Kankan n'est visible

### Test 3 : Admin
1. Se connecter avec un admin
2. Vérifier que TOUTES les données de TOUTES les régions sont visibles
3. Vérifier que la bannière indique "Vue globale"

### Test 4 : Responsive
1. Tester sur desktop (1920x1080)
2. Tester sur tablette (768x1024)
3. Tester sur mobile (375x667)
4. Vérifier que la bannière de région reste visible et lisible

---

## 📚 DOCUMENTATION TECHNIQUE

### Architecture du filtrage

```
User (region_id)
    ↓
get_user_region_id()
    ↓
filter_*_by_region(query)
    ↓
Query filtrée
    ↓
Template avec region_info
    ↓
Affichage filtré + bannière
```

### Flux de données

1. **Authentification** : `load_user()` charge `User.region` et `User.role`
2. **Context Processor** : Injecte `region_info` dans tous les templates
3. **Routes** : Appliquent les filtres via `utils_region_filter`
4. **Templates** : Affichent les données filtrées + bannière de région

---

## 🔄 MAINTENANCE ET ÉVOLUTION

### Ajouter un nouveau type de données à filtrer

1. **Créer la fonction de filtrage** dans `utils_region_filter.py` :
```python
def filter_nouveau_type_by_region(query):
    region_id = get_user_region_id()
    if region_id is not None:
        # Logique de filtrage
        query = query.filter(NouveauType.region_id == region_id)
    return query
```

2. **Appliquer dans les routes** :
```python
from utils_region_filter import filter_nouveau_type_by_region

query = NouveauType.query
query = filter_nouveau_type_by_region(query)
items = query.all()
```

3. **Ajouter à la checklist** ci-dessus

### Vérifier la cohérence des données

Exécuter régulièrement le script SQL de vérification pour s'assurer que :
- Tous les utilisateurs ont une région (sauf admins)
- Tous les dépôts ont une région
- Toutes les commandes ont une région
- Tous les employés ont une région

---

## ✅ CONCLUSION

Ce système de filtrage par région est **centralisé** et **cohérent** dans toute l'application. Il garantit que :

1. ✅ Chaque utilisateur ne voit que les données de sa région
2. ✅ Les admins voient toutes les données
3. ✅ L'interface indique clairement le mode de filtrage
4. ✅ Le système est responsive et adapté à tous les appareils
5. ✅ La base de données est structurée pour supporter le filtrage
6. ✅ Les performances sont optimisées avec des requêtes efficaces

**Toute nouvelle fonctionnalité doit respecter ces règles de filtrage par région.**

