-- =========================================================
-- SCRIPT DE MIGRATION COMPLÈTE : MODULE STOCKS POSTGRESQL
-- =========================================================
-- Date : 2 Janvier 2026
-- Description : Script complet pour corriger toutes les tables
--                du module stocks sur Render
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

BEGIN;

-- =========================================================
-- 1. CORRECTION stock_movements
-- =========================================================
-- (Inclut dans migration_complete_postgresql_render.sql)

-- =========================================================
-- 2. CORRECTION depot_stocks ET vehicle_stocks
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
    
    -- Ajouter colonnes manquantes
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'depot_stocks' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE depot_stocks ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- Mettre à jour les valeurs NULL
    UPDATE depot_stocks SET quantity = 0.0000 WHERE quantity IS NULL;
    ALTER TABLE depot_stocks ALTER COLUMN quantity SET NOT NULL;
    ALTER TABLE depot_stocks ALTER COLUMN quantity SET DEFAULT 0.0000;
    
    -- Contraintes et index
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
    
    -- Ajouter colonnes manquantes
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vehicle_stocks' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE vehicle_stocks ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- Mettre à jour les valeurs NULL
    UPDATE vehicle_stocks SET quantity = 0.0000 WHERE quantity IS NULL;
    ALTER TABLE vehicle_stocks ALTER COLUMN quantity SET NOT NULL;
    ALTER TABLE vehicle_stocks ALTER COLUMN quantity SET DEFAULT 0.0000;
    
    -- Contraintes et index
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
    
    RAISE NOTICE '✅ Tables depot_stocks et vehicle_stocks corrigées';
END $$;

-- =========================================================
-- 3. SYNCHRONISER LES STOCKS DEPUIS stock_movements
-- =========================================================
DO $$
DECLARE
    rec RECORD;
    calculated_qty NUMERIC(18,4);
BEGIN
    RAISE NOTICE '🔄 Synchronisation des stocks depuis stock_movements...';
    
    -- Synchroniser depot_stocks
    FOR rec IN 
        SELECT DISTINCT 
            COALESCE(to_depot_id, from_depot_id) as depot_id,
            stock_item_id
        FROM stock_movements
        WHERE to_depot_id IS NOT NULL OR from_depot_id IS NOT NULL
    LOOP
        SELECT COALESCE(SUM(
            CASE 
                WHEN to_depot_id = rec.depot_id THEN quantity
                WHEN from_depot_id = rec.depot_id THEN -ABS(quantity)
                ELSE 0
            END
        ), 0) INTO calculated_qty
        FROM stock_movements
        WHERE (to_depot_id = rec.depot_id OR from_depot_id = rec.depot_id)
        AND stock_item_id = rec.stock_item_id;
        
        INSERT INTO depot_stocks (depot_id, stock_item_id, quantity, updated_at)
        VALUES (rec.depot_id, rec.stock_item_id, calculated_qty, CURRENT_TIMESTAMP)
        ON CONFLICT (depot_id, stock_item_id) 
        DO UPDATE SET 
            quantity = calculated_qty,
            updated_at = CURRENT_TIMESTAMP;
    END LOOP;
    
    -- Synchroniser vehicle_stocks
    FOR rec IN 
        SELECT DISTINCT 
            COALESCE(to_vehicle_id, from_vehicle_id) as vehicle_id,
            stock_item_id
        FROM stock_movements
        WHERE to_vehicle_id IS NOT NULL OR from_vehicle_id IS NOT NULL
    LOOP
        SELECT COALESCE(SUM(
            CASE 
                WHEN to_vehicle_id = rec.vehicle_id THEN quantity
                WHEN from_vehicle_id = rec.vehicle_id THEN -ABS(quantity)
                ELSE 0
            END
        ), 0) INTO calculated_qty
        FROM stock_movements
        WHERE (to_vehicle_id = rec.vehicle_id OR from_vehicle_id = rec.vehicle_id)
        AND stock_item_id = rec.stock_item_id;
        
        INSERT INTO vehicle_stocks (vehicle_id, stock_item_id, quantity, updated_at)
        VALUES (rec.vehicle_id, rec.stock_item_id, calculated_qty, CURRENT_TIMESTAMP)
        ON CONFLICT (vehicle_id, stock_item_id) 
        DO UPDATE SET 
            quantity = calculated_qty,
            updated_at = CURRENT_TIMESTAMP;
    END LOOP;
    
    RAISE NOTICE '✅ Synchronisation terminée';
END $$;

-- =========================================================
-- VÉRIFICATIONS FINALES
-- =========================================================
DO $$
DECLARE
    depot_stocks_count INTEGER;
    vehicle_stocks_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VÉRIFICATIONS FINALES';
    RAISE NOTICE '========================================';
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'depot_stocks') THEN
        SELECT COUNT(*) INTO depot_stocks_count FROM depot_stocks;
        RAISE NOTICE '✅ depot_stocks: OK (% enregistrements)', depot_stocks_count;
    ELSE
        RAISE WARNING '❌ depot_stocks: MANQUANTE';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vehicle_stocks') THEN
        SELECT COUNT(*) INTO vehicle_stocks_count FROM vehicle_stocks;
        RAISE NOTICE '✅ vehicle_stocks: OK (% enregistrements)', vehicle_stocks_count;
    ELSE
        RAISE WARNING '❌ vehicle_stocks: MANQUANTE';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION STOCKS TERMINÉE';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

