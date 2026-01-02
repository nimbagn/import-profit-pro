# 🔧 CORRECTION DU BUG DE VÉRIFICATION DU STOCK

**Date:** 2026-01-01  
**Problème:** Le magasinier ne peut pas faire de mouvement de stock car le système indique "Stock insuffisant" alors qu'il y a du stock disponible.

## 🐛 Problème Identifié

### Symptôme
```
Erreur: Stock insuffisant à la source pour MADAR POUDRE 1KG X 10 (disponible: 0, requis: 5)
```
Alors qu'il y a effectivement du stock disponible dans le dépôt.

### Cause Racine

Le bug se trouvait dans la fonction `movement_new()` du fichier `stocks.py`, lignes 974-1013.

**Problème 1: Vérification du stock source incorrecte**
```python
# AVANT (BUGUÉ)
if from_depot_id:
    source_stock = DepotStock.query.filter_by(...).first()
if not source_stock:  # ⚠️ Cette vérification est en dehors du bloc if from_depot_id
    # Créer le stock avec quantité 0
    source_stock = DepotStock(...)
    db.session.add(source_stock)
```

**Problèmes:**
1. La vérification `if not source_stock:` était en dehors du bloc `if from_depot_id:`, donc elle s'exécutait même si `from_depot_id` n'était pas défini
2. Si `from_depot_id` n'était pas défini, `source_stock` n'était jamais initialisé, donc `if not source_stock:` était toujours `True`
3. Cela créait un nouveau `DepotStock` avec quantité 0, même si un stock existait déjà dans la base de données
4. Il n'y avait pas de `else` entre `from_depot_id` et `from_vehicle_id`, donc les deux pouvaient être traités, causant des conflits

**Problème 2: Même problème pour la destination**
Le même problème existait pour la mise à jour du stock destination.

## ✅ Solution Appliquée

### Correction du stock source
```python
# APRÈS (CORRIGÉ)
source_stock = None

if from_depot_id:
    source_stock = DepotStock.query.filter_by(
        depot_id=int(from_depot_id), 
        stock_item_id=stock_item_id
    ).first()
    if not source_stock:
        # Créer le stock avec quantité 0
        source_stock = DepotStock(
            depot_id=int(from_depot_id),
            stock_item_id=stock_item_id,
            quantity=Decimal('0')
        )
        db.session.add(source_stock)
    # Vérifier le stock disponible
    if source_stock.quantity < quantity:
        item = StockItem.query.get(stock_item_id)
        item_name = item.name if item else f"ID {stock_item_id}"
        errors.append(f"Stock insuffisant à la source pour {item_name} (disponible: {source_stock.quantity}, requis: {quantity})")
        continue
    # Déduire la quantité du stock source
    source_stock.quantity -= quantity

elif from_vehicle_id:
    source_stock = VehicleStock.query.filter_by(
        vehicle_id=int(from_vehicle_id), 
        stock_item_id=stock_item_id
    ).first()
    if not source_stock:
        # Créer le stock avec quantité 0
        source_stock = VehicleStock(
            vehicle_id=int(from_vehicle_id),
            stock_item_id=stock_item_id,
            quantity=Decimal('0')
        )
        db.session.add(source_stock)
    # Vérifier le stock disponible
    if source_stock.quantity < quantity:
        item = StockItem.query.get(stock_item_id)
        item_name = item.name if item else f"ID {stock_item_id}"
        errors.append(f"Stock insuffisant à la source pour {item_name} (disponible: {source_stock.quantity}, requis: {quantity})")
        continue
    # Déduire la quantité du stock source
    source_stock.quantity -= quantity

else:
    # Aucune source définie (ne devrait pas arriver pour un transfert)
    errors.append(f"Aucune source définie pour le transfert de l'article {stock_item_id}")
    continue
```

### Améliorations
1. ✅ Initialisation explicite de `source_stock = None` au début
2. ✅ Utilisation de `elif` pour `from_vehicle_id` pour s'assurer qu'un seul est traité
3. ✅ Toutes les vérifications sont maintenant à l'intérieur des blocs appropriés
4. ✅ Ajout d'un `else` pour gérer le cas où aucune source n'est définie
5. ✅ Même correction appliquée pour la destination

## 📋 Fichiers Modifiés

- `stocks.py` (lignes 974-1052)
  - Correction de la vérification du stock source
  - Correction de la mise à jour du stock destination

## 🧪 Tests à Effectuer

1. **Test 1: Transfert depuis un dépôt avec stock disponible**
   - Créer un mouvement de transfert depuis un dépôt qui a du stock
   - Vérifier que le mouvement est créé sans erreur
   - Vérifier que le stock source est correctement déduit

2. **Test 2: Transfert depuis un dépôt sans stock**
   - Créer un mouvement de transfert depuis un dépôt sans stock
   - Vérifier que l'erreur "Stock insuffisant" est correctement affichée

3. **Test 3: Transfert depuis un véhicule**
   - Créer un mouvement de transfert depuis un véhicule
   - Vérifier que le stock véhicule est correctement géré

4. **Test 4: Transfert vers un dépôt/véhicule**
   - Vérifier que le stock destination est correctement augmenté

## ✅ Résultat Attendu

- Le système détecte correctement le stock disponible dans le dépôt/véhicule source
- Les mouvements de stock peuvent être créés sans erreur si le stock est suffisant
- Les erreurs "Stock insuffisant" ne s'affichent que lorsque le stock est réellement insuffisant

## 🚀 Déploiement

1. Tester localement avec un mouvement de stock réel
2. Vérifier que le problème est résolu
3. Pousser la correction sur Git
4. Déployer sur l'environnement de production

---

**Note:** Cette correction garantit que le stock disponible est correctement récupéré depuis la base de données avant de vérifier s'il est suffisant pour le mouvement demandé.

