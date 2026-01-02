# ✅ IMPLÉMENTATION : RETOURS FOURNISSEURS

**Date :** 2 Janvier 2026  
**Statut :** ✅ **COMPLÉTÉ**

---

## 📋 RÉSUMÉ

Les retours sont maintenant vraiment le **mouvement inverse des réceptions**. Le système gère désormais deux types de retours :
- **Retour Client** : Retour de marchandise depuis un client → Augmente le stock
- **Retour Fournisseur** : Retour vers un fournisseur → Diminue le stock (mouvement inverse de réception)

---

## 🔧 MODIFICATIONS APPORTÉES

### 1. Modèle `StockReturn` (`models.py`)

#### Nouveaux champs ajoutés :
```python
- return_type: Enum('client', 'supplier')  # Type de retour
- supplier_name: String(120)               # Nom du fournisseur (pour retours fournisseurs)
- original_reception_id: FK(receptions.id) # Lien avec réception originale
```

#### Modifications :
- `client_name` est maintenant **nullable** (optionnel pour retours fournisseurs)
- Nouvelle relation `original_reception` pour lier aux réceptions
- Nouveaux index pour améliorer les performances

### 2. Modèle `StockMovement` (`models.py`)

#### Nouveau type de mouvement :
```python
movement_type: Enum('transfer', 'reception', 'reception_return', 'adjustment', 'inventory')
```

Le type `'reception_return'` est maintenant disponible pour les retours fournisseurs.

### 3. Route `return_new` (`stocks.py`)

#### Logique implémentée :

**Retour Client** (type = 'client') :
- Augmente le stock (quantité POSITIVE)
- Type de mouvement : `'transfer'`
- Destination : dépôt ou véhicule
- Lien avec sortie originale (`original_outgoing_id`)

**Retour Fournisseur** (type = 'supplier') :
- **Diminue le stock** (quantité NÉGATIVE) ✅
- Type de mouvement : `'reception_return'` ✅
- Source : dépôt (obligatoire)
- Lien avec réception originale (`original_reception_id`) ✅
- Vérification du stock disponible avant retour

### 4. Template `return_form.html`

#### Nouvelles fonctionnalités :
- **Sélecteur de type de retour** au début du formulaire
- **Sections conditionnelles** :
  - Section "Retour Client" (champs client, sortie originale, commercial)
  - Section "Retour Fournisseur" (champs fournisseur, réception originale)
- **JavaScript dynamique** pour basculer entre les deux types
- **Validation adaptative** selon le type sélectionné
- **Aide contextuelle** expliquant l'effet sur le stock

### 5. Fonction `generate_movement_reference` (`stocks.py`)

#### Nouveau préfixe :
```python
'reception_return': 'RET-REC'  # Pour retours fournisseurs
```

---

## 📊 COMPARAISON AVANT/APRÈS

| Aspect | Avant | Après |
|--------|-------|-------|
| **Types de retours** | 1 seul (client) | 2 types (client + fournisseur) |
| **Retour fournisseur** | ❌ N'existait pas | ✅ Implémenté |
| **Lien avec réceptions** | ❌ Aucun | ✅ `original_reception_id` |
| **Effet sur stock (retour fournisseur)** | ❌ Augmentait (incorrect) | ✅ Diminue (correct) |
| **Type de mouvement** | `'transfer'` | `'reception_return'` pour retours fournisseurs |
| **Quantité** | Toujours positive | Négative pour retours fournisseurs |

---

## 🔄 LOGIQUE MÉTIER

### Réception (Fournisseur → Dépôt)
```
Stock augmente : +qty
Mouvement : type='reception', quantity=+qty
```

### Retour Fournisseur (Dépôt → Fournisseur)
```
Stock diminue : -qty
Mouvement : type='reception_return', quantity=-qty
```

### Retour Client (Client → Dépôt/Véhicule)
```
Stock augmente : +qty
Mouvement : type='transfer', quantity=+qty
```

---

## 📝 SCRIPTS DE MIGRATION

### Fichiers créés :

1. **`scripts/migration_retours_fournisseurs_mysql.sql`**
   - Migration MySQL pour ajouter les colonnes

2. **`scripts/migration_retours_fournisseurs_postgresql.sql`**
   - Migration PostgreSQL pour ajouter les colonnes

3. **`scripts/migration_movement_type_reception_return_mysql.sql`**
   - Migration MySQL pour ajouter le type `'reception_return'`

4. **`scripts/migration_movement_type_reception_return_postgresql.sql`**
   - Migration PostgreSQL pour ajouter le type `'reception_return'`

5. **`scripts/migration_retours_fournisseurs.py`**
   - Script Python automatique pour exécuter toutes les migrations

---

## 🚀 UTILISATION

### Pour créer un retour fournisseur :

1. Aller sur `/stocks/returns/new`
2. Sélectionner **"Retour Fournisseur"** dans le sélecteur de type
3. Remplir :
   - Nom du fournisseur (obligatoire)
   - Réception originale (optionnel, pour traçabilité)
   - Dépôt source (obligatoire)
   - Date de retour
   - Articles à retourner
4. Le système :
   - Vérifie que le stock est suffisant
   - Diminue le stock du dépôt
   - Crée un mouvement de type `'reception_return'` avec quantité négative

### Pour créer un retour client :

1. Aller sur `/stocks/returns/new`
2. Sélectionner **"Retour Client"** (par défaut)
3. Remplir les champs client habituels
4. Le système :
   - Augmente le stock (dépôt ou véhicule)
   - Crée un mouvement de type `'transfer'` avec quantité positive

---

## ✅ VÉRIFICATIONS

### Points à vérifier après migration :

1. ✅ Les colonnes `return_type`, `supplier_name`, `original_reception_id` existent dans `stock_returns`
2. ✅ Le type `'reception_return'` existe dans l'enum `movement_type`
3. ✅ Les retours fournisseurs diminuent bien le stock
4. ✅ Les retours clients augmentent le stock
5. ✅ Les mouvements de type `'reception_return'` ont des quantités négatives
6. ✅ Le formulaire permet de choisir entre les deux types

---

## 📚 DOCUMENTATION

- **Analyse détaillée** : `ANALYSE_RECEPTIONS_VS_RETOURS.md`
- **Scripts de migration** : `scripts/migration_retours_fournisseurs*.sql`
- **Script Python** : `scripts/migration_retours_fournisseurs.py`

---

## 🎯 RÉSULTAT

Les **retours fournisseurs** sont maintenant le **mouvement inverse des réceptions** :
- ✅ Lien avec les réceptions (`original_reception_id`)
- ✅ Diminution du stock (quantité négative)
- ✅ Type de mouvement dédié (`'reception_return'`)
- ✅ Traçabilité complète du cycle : Réception → Retour Fournisseur

