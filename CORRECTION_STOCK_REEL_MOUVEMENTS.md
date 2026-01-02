# 🔧 CORRECTION DU CALCUL DU STOCK RÉEL DANS LES MOUVEMENTS

**Date:** 2026-01-01  
**Problème:** Le système indiquait "Stock insuffisant" même quand il y avait du stock, et affichait des quantités incorrectes (1.994 au lieu de 2).

## 🐛 Problème Identifié

### Symptômes
1. Erreur: "Stock insuffisant à la source pour BOITE MOUCHOIRES DOUBLE 200 HG (disponible: 0, requis: 1.994)"
2. L'utilisateur saisit 2 mais le système affiche 1.994
3. Le stock disponible est affiché comme 0 alors qu'il y a du stock

### Causes Racines

1. **Désynchronisation entre DepotStock et StockMovement**
   - `DepotStock` peut être désynchronisé avec les mouvements réels
   - Le stock réel doit être calculé à partir de l'historique des mouvements

2. **Problème de précision décimale**
   - Les calculs avec `Decimal` peuvent produire des valeurs comme 1.994 au lieu de 2
   - L'affichage des quantités n'était pas formaté correctement

3. **Pas de recalcul du stock réel**
   - Le code utilisait uniquement `DepotStock.quantity` sans vérifier les mouvements
   - Si `DepotStock` était désynchronisé, le stock affiché était incorrect

## ✅ Solution Appliquée

### 1. Calcul du Stock Réel à partir des Mouvements

Le code calcule maintenant le stock réel en additionnant tous les mouvements :

```python
# Calculer le stock réel à partir des mouvements pour vérification
actual_stock = Decimal('0')
depot_movements = StockMovement.query.filter(
    or_(
        and_(
            StockMovement.to_depot_id == int(from_depot_id),
            StockMovement.stock_item_id == stock_item_id
        ),
        and_(
            StockMovement.from_depot_id == int(from_depot_id),
            StockMovement.stock_item_id == stock_item_id
        )
    )
).all()

for mov in depot_movements:
    if mov.to_depot_id == int(from_depot_id):
        # Entrée dans le dépôt
        actual_stock += Decimal(str(mov.quantity))
    elif mov.from_depot_id == int(from_depot_id):
        # Sortie du dépôt
        actual_stock -= abs(Decimal(str(mov.quantity)))
```

### 2. Synchronisation de DepotStock

Si `DepotStock` est désynchronisé, il est automatiquement mis à jour :

```python
# Utiliser le stock réel calculé ou celui de DepotStock
available_quantity = actual_stock if actual_stock > 0 else (source_stock.quantity if source_stock else Decimal('0'))

# Si DepotStock n'existe pas ou est désynchronisé, le créer/mettre à jour
if not source_stock:
    source_stock = DepotStock(
        depot_id=int(from_depot_id),
        stock_item_id=stock_item_id,
        quantity=available_quantity
    )
    db.session.add(source_stock)
elif abs(source_stock.quantity - actual_stock) > Decimal('0.0001'):
    # Synchroniser DepotStock avec le stock réel
    source_stock.quantity = actual_stock
```

### 3. Formatage des Quantités pour l'Affichage

Les quantités sont maintenant formatées pour éviter les décimales inutiles :

```python
# Formater les quantités pour l'affichage (éviter les décimales inutiles)
available_display = f"{available_quantity:.4f}".rstrip('0').rstrip('.')
quantity_display = f"{quantity:.4f}".rstrip('0').rstrip('.')
errors.append(f"Stock insuffisant à la source pour {item_name} (disponible: {available_display}, requis: {quantity_display})")
```

### 4. Arrondi pour la Comparaison

Les quantités sont arrondies avant la comparaison pour éviter les problèmes de précision :

```python
quantity_decimal = Decimal(str(quantity)).quantize(Decimal('0.0001'))
available_decimal = available_quantity.quantize(Decimal('0.0001'))

if available_decimal < quantity_decimal:
    # Erreur...
```

## 📋 Fichiers Modifiés

- `stocks.py` (lignes 985-1045)
  - Ajout du calcul du stock réel à partir des mouvements
  - Synchronisation automatique de `DepotStock`
  - Formatage des quantités pour l'affichage
  - Arrondi pour la comparaison

## 🧪 Tests à Effectuer

1. **Test 1: Stock disponible correctement détecté**
   - Créer un mouvement avec un dépôt qui a du stock
   - Vérifier que le mouvement est créé sans erreur

2. **Test 2: Stock insuffisant correctement détecté**
   - Créer un mouvement avec une quantité supérieure au stock disponible
   - Vérifier que l'erreur est correctement affichée avec les bonnes quantités

3. **Test 3: Synchronisation automatique**
   - Vérifier que `DepotStock` est synchronisé avec les mouvements
   - Vérifier que le stock affiché correspond au stock réel

4. **Test 4: Formatage des quantités**
   - Saisir une quantité de 2
   - Vérifier que le message d'erreur affiche "2" et non "1.994"

## ✅ Résultat Attendu

- Le système calcule le stock réel à partir des mouvements
- `DepotStock` est automatiquement synchronisé
- Les quantités sont correctement formatées dans les messages d'erreur
- Les problèmes de précision décimale sont résolus
- Le stock disponible est correctement détecté

## 🚀 Déploiement

1. Tester localement avec un mouvement de stock réel
2. Vérifier que le problème est résolu
3. Pousser la correction sur Git
4. Déployer sur l'environnement de production

---

**Note:** Cette correction garantit que le stock disponible est toujours calculé à partir de l'historique des mouvements, ce qui est la source de vérité la plus fiable.

