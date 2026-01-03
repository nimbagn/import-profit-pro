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
-- 3. CORRECTION COMPLÈTE DE stock_movements
-- =========================================================
DO $$
BEGIN
    -- Vérifier si le type ENUM existe
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'movement_type') THEN
        CREATE TYPE movement_type AS ENUM ('transfer', 'reception', 'adjustment', 'inventory');
    END IF;
    
    -- Ajouter 'reception_return' si elle n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'reception_return' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
    ) THEN
        ALTER TYPE movement_type ADD VALUE 'reception_return';
    END IF;
    
    -- Ajouter la colonne reference si manquante
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'stock_movements'
        AND column_name = 'reference'
    ) THEN
        ALTER TABLE stock_movements 
        ADD COLUMN reference VARCHAR(50) NULL;
    END IF;
    
    -- Créer les index manquants
    CREATE UNIQUE INDEX IF NOT EXISTS idx_movement_reference ON stock_movements(reference) 
    WHERE reference IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_movement_from_depot ON stock_movements(from_depot_id);
    CREATE INDEX IF NOT EXISTS idx_movement_to_depot ON stock_movements(to_depot_id);
    CREATE INDEX IF NOT EXISTS idx_movement_from_vehicle ON stock_movements(from_vehicle_id);
    CREATE INDEX IF NOT EXISTS idx_movement_to_vehicle ON stock_movements(to_vehicle_id);
    
    -- Ajouter les FK manquantes
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_movements_from_depot') THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_from_depot 
        FOREIGN KEY (from_depot_id) REFERENCES depots(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_movements_to_depot') THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_to_depot 
        FOREIGN KEY (to_depot_id) REFERENCES depots(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_movements_from_vehicle') THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_from_vehicle 
        FOREIGN KEY (from_vehicle_id) REFERENCES vehicles(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_movements_to_vehicle') THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_to_vehicle 
        FOREIGN KEY (to_vehicle_id) REFERENCES vehicles(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
    
    RAISE NOTICE '✅ stock_movements corrigé et complété';
END $$;

-- =========================================================
-- 4. CORRECTION TABLES depot_stocks ET vehicle_stocks
-- =========================================================
DO $$
BEGIN
    -- Créer depot_stocks si elle n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'depot_stocks'
    ) THEN
        CREATE TABLE depot_stocks (
            id BIGSERIAL PRIMARY KEY,
            depot_id BIGINT NOT NULL,
            stock_item_id BIGINT NOT NULL,
            quantity NUMERIC(18,4) NOT NULL DEFAULT 0.0000,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        RAISE NOTICE '✅ Table depot_stocks créée';
    END IF;
    
    -- Ajouter colonnes manquantes à depot_stocks
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'depot_stocks' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE depot_stocks ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- Contraintes et index pour depot_stocks
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_depot_stock') THEN
        ALTER TABLE depot_stocks ADD CONSTRAINT uq_depot_stock UNIQUE (depot_id, stock_item_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_depotstock_depot') THEN
        ALTER TABLE depot_stocks ADD CONSTRAINT fk_depotstock_depot 
        FOREIGN KEY (depot_id) REFERENCES depots(id) ON UPDATE CASCADE ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_depotstock_item') THEN
        ALTER TABLE depot_stocks ADD CONSTRAINT fk_depotstock_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE CASCADE;
    END IF;
    CREATE INDEX IF NOT EXISTS idx_depotstock_depot ON depot_stocks(depot_id);
    CREATE INDEX IF NOT EXISTS idx_depotstock_item ON depot_stocks(stock_item_id);
    CREATE INDEX IF NOT EXISTS idx_depotstock_depot_item ON depot_stocks(depot_id, stock_item_id);
    
    -- Créer vehicle_stocks si elle n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'vehicle_stocks'
    ) THEN
        CREATE TABLE vehicle_stocks (
            id BIGSERIAL PRIMARY KEY,
            vehicle_id BIGINT NOT NULL,
            stock_item_id BIGINT NOT NULL,
            quantity NUMERIC(18,4) NOT NULL DEFAULT 0.0000,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        RAISE NOTICE '✅ Table vehicle_stocks créée';
    END IF;
    
    -- Ajouter colonnes manquantes à vehicle_stocks
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vehicle_stocks' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE vehicle_stocks ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- Contraintes et index pour vehicle_stocks
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_vehicle_stock') THEN
        ALTER TABLE vehicle_stocks ADD CONSTRAINT uq_vehicle_stock UNIQUE (vehicle_id, stock_item_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_vehiclestock_vehicle') THEN
        ALTER TABLE vehicle_stocks ADD CONSTRAINT fk_vehiclestock_vehicle 
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_vehiclestock_item') THEN
        ALTER TABLE vehicle_stocks ADD CONSTRAINT fk_vehiclestock_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE CASCADE;
    END IF;
    CREATE INDEX IF NOT EXISTS idx_vehiclestock_vehicle ON vehicle_stocks(vehicle_id);
    CREATE INDEX IF NOT EXISTS idx_vehiclestock_item ON vehicle_stocks(stock_item_id);
    CREATE INDEX IF NOT EXISTS idx_vehiclestock_vehicle_item ON vehicle_stocks(vehicle_id, stock_item_id);
    
    -- Synchroniser les données depuis stock_movements
    -- IMPORTANT : Recalculer depuis zéro pour corriger les incohérences
    RAISE NOTICE '🔄 Synchronisation des stocks depuis stock_movements...';
    
    -- Synchroniser depot_stocks : Recalculer depuis zéro
    DELETE FROM depot_stocks;
    
    INSERT INTO depot_stocks (depot_id, stock_item_id, quantity, updated_at)
    SELECT 
        depot_id,
        stock_item_id,
        COALESCE(SUM(quantity_change), 0) as quantity,
        CURRENT_TIMESTAMP
    FROM (
        SELECT to_depot_id as depot_id, stock_item_id, quantity as quantity_change
        FROM stock_movements WHERE to_depot_id IS NOT NULL
        UNION ALL
        SELECT from_depot_id as depot_id, stock_item_id, -ABS(quantity) as quantity_change
        FROM stock_movements WHERE from_depot_id IS NOT NULL
    ) as stock_changes
    WHERE depot_id IS NOT NULL
    GROUP BY depot_id, stock_item_id;
    
    -- Synchroniser vehicle_stocks : Recalculer depuis zéro
    DELETE FROM vehicle_stocks;
    
    INSERT INTO vehicle_stocks (vehicle_id, stock_item_id, quantity, updated_at)
    SELECT 
        vehicle_id,
        stock_item_id,
        COALESCE(SUM(quantity_change), 0) as quantity,
        CURRENT_TIMESTAMP
    FROM (
        SELECT to_vehicle_id as vehicle_id, stock_item_id, quantity as quantity_change
        FROM stock_movements WHERE to_vehicle_id IS NOT NULL
        UNION ALL
        SELECT from_vehicle_id as vehicle_id, stock_item_id, -ABS(quantity) as quantity_change
        FROM stock_movements WHERE from_vehicle_id IS NOT NULL
    ) as stock_changes
    WHERE vehicle_id IS NOT NULL
    GROUP BY vehicle_id, stock_item_id;
    
    RAISE NOTICE '✅ Tables depot_stocks et vehicle_stocks corrigées et synchronisées';
END $$;

-- =========================================================
-- 5. unit_price_gnf NULLABLE DANS reception_details
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
-- 6. RETOURS FOURNISSEURS : Colonnes dans stock_returns
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
-- 7. TYPE DE MOUVEMENT 'reception_return' DANS movement_type
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
-- 8. PERMISSIONS RÔLE MAGASINIER (warehouse)
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
-- 9. PERMISSIONS RÔLE RH_ASSISTANT
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
    
    -- Vérifier stock_movements (index et FK)
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_from_depot'
    ) THEN
        RAISE NOTICE '✅ Index stock_movements: OK';
    ELSE
        RAISE WARNING '❌ Index stock_movements: MANQUANTS';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_from_depot'
    ) THEN
        RAISE NOTICE '✅ FK stock_movements: OK';
    ELSE
        RAISE WARNING '❌ FK stock_movements: MANQUANTES';
    END IF;
    
    -- Vérifier depot_stocks
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'depot_stocks'
    ) THEN
        RAISE NOTICE '✅ Table depot_stocks: OK';
    ELSE
        RAISE WARNING '❌ Table depot_stocks: MANQUANTE';
    END IF;
    
    -- Vérifier vehicle_stocks
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'vehicle_stocks'
    ) THEN
        RAISE NOTICE '✅ Table vehicle_stocks: OK';
    ELSE
        RAISE WARNING '❌ Table vehicle_stocks: MANQUANTE';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION TERMINÉE';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

