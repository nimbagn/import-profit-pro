-- Migration PostgreSQL : Changer price_list_items pour utiliser stock_items au lieu de articles
-- ATTENTION : Cette migration supprime toutes les données existantes de price_list_items
-- car il n'y a pas de correspondance directe entre Article et StockItem

-- Étape 1 : Supprimer toutes les données existantes (car pas de correspondance Article -> StockItem)
DELETE FROM price_list_items;

-- Étape 2 : Supprimer l'ancienne contrainte de clé étrangère
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_pricelistitem_article'
    ) THEN
        ALTER TABLE price_list_items DROP CONSTRAINT fk_pricelistitem_article;
    END IF;
END $$;

-- Étape 3 : Supprimer l'ancien index
DROP INDEX IF EXISTS idx_pricelistitem_article;

-- Étape 4 : Supprimer l'ancienne contrainte unique
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uk_pricelistitem_unique'
    ) THEN
        ALTER TABLE price_list_items DROP CONSTRAINT uk_pricelistitem_unique;
    END IF;
END $$;

-- Étape 5 : Supprimer l'ancienne colonne article_id
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'price_list_items' 
        AND column_name = 'article_id'
    ) THEN
        ALTER TABLE price_list_items DROP COLUMN article_id;
    END IF;
END $$;

-- Étape 6 : Ajouter la nouvelle colonne stock_item_id
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'price_list_items' 
        AND column_name = 'stock_item_id'
    ) THEN
        ALTER TABLE price_list_items 
        ADD COLUMN stock_item_id BIGINT NOT NULL;
    END IF;
END $$;

-- Étape 7 : Ajouter la contrainte de clé étrangère vers stock_items
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_pricelistitem_stock_item'
    ) THEN
        ALTER TABLE price_list_items 
        ADD CONSTRAINT fk_pricelistitem_stock_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
        ON UPDATE CASCADE ON DELETE CASCADE;
    END IF;
END $$;

-- Étape 8 : Ajouter l'index sur stock_item_id
CREATE INDEX IF NOT EXISTS idx_pricelistitem_stock_item ON price_list_items(stock_item_id);

-- Étape 9 : Ajouter la nouvelle contrainte unique
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uk_pricelistitem_unique'
    ) THEN
        ALTER TABLE price_list_items 
        ADD CONSTRAINT uk_pricelistitem_unique 
        UNIQUE (price_list_id, stock_item_id);
    END IF;
END $$;

-- Vérification
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'price_list_items'
ORDER BY ordinal_position;

