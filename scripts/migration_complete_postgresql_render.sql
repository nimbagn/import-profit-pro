-- =========================================================
-- SCRIPT DE MIGRATION COMPLÈTE POSTGRESQL POUR RENDER
-- =========================================================
-- Date : 2 Janvier 2026
-- Description : Script complet et idempotent pour mettre à jour
--                la base de données PostgreSQL avec toutes les
--                fonctionnalités du projet
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

BEGIN;

-- =========================================================
-- 1. COLONNE additional_permissions DANS users
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'additional_permissions'
    ) THEN
        ALTER TABLE users 
        ADD COLUMN additional_permissions JSONB NULL;
        
        COMMENT ON COLUMN users.additional_permissions IS 
        'Permissions supplémentaires attribuées individuellement à un utilisateur (ex: stocks.read pour RH). Format JSON: {"module": ["action1", "action2"]}';
        
        RAISE NOTICE '✅ Colonne additional_permissions ajoutée';
    ELSE
        RAISE NOTICE 'ℹ️  Colonne additional_permissions existe déjà';
    END IF;
END $$;

-- =========================================================
-- 2. MIGRATION price_list_items : articles -> stock_items
-- =========================================================
DO $$
BEGIN
    -- Supprimer les données existantes si on migre
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'price_list_items' 
        AND column_name = 'article_id'
    ) THEN
        DELETE FROM price_list_items;
        RAISE NOTICE '✅ Données price_list_items supprimées pour migration';
    END IF;
    
    -- Supprimer l'ancienne contrainte FK
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_pricelistitem_article'
    ) THEN
        ALTER TABLE price_list_items DROP CONSTRAINT fk_pricelistitem_article;
        RAISE NOTICE '✅ Ancienne FK article supprimée';
    END IF;
    
    -- Supprimer l'ancien index
    DROP INDEX IF EXISTS idx_pricelistitem_article;
    
    -- Supprimer l'ancienne contrainte unique
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uk_pricelistitem_unique'
    ) THEN
        ALTER TABLE price_list_items DROP CONSTRAINT uk_pricelistitem_unique;
    END IF;
    
    -- Supprimer l'ancienne colonne article_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'price_list_items' 
        AND column_name = 'article_id'
    ) THEN
        ALTER TABLE price_list_items DROP COLUMN article_id;
        RAISE NOTICE '✅ Colonne article_id supprimée';
    END IF;
    
    -- Ajouter la nouvelle colonne stock_item_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'price_list_items' 
        AND column_name = 'stock_item_id'
    ) THEN
        ALTER TABLE price_list_items 
        ADD COLUMN stock_item_id BIGINT NULL;
        RAISE NOTICE '✅ Colonne stock_item_id ajoutée';
    END IF;
    
    -- Ajouter la contrainte FK vers stock_items
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_pricelistitem_stock_item'
    ) THEN
        ALTER TABLE price_list_items 
        ADD CONSTRAINT fk_pricelistitem_stock_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
        ON UPDATE CASCADE ON DELETE CASCADE;
        RAISE NOTICE '✅ FK stock_item ajoutée';
    END IF;
    
    -- Ajouter l'index
    CREATE INDEX IF NOT EXISTS idx_pricelistitem_stock_item ON price_list_items(stock_item_id);
    
    -- Ajouter la contrainte unique
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uk_pricelistitem_unique'
    ) THEN
        ALTER TABLE price_list_items 
        ADD CONSTRAINT uk_pricelistitem_unique 
        UNIQUE (price_list_id, stock_item_id);
        RAISE NOTICE '✅ Contrainte unique ajoutée';
    END IF;
    
    -- Rendre stock_item_id NOT NULL si nécessaire (après migration des données)
    -- Note: À faire manuellement si vous avez des données à migrer
END $$;

-- =========================================================
-- 3. COLONNE reference DANS stock_movements
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'stock_movements'
        AND column_name = 'reference'
    ) THEN
        ALTER TABLE stock_movements 
        ADD COLUMN reference VARCHAR(50) NULL;
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_movement_reference ON stock_movements(reference);
        
        RAISE NOTICE '✅ Colonne reference ajoutée à stock_movements';
    ELSE
        RAISE NOTICE 'ℹ️  Colonne reference existe déjà';
    END IF;
END $$;

-- =========================================================
-- 4. unit_price_gnf NULLABLE DANS reception_details
-- =========================================================
DO $$
BEGIN
    -- Mettre à jour les valeurs NULL existantes avec 0
    UPDATE reception_details
    SET unit_price_gnf = 0
    WHERE unit_price_gnf IS NULL;
    
    -- Modifier la colonne pour permettre NULL
    ALTER TABLE reception_details
    ALTER COLUMN unit_price_gnf DROP NOT NULL;
    
    RAISE NOTICE '✅ unit_price_gnf rendu nullable';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ℹ️  unit_price_gnf déjà nullable ou erreur: %', SQLERRM;
END $$;

-- =========================================================
-- 5. RETOURS FOURNISSEURS : Colonnes dans stock_returns
-- =========================================================
DO $$
BEGIN
    -- Créer le type ENUM pour return_type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'return_type') THEN
        CREATE TYPE return_type AS ENUM ('client', 'supplier');
        RAISE NOTICE '✅ Type return_type créé';
    END IF;
    
    -- Ajouter return_type
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'return_type'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN return_type return_type NOT NULL DEFAULT 'client';
        RAISE NOTICE '✅ Colonne return_type ajoutée';
    END IF;
    
    -- Ajouter supplier_name
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'supplier_name'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN supplier_name VARCHAR(120) NULL;
        RAISE NOTICE '✅ Colonne supplier_name ajoutée';
    END IF;
    
    -- Ajouter original_reception_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'original_reception_id'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN original_reception_id BIGINT NULL;
        
        -- Ajouter la FK
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'fk_return_reception'
        ) THEN
            ALTER TABLE stock_returns 
            ADD CONSTRAINT fk_return_reception 
                FOREIGN KEY (original_reception_id) 
                REFERENCES receptions(id) 
                ON UPDATE CASCADE 
                ON DELETE SET NULL;
        END IF;
        
        RAISE NOTICE '✅ Colonne original_reception_id ajoutée';
    END IF;
    
    -- Rendre client_name nullable
    BEGIN
        ALTER TABLE stock_returns 
        ALTER COLUMN client_name DROP NOT NULL;
        RAISE NOTICE '✅ client_name rendu nullable';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'ℹ️  client_name déjà nullable';
    END;
    
    -- Ajouter les index
    CREATE INDEX IF NOT EXISTS idx_return_type ON stock_returns(return_type);
    CREATE INDEX IF NOT EXISTS idx_return_reception ON stock_returns(original_reception_id);
END $$;

-- =========================================================
-- 6. TYPE DE MOUVEMENT 'reception_return' DANS movement_type
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'reception_return' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
    ) THEN
        ALTER TYPE movement_type ADD VALUE 'reception_return';
        RAISE NOTICE '✅ Type reception_return ajouté à movement_type';
    ELSE
        RAISE NOTICE 'ℹ️  Type reception_return existe déjà';
    END IF;
END $$;

-- =========================================================
-- 7. PERMISSIONS RÔLE MAGASINIER (warehouse)
-- =========================================================
DO $$
DECLARE
    warehouse_role_id INTEGER;
    current_permissions JSONB;
    new_permissions JSONB;
BEGIN
    SELECT id INTO warehouse_role_id
    FROM roles
    WHERE code = 'warehouse';
    
    IF warehouse_role_id IS NULL THEN
        RAISE NOTICE '⚠️  Le rôle warehouse n''existe pas, création ignorée';
        RETURN;
    END IF;
    
    SELECT permissions INTO current_permissions
    FROM roles
    WHERE id = warehouse_role_id;
    
    new_permissions := COALESCE(current_permissions, '{}'::JSONB);
    
    -- Ajouter receptions
    IF NOT (new_permissions ? 'receptions') THEN
        new_permissions := new_permissions || '{"receptions": ["read", "create", "update"]}'::JSONB;
    END IF;
    
    -- Ajouter outgoings
    IF NOT (new_permissions ? 'outgoings') THEN
        new_permissions := new_permissions || '{"outgoings": ["read", "create", "update"]}'::JSONB;
    END IF;
    
    -- Ajouter returns
    IF NOT (new_permissions ? 'returns') THEN
        new_permissions := new_permissions || '{"returns": ["read", "create", "update"]}'::JSONB;
    END IF;
    
    -- Ajouter orders
    IF NOT (new_permissions ? 'orders') THEN
        new_permissions := new_permissions || '{"orders": ["read"]}'::JSONB;
    END IF;
    
    -- Ajouter stock_loading
    IF NOT (new_permissions ? 'stock_loading') THEN
        new_permissions := new_permissions || '{"stock_loading": ["read", "verify", "load"]}'::JSONB;
    END IF;
    
    UPDATE roles
    SET permissions = new_permissions
    WHERE id = warehouse_role_id;
    
    RAISE NOTICE '✅ Permissions warehouse mises à jour';
END $$;

-- =========================================================
-- 8. PERMISSIONS RÔLE RH_ASSISTANT
-- =========================================================
DO $$
DECLARE
    rh_assistant_role_id INTEGER;
BEGIN
    SELECT id INTO rh_assistant_role_id
    FROM roles
    WHERE code = 'rh_assistant';
    
    IF rh_assistant_role_id IS NULL THEN
        RAISE NOTICE '⚠️  Le rôle rh_assistant n''existe pas, création ignorée';
        RETURN;
    END IF;
    
    UPDATE roles 
    SET permissions = '{
        "users": ["read", "create", "update"],
        "employees": ["read", "create", "update"],
        "contracts": ["read", "create", "update"],
        "trainings": ["read", "create", "update"],
        "evaluations": ["read", "create"],
        "absences": ["read", "create", "update"],
        "reports": ["read"]
    }'::jsonb
    WHERE id = rh_assistant_role_id;
    
    RAISE NOTICE '✅ Permissions rh_assistant mises à jour';
END $$;

-- =========================================================
-- VÉRIFICATIONS FINALES
-- =========================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VÉRIFICATIONS FINALES';
    RAISE NOTICE '========================================';
    
    -- Vérifier additional_permissions
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'additional_permissions'
    ) THEN
        RAISE NOTICE '✅ additional_permissions: OK';
    ELSE
        RAISE WARNING '❌ additional_permissions: MANQUANT';
    END IF;
    
    -- Vérifier stock_item_id dans price_list_items
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'price_list_items' AND column_name = 'stock_item_id'
    ) THEN
        RAISE NOTICE '✅ stock_item_id dans price_list_items: OK';
    ELSE
        RAISE WARNING '❌ stock_item_id: MANQUANT';
    END IF;
    
    -- Vérifier reference dans stock_movements
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_movements' AND column_name = 'reference'
    ) THEN
        RAISE NOTICE '✅ reference dans stock_movements: OK';
    ELSE
        RAISE WARNING '❌ reference: MANQUANT';
    END IF;
    
    -- Vérifier return_type dans stock_returns
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'return_type'
    ) THEN
        RAISE NOTICE '✅ return_type dans stock_returns: OK';
    ELSE
        RAISE WARNING '❌ return_type: MANQUANT';
    END IF;
    
    -- Vérifier reception_return dans movement_type
    IF EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'reception_return' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
    ) THEN
        RAISE NOTICE '✅ reception_return dans movement_type: OK';
    ELSE
        RAISE WARNING '❌ reception_return: MANQUANT';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION TERMINÉE';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

