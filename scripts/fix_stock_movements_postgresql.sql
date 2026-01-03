-- =========================================================
-- SCRIPT DE CORRECTION : stock_movements POUR POSTGRESQL
-- =========================================================
-- Date : 2 Janvier 2026
-- Description : Corrige et complète la table stock_movements
--                pour que /stocks/movements fonctionne sur Render
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

BEGIN;

-- =========================================================
-- 1. VÉRIFIER ET CRÉER LE TYPE ENUM movement_type
-- =========================================================
DO $$
BEGIN
    -- Vérifier si le type existe
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'movement_type') THEN
        CREATE TYPE movement_type AS ENUM ('transfer', 'reception', 'adjustment', 'inventory');
        RAISE NOTICE '✅ Type movement_type créé';
    ELSE
        RAISE NOTICE 'ℹ️  Type movement_type existe déjà';
    END IF;
    
    -- Ajouter 'reception_return' si elle n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'reception_return' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
    ) THEN
        ALTER TYPE movement_type ADD VALUE 'reception_return';
        RAISE NOTICE '✅ Valeur reception_return ajoutée à movement_type';
    ELSE
        RAISE NOTICE 'ℹ️  Valeur reception_return existe déjà';
    END IF;
END $$;

-- =========================================================
-- 2. VÉRIFIER ET CRÉER LA TABLE stock_movements
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'stock_movements'
    ) THEN
        -- Créer la table si elle n'existe pas
        CREATE TABLE stock_movements (
            id BIGSERIAL PRIMARY KEY,
            reference VARCHAR(50) NULL,
            movement_type movement_type NOT NULL,
            movement_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            stock_item_id BIGINT NOT NULL,
            quantity NUMERIC(18,4) NOT NULL,
            user_id BIGINT NULL,
            from_depot_id BIGINT NULL,
            from_vehicle_id BIGINT NULL,
            to_depot_id BIGINT NULL,
            to_vehicle_id BIGINT NULL,
            supplier_name VARCHAR(120) NULL,
            bl_number VARCHAR(50) NULL,
            reason TEXT NULL,
            inventory_session_id BIGINT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE '✅ Table stock_movements créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table stock_movements existe déjà';
    END IF;
END $$;

-- =========================================================
-- 3. AJOUTER LA COLONNE reference SI MANQUANTE
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'stock_movements'
        AND column_name = 'reference'
    ) THEN
        ALTER TABLE stock_movements 
        ADD COLUMN reference VARCHAR(50) NULL;
        
        RAISE NOTICE '✅ Colonne reference ajoutée';
    ELSE
        RAISE NOTICE 'ℹ️  Colonne reference existe déjà';
    END IF;
END $$;

-- =========================================================
-- 4. AJOUTER LES CONTRAINTES DE CLÉS ÉTRANGÈRES
-- =========================================================
DO $$
BEGIN
    -- FK vers stock_items
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_item'
    ) THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
        ON UPDATE CASCADE ON DELETE RESTRICT;
        RAISE NOTICE '✅ FK fk_movements_item ajoutée';
    END IF;
    
    -- FK vers users
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_user'
    ) THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_user 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
        RAISE NOTICE '✅ FK fk_movements_user ajoutée';
    END IF;
    
    -- FK vers depots (from_depot_id)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_from_depot'
    ) THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_from_depot 
        FOREIGN KEY (from_depot_id) REFERENCES depots(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
        RAISE NOTICE '✅ FK fk_movements_from_depot ajoutée';
    END IF;
    
    -- FK vers vehicles (from_vehicle_id)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_from_vehicle'
    ) THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_from_vehicle 
        FOREIGN KEY (from_vehicle_id) REFERENCES vehicles(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
        RAISE NOTICE '✅ FK fk_movements_from_vehicle ajoutée';
    END IF;
    
    -- FK vers depots (to_depot_id)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_to_depot'
    ) THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_to_depot 
        FOREIGN KEY (to_depot_id) REFERENCES depots(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
        RAISE NOTICE '✅ FK fk_movements_to_depot ajoutée';
    END IF;
    
    -- FK vers vehicles (to_vehicle_id)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_movements_to_vehicle'
    ) THEN
        ALTER TABLE stock_movements 
        ADD CONSTRAINT fk_movements_to_vehicle 
        FOREIGN KEY (to_vehicle_id) REFERENCES vehicles(id) 
        ON UPDATE CASCADE ON DELETE SET NULL;
        RAISE NOTICE '✅ FK fk_movements_to_vehicle ajoutée';
    END IF;
    
    -- FK vers inventory_sessions (si la table existe)
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'inventory_sessions'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'fk_movements_inventory_session'
        ) THEN
            ALTER TABLE stock_movements 
            ADD CONSTRAINT fk_movements_inventory_session 
            FOREIGN KEY (inventory_session_id) REFERENCES inventory_sessions(id) 
            ON UPDATE CASCADE ON DELETE SET NULL;
            RAISE NOTICE '✅ FK fk_movements_inventory_session ajoutée';
        END IF;
    END IF;
END $$;

-- =========================================================
-- 5. AJOUTER LES INDEX POUR PERFORMANCE
-- =========================================================
DO $$
BEGIN
    -- Index sur movement_date
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_date'
    ) THEN
        CREATE INDEX idx_movement_date ON stock_movements(movement_date);
        RAISE NOTICE '✅ Index idx_movement_date créé';
    END IF;
    
    -- Index sur movement_type
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_type'
    ) THEN
        CREATE INDEX idx_movement_type ON stock_movements(movement_type);
        RAISE NOTICE '✅ Index idx_movement_type créé';
    END IF;
    
    -- Index sur stock_item_id
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_item'
    ) THEN
        CREATE INDEX idx_movement_item ON stock_movements(stock_item_id);
        RAISE NOTICE '✅ Index idx_movement_item créé';
    END IF;
    
    -- Index sur user_id
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_user'
    ) THEN
        CREATE INDEX idx_movement_user ON stock_movements(user_id);
        RAISE NOTICE '✅ Index idx_movement_user créé';
    END IF;
    
    -- Index sur reference (unique si non NULL)
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_reference'
    ) THEN
        CREATE UNIQUE INDEX idx_movement_reference ON stock_movements(reference) 
        WHERE reference IS NOT NULL;
        RAISE NOTICE '✅ Index idx_movement_reference créé';
    END IF;
    
    -- Index sur from_depot_id (pour les requêtes de filtrage)
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_from_depot'
    ) THEN
        CREATE INDEX idx_movement_from_depot ON stock_movements(from_depot_id);
        RAISE NOTICE '✅ Index idx_movement_from_depot créé';
    END IF;
    
    -- Index sur to_depot_id
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_to_depot'
    ) THEN
        CREATE INDEX idx_movement_to_depot ON stock_movements(to_depot_id);
        RAISE NOTICE '✅ Index idx_movement_to_depot créé';
    END IF;
    
    -- Index sur from_vehicle_id
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_from_vehicle'
    ) THEN
        CREATE INDEX idx_movement_from_vehicle ON stock_movements(from_vehicle_id);
        RAISE NOTICE '✅ Index idx_movement_from_vehicle créé';
    END IF;
    
    -- Index sur to_vehicle_id
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'stock_movements' 
        AND indexname = 'idx_movement_to_vehicle'
    ) THEN
        CREATE INDEX idx_movement_to_vehicle ON stock_movements(to_vehicle_id);
        RAISE NOTICE '✅ Index idx_movement_to_vehicle créé';
    END IF;
END $$;

-- =========================================================
-- 6. VÉRIFICATIONS FINALES
-- =========================================================
DO $$
DECLARE
    col_count INTEGER;
    idx_count INTEGER;
    fk_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VÉRIFICATIONS FINALES';
    RAISE NOTICE '========================================';
    
    -- Compter les colonnes
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'stock_movements';
    
    RAISE NOTICE 'Colonnes dans stock_movements: %', col_count;
    
    -- Compter les index
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE tablename = 'stock_movements';
    
    RAISE NOTICE 'Index sur stock_movements: %', idx_count;
    
    -- Compter les FK
    SELECT COUNT(*) INTO fk_count
    FROM pg_constraint
    WHERE conrelid = 'stock_movements'::regclass
    AND contype = 'f';
    
    RAISE NOTICE 'Clés étrangères: %', fk_count;
    
    -- Vérifier les colonnes essentielles
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'stock_movements'
        AND column_name = 'reference'
    ) THEN
        RAISE NOTICE '✅ Colonne reference: OK';
    ELSE
        RAISE WARNING '❌ Colonne reference: MANQUANTE';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'stock_movements'
        AND column_name = 'movement_type'
    ) THEN
        RAISE NOTICE '✅ Colonne movement_type: OK';
    ELSE
        RAISE WARNING '❌ Colonne movement_type: MANQUANTE';
    END IF;
    
    -- Vérifier le type ENUM
    IF EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'reception_return'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
    ) THEN
        RAISE NOTICE '✅ Type reception_return dans movement_type: OK';
    ELSE
        RAISE WARNING '❌ Type reception_return: MANQUANT';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'CORRECTION TERMINÉE';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

