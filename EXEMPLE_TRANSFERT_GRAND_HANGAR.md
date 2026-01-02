# 📦 EXEMPLE CONCRET : TRANSFERT GRAND HANGAR → AMADOU

## Scénario

### Étape 1 : Réception au Grand Hangar
- **Action** : Réception de **10 cartons** au dépôt "Grand Hangar"
- **Mouvement créé** :
  - Type : `reception`
  - Quantité : `+10` (positif = entrée)
  - `to_depot_id` : Grand Hangar
  - `from_depot_id` : `None` (réception externe)

### Étape 2 : Transfert vers Amadou
- **Action** : Transfert de **5 cartons** du Grand Hangar vers Amadou
- **Mouvements créés** :
  1. **SORTIE** (Grand Hangar) :
     - Type : `transfer`
     - Quantité : `-5` (négatif = sortie)
     - `from_depot_id` : Grand Hangar
     - `to_depot_id` : `None`
  
  2. **ENTRÉE** (Amadou) :
     - Type : `transfer`
     - Quantité : `+5` (positif = entrée)
     - `from_depot_id` : `None`
     - `to_depot_id` : Amadou

---

## 📊 État des Stocks

### Avant le Transfert

| Dépôt | DepotStock.quantity | Mouvements | Total |
|-------|---------------------|------------|-------|
| Grand Hangar | 10 | +10 (réception) | 10 |
| Amadou | 0 | - | 0 |
| **TOTAL GLOBAL** | **10** | **+10** | **10** |

### Après le Transfert

| Dépôt | DepotStock.quantity | Mouvements | Total |
|-------|---------------------|------------|-------|
| Grand Hangar | 5 | +10 (réception), -5 (sortie) | 5 |
| Amadou | 5 | +5 (entrée) | 5 |
| **TOTAL GLOBAL** | **10** | **+10 -5 +5 = 10** | **10** ✅ |

---

## ✅ Vérification

### 1. Stock Global
```
Total = Somme de tous les DepotStock.quantity
Total = 5 (Grand Hangar) + 5 (Amadou) = 10 ✅
```

### 2. Stock par Dépôt
```
Grand Hangar = 10 - 5 = 5 ✅
Amadou = 0 + 5 = 5 ✅
```

### 3. Mouvements
```
Réception : +10
Transfert SORTIE : -5
Transfert ENTRÉE : +5
Total mouvements : +10 -5 +5 = 10 ✅
```

---

## 🔍 Code Vérifié

### Mise à jour DepotStock (lignes 1029-1072)

```python
# Source (Grand Hangar)
source_stock.quantity -= quantity_decimal  # 10 - 5 = 5 ✅

# Destination (Amadou)
dest_stock.quantity += quantity  # 0 + 5 = 5 ✅
```

### Création des mouvements (lignes 1124-1160)

```python
# Mouvement SORTIE
movement_out = StockMovement(
    quantity=-quantity,  # -5 ✅
    from_depot_id=grand_hangar_id,
    to_depot_id=None
)

# Mouvement ENTRÉE
movement_in = StockMovement(
    quantity=quantity,  # +5 ✅
    from_depot_id=None,
    to_depot_id=amadou_id
)
```

---

## ✅ Conclusion

**La logique est correcte !** 

- ✅ Le stock global reste constant (10 cartons)
- ✅ Grand Hangar a 5 cartons (10 - 5)
- ✅ Amadou a 5 cartons (0 + 5)
- ✅ Les mouvements reflètent correctement les transferts
- ✅ `DepotStock` est mis à jour correctement

**Le système respecte la conservation du stock global !** ✅

