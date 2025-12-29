# 📊 Différence entre Articles et Stock Items

## 🔍 Vue d'ensemble

Votre application utilise **deux systèmes distincts** pour gérer les produits :

### 1. `/articles` - Articles pour Simulations
### 2. `/referentiels/stock-items` - Articles de Stock pour Gestion

---

## 📝 `/articles` - Articles (Modèle `Article`)

### 🎯 **Usage Principal**
- **Simulations de rentabilité** : Calculer les marges et profits
- **Prévisions de ventes** : Analyser la rentabilité des importations
- **Catalogue produits** : Référentiel pour les simulations

### 📋 **Caractéristiques**
- **Modèle** : `Article`
- **Organisation** : Par **Catégories** (`Category`)
- **Prix** : En USD (par défaut) avec devise configurable
- **Affichage** : Grille de cartes avec filtres avancés
- **Champs** :
  - Nom, SKU
  - Catégorie
  - Prix d'achat (USD)
  - Devise (USD, EUR, etc.)
  - Poids unitaire (kg)
  - Statut actif/inactif

### 🔗 **Utilisé dans**
- Simulations de rentabilité
- Prévisions de ventes
- Calculs de marge
- API pour analyses

---

## 📦 `/referentiels/stock-items` - Articles de Stock (Modèle `StockItem`)

### 🎯 **Usage Principal**
- **Gestion de stock physique** : Suivi des quantités en dépôts et véhicules
- **Alertes de stock** : Seuils minimum pour réapprovisionnement
- **Traçabilité** : Mouvements de stock, réceptions, sorties
- **Inventaires** : Sessions d'inventaire et ajustements

### 📋 **Caractéristiques**
- **Modèle** : `StockItem`
- **Organisation** : Par **Familles** (`Family`)
- **Prix** : En GNF (francs guinéens)
- **Affichage** : Tableau avec actions rapides
- **Champs** :
  - SKU (obligatoire, unique)
  - Nom
  - Famille
  - Prix d'achat (GNF)
  - Poids unitaire (kg)
  - **Seuil minimum dépôt** ⚠️
  - **Seuil minimum véhicule** ⚠️
  - Description
  - Statut actif/inactif

### 🔗 **Utilisé dans**
- Gestion des stocks par dépôt
- Gestion des stocks par véhicule
- Mouvements de stock (transferts, réceptions, sorties)
- Alertes de stock minimum
- Inventaires physiques
- Traçabilité complète

---

## 🔄 **Différences Clés**

| Caractéristique | `/articles` | `/referentiels/stock-items` |
|----------------|-------------|----------------------------|
| **Modèle** | `Article` | `StockItem` |
| **Organisation** | Catégories | Familles |
| **Prix** | USD (par défaut) | GNF |
| **SKU** | Optionnel | Obligatoire et unique |
| **Seuils stock** | ❌ Non | ✅ Oui (dépôt + véhicule) |
| **Gestion stock** | ❌ Non | ✅ Oui (quantités, mouvements) |
| **Affichage** | Grille de cartes | Tableau |
| **Usage** | Simulations | Gestion opérationnelle |

---

## 💡 **Quand utiliser lequel ?**

### Utilisez `/articles` quand :
- ✅ Vous voulez créer des **simulations de rentabilité**
- ✅ Vous analysez les **marges et profits**
- ✅ Vous faites des **prévisions de ventes**
- ✅ Vous travaillez avec des **prix en devises étrangères** (USD, EUR)

### Utilisez `/referentiels/stock-items` quand :
- ✅ Vous gérez le **stock physique** (dépôts, véhicules)
- ✅ Vous avez besoin de **traçabilité** (mouvements, réceptions)
- ✅ Vous voulez des **alertes de stock minimum**
- ✅ Vous faites des **inventaires physiques**
- ✅ Vous travaillez avec des **prix en GNF**

---

## 🎯 **Recommandation**

Pour une gestion complète, vous devriez :
1. **Créer les articles** dans `/articles` pour les simulations
2. **Créer les stock items** dans `/referentiels/stock-items` pour la gestion opérationnelle
3. **Synchroniser** les deux si nécessaire (même SKU, même nom)

**Note** : Actuellement, les deux systèmes sont indépendants. Vous pourriez envisager une synchronisation future pour éviter la duplication.
