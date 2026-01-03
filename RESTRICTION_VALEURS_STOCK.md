# 🔒 RESTRICTION D'AFFICHAGE DES VALEURS DE STOCK

**Date :** 2 Janvier 2026

---

## 📋 OBJECTIF

Restreindre l'affichage des valeurs monétaires du stock pour certains rôles :
- **Magasinier (warehouse)** : Ne peut pas voir les valeurs
- **Superviseur (supervisor)** : Ne peut pas voir les valeurs
- **Commercial (commercial)** : Ne peut pas voir les valeurs

Seuls les **admins** et autres rôles de gestion peuvent voir les valeurs.

---

## 🔧 MODIFICATIONS APPORTÉES

### 1. **Nouvelle fonction de permission** (`auth.py`)

Ajout de la fonction `can_view_stock_values(user)` :

```python
def can_view_stock_values(user):
    """
    Vérifier si l'utilisateur peut voir les valeurs monétaires du stock
    
    Les rôles suivants NE PEUVENT PAS voir les valeurs :
    - warehouse (magasinier)
    - supervisor (superviseur)
    - commercial
    
    Seuls les admins et autres rôles de gestion peuvent voir les valeurs.
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    if not hasattr(user, 'role') or not user.role:
        return False
    
    # Admin peut toujours voir les valeurs
    if user.role.code == 'admin':
        return True
    
    # Rôles qui ne peuvent PAS voir les valeurs
    restricted_roles = ['warehouse', 'supervisor', 'commercial']
    if user.role.code in restricted_roles:
        return False
    
    # Tous les autres rôles peuvent voir les valeurs
    return True
```

---

### 2. **Modifications des routes** (`stocks.py`)

#### Route `depot_stock`
- Ajout de `can_view_stock_values` dans le contexte du template
- Calcul de `total_value` conditionnel

#### Route `vehicle_stock`
- Ajout de `can_view_stock_values` dans le contexte du template
- Calcul de `total_value` conditionnel

#### Route `stock_summary`
- Ajout de `can_view_stock_values` dans le contexte du template
- Calcul de `total_value` conditionnel

---

### 3. **Modifications des routes** (`analytics.py`)

#### Route `dashboard`
- Import de `can_view_stock_values`
- Ajout de `can_view_stock_values` dans le contexte du template

---

### 4. **Modifications des routes** (`flotte.py`)

#### Route `vehicle_detail`
- Import de `can_view_stock_values`
- Calcul de `stock_value` conditionnel
- Ajout de `can_view_stock_values` dans le contexte du template

---

### 5. **Modifications des templates**

#### `templates/stocks/stock_summary.html`
- Colonne "Valeur (GNF)" masquée si `can_view_stock_values == False`
- Statistique "Valeur Totale" masquée si `can_view_stock_values == False`
- Ajustement du `colspan` pour les messages vides

#### `templates/stocks/depot_stock.html`
- Colonne "Valeur" masquée si `can_view_stock_values == False`

#### `templates/stocks/vehicle_stock.html`
- Colonne "Valeur" masquée si `can_view_stock_values == False`
- Statistique "Valeur totale" masquée si `can_view_stock_values == False`

#### `templates/analytics/dashboard.html`
- KPI "Valeur Stock" masqué si `can_view_stock_values == False`

#### `templates/flotte/vehicle_detail.html`
- Colonnes "Prix Unitaire" et "Valeur Totale" masquées si `can_view_stock_values == False`
- Ligne de total "Valeur totale du stock" masquée si `can_view_stock_values == False`

---

## ✅ RÉSULTAT

### Rôles qui VOIENT les valeurs :
- ✅ **Admin** : Voit toutes les valeurs
- ✅ **Autres rôles de gestion** : Voient les valeurs

### Rôles qui NE VOIENT PAS les valeurs :
- ❌ **Magasinier (warehouse)** : Ne voit que les quantités
- ❌ **Superviseur (supervisor)** : Ne voit que les quantités
- ❌ **Commercial (commercial)** : Ne voit que les quantités

---

## 📝 NOTES

- Les quantités restent toujours visibles pour tous les rôles
- Seules les valeurs monétaires (GNF) sont masquées
- Les calculs de valeurs sont toujours effectués côté serveur, mais ne sont pas affichés si l'utilisateur n'a pas la permission
- L'admin conserve toujours tous les droits et voit toutes les valeurs

---

## 🔄 PROCHAINES ÉTAPES

1. Tester avec un utilisateur magasinier
2. Tester avec un utilisateur superviseur
3. Tester avec un utilisateur commercial
4. Vérifier que l'admin voit toujours toutes les valeurs
5. Vérifier que les quantités restent visibles pour tous

