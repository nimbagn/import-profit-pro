# Migration Fiches de Prix : Articles → Articles de Stock

## 🎯 Objectif
Modifier les fiches de prix pour utiliser les **articles de stock** (`StockItem`) au lieu des **articles standards** (`Article`).

## 📋 Modifications Apportées

### 1. Modèle de Données (`models.py`)

#### `PriceListItem` :
- ❌ **Ancien** : `article_id` → référence `articles.id`
- ✅ **Nouveau** : `stock_item_id` → référence `stock_items.id`
- ❌ **Ancien** : Relation `article = db.relationship("Article", ...)`
- ✅ **Nouveau** : Relation `stock_item = db.relationship("StockItem", ...)`
- ❌ **Ancien** : Contrainte unique sur `(price_list_id, article_id)`
- ✅ **Nouveau** : Contrainte unique sur `(price_list_id, stock_item_id)`

### 2. Routes (`price_lists.py`)

#### Changements :
- ❌ **Ancien** : `Article.query.filter_by(is_active=True)`
- ✅ **Nouveau** : `StockItem.query.filter_by(is_active=True)`
- ❌ **Ancien** : Groupement par `Category`
- ✅ **Nouveau** : Groupement par `Family`
- ❌ **Ancien** : `article_ids[]` dans les formulaires
- ✅ **Nouveau** : `stock_item_ids[]` dans les formulaires
- ❌ **Ancien** : `item.article_id` et `item.article`
- ✅ **Nouveau** : `item.stock_item_id` et `item.stock_item`

### 3. Templates

#### `templates/price_lists/form.html` :
- Variables JavaScript : `allArticlesData` → `allStockItemsData`
- Variables JavaScript : `selectedArticles` → `selectedStockItems`
- Fonctions : `showArticleSelector()` → `showStockItemSelector()`
- Fonctions : `filterArticles()` → `filterStockItems()`
- Affichage : Catégories → Familles
- Affichage : Devise d'achat → Prix d'achat GNF
- Affichage : SKU ajouté pour les articles de stock

#### `templates/price_lists/detail.html` :
- Variables : `items_by_category` → `items_by_family`
- Variables : `categories` → `families`
- Affichage : Groupement par famille au lieu de catégorie
- Filtres : Filtre par famille au lieu de catégorie
- JavaScript : `filterArticles()` → `filterStockItems()`
- JavaScript : `toggleCategory()` → `toggleFamily()`

## ⚠️ ATTENTION - Migration de Base de Données

### ⚠️ IMPORTANT : Perte de Données
**Cette migration supprime toutes les données existantes dans `price_list_items`** car il n'y a pas de correspondance directe entre `Article` et `StockItem`.

### Scripts de Migration

#### MySQL (`scripts/migrer_price_list_items_vers_stock_items_mysql.sql`)
```sql
-- Supprime les données existantes
DELETE FROM price_list_items;

-- Supprime l'ancienne structure
ALTER TABLE price_list_items DROP FOREIGN KEY fk_pricelistitem_article;
ALTER TABLE price_list_items DROP COLUMN article_id;

-- Ajoute la nouvelle structure
ALTER TABLE price_list_items ADD COLUMN stock_item_id BIGINT UNSIGNED NOT NULL;
ALTER TABLE price_list_items ADD CONSTRAINT fk_pricelistitem_stock_item 
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id);
ALTER TABLE price_list_items ADD CONSTRAINT uk_pricelistitem_unique 
    UNIQUE (price_list_id, stock_item_id);
```

#### PostgreSQL (`scripts/migrer_price_list_items_vers_stock_items_postgresql.sql`)
```sql
-- Supprime les données existantes
DELETE FROM price_list_items;

-- Supprime l'ancienne structure
ALTER TABLE price_list_items DROP CONSTRAINT IF EXISTS fk_pricelistitem_article;
ALTER TABLE price_list_items DROP COLUMN IF EXISTS article_id;

-- Ajoute la nouvelle structure
ALTER TABLE price_list_items ADD COLUMN stock_item_id BIGINT NOT NULL;
ALTER TABLE price_list_items ADD CONSTRAINT fk_pricelistitem_stock_item 
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id);
ALTER TABLE price_list_items ADD CONSTRAINT uk_pricelistitem_unique 
    UNIQUE (price_list_id, stock_item_id);
```

## 🚀 Déploiement

### 1. Local (Test)
```bash
# MySQL
mysql -u root -p madargn < scripts/migrer_price_list_items_vers_stock_items_mysql.sql

# PostgreSQL
psql -U postgres -d madargn -f scripts/migrer_price_list_items_vers_stock_items_postgresql.sql
```

### 2. Production (Render)
1. Se connecter au shell Render
2. Exécuter le script PostgreSQL approprié
3. Vérifier que la migration s'est bien passée

## ✅ Vérification Post-Migration

### Vérifier la structure de la table :
```sql
-- MySQL
DESCRIBE price_list_items;

-- PostgreSQL
\d price_list_items
```

### Vérifier les contraintes :
```sql
-- MySQL
SHOW CREATE TABLE price_list_items;

-- PostgreSQL
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'price_list_items'::regclass;
```

## 📝 Notes

- **Les fiches de prix existantes seront vidées** de leurs articles
- **Les utilisateurs devront recréer les fiches de prix** avec les articles de stock
- **Les articles de stock** sont accessibles via `/referentiels/stock-items`
- **Les familles** remplacent les catégories dans l'affichage

## 🔄 Rollback (Si Nécessaire)

Si vous devez revenir en arrière, vous devrez :
1. Restaurer une sauvegarde de la base de données
2. Ou recréer manuellement la colonne `article_id` et restaurer les données

