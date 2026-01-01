-- Migration MySQL : Changer price_list_items pour utiliser stock_items au lieu de articles
-- ATTENTION : Cette migration supprime toutes les données existantes de price_list_items
-- car il n'y a pas de correspondance directe entre Article et StockItem

USE madargn;

-- Étape 1 : Supprimer toutes les données existantes (car pas de correspondance Article -> StockItem)
DELETE FROM price_list_items;

-- Étape 2 : Supprimer l'ancienne contrainte de clé étrangère
ALTER TABLE price_list_items 
DROP FOREIGN KEY IF EXISTS fk_pricelistitem_article;

-- Étape 3 : Supprimer l'ancien index
ALTER TABLE price_list_items 
DROP INDEX IF EXISTS idx_pricelistitem_article;

-- Étape 4 : Supprimer l'ancienne contrainte unique
ALTER TABLE price_list_items 
DROP INDEX IF EXISTS uk_pricelistitem_unique;

-- Étape 5 : Supprimer l'ancienne colonne article_id
ALTER TABLE price_list_items 
DROP COLUMN IF EXISTS article_id;

-- Étape 6 : Ajouter la nouvelle colonne stock_item_id
ALTER TABLE price_list_items 
ADD COLUMN stock_item_id BIGINT UNSIGNED NOT NULL AFTER price_list_id;

-- Étape 7 : Ajouter la contrainte de clé étrangère vers stock_items
ALTER TABLE price_list_items 
ADD CONSTRAINT fk_pricelistitem_stock_item 
FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
ON UPDATE CASCADE ON DELETE CASCADE;

-- Étape 8 : Ajouter l'index sur stock_item_id
ALTER TABLE price_list_items 
ADD INDEX idx_pricelistitem_stock_item (stock_item_id);

-- Étape 9 : Ajouter la nouvelle contrainte unique
ALTER TABLE price_list_items 
ADD CONSTRAINT uk_pricelistitem_unique 
UNIQUE KEY (price_list_id, stock_item_id);

-- Vérification
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE,
    COLUMN_KEY
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'madargn' 
  AND TABLE_NAME = 'price_list_items'
ORDER BY ORDINAL_POSITION;

