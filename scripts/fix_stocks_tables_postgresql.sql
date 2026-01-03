-- =========================================================
-- SCRIPT DE CORRECTION : TABLES DE STOCK POUR POSTGRESQL
-- =========================================================
-- Date : 2 Janvier 2026
-- Description : Corrige et complète les tables depot_stocks et vehicle_stocks
--                pour que les mouvements de stock fonctionnent sur Render
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

BEGIN;

-- =========================================================
-- 1. CRÉER LA TABLE depot_stocks SI ELLE N'EXISTE PAS
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'depot_stocks'
    ) THEN
        CREATE TABLE depot_stocks (
            id BIGSERIAL PRIMARY KEY,
            depot_id BIGINT NOT NULL,
            stock_item_id BIGINT NOT NULL,
            quantity NUMERIC(18,4) NOT NULL DEFAULT 0.0000,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE '✅ Table depot_stocks créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table depot_stocks existe déjà';
    END IF;
END $$;

-- =========================================================
-- 2. AJOUTER LES COLONNES MANQUANTES À depot_stocks
-- =========================================================
DO $$
BEGIN
    -- Vérifier et ajouter updated_at si manquante
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'depot_stocks' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE depot_stocks 
        ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE '✅ Colonne updated_at ajoutée à depot_stocks';
    END IF;
    
    -- S'assurer que quantity a une valeur par défaut
    ALTER TABLE depot_stocks 
    ALTER COLUMN quantity SET DEFAULT 0.0000;
    
    -- Mettre à jour les valeurs NULL à 0
    UPDATE depot_stocks 
    SET quantity = 0.0000 
    WHERE quantity IS NULL;
    
    -- Rendre quantity NOT NULL si ce n'est pas déjà le cas
    ALTER TABLE depot_stocks 
    ALTER COLUMN quantity SET NOT NULL;
END $$;

-- =========================================================
-- 3. CONTRAINTES ET INDEX POUR depot_stocks
-- =========================================================
DO $$
BEGIN
    -- Contrainte unique (depot_id, stock_item_id)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_depot_stock'
    ) THEN
        ALTER TABLE depot_stocks 
        ADD CONSTRAINT uq_depot_stock 
        UNIQUE (depot_id, stock_item_id);
        RAISE NOTICE '✅ Contrainte unique uq_depot_stock ajoutée';
    END IF;
    
    -- FK vers depots
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_depotstock_depot'
    ) THEN
        ALTER TABLE depot_stocks 
        ADD CONSTRAINT fk_depotstock_depot 
        FOREIGN KEY (depot_id) REFERENCES depots(id) 
        ON UPDATE CASCADE ON DELETE CASCADE;
        RAISE NOTICE '✅ FK fk_depotstock_depot ajoutée';
    END IF;
    
    -- FK vers stock_items
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_depotstock_item'
    ) THEN
        ALTER TABLE depot_stocks 
        ADD CONSTRAINT fk_depotstock_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
        ON UPDATE CASCADE ON DELETE CASCADE;
        RAISE NOTICE '✅ FK fk_depotstock_item ajoutée';
    END IF;
    
    -- Index sur depot_id
    CREATE INDEX IF NOT EXISTS idx_depotstock_depot ON depot_stocks(depot_id);
    
    -- Index sur stock_item_id
    CREATE INDEX IF NOT EXISTS idx_depotstock_item ON depot_stocks(stock_item_id);
    
    -- Index composite pour les requêtes fréquentes
    CREATE INDEX IF NOT EXISTS idx_depotstock_depot_item ON depot_stocks(depot_id, stock_item_id);
END $$;

-- =========================================================
-- 4. CRÉER LA TABLE vehicle_stocks SI ELLE N'EXISTE PAS
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'vehicle_stocks'
    ) THEN
        CREATE TABLE vehicle_stocks (
            id BIGSERIAL PRIMARY KEY,
            vehicle_id BIGINT NOT NULL,
            stock_item_id BIGINT NOT NULL,
            quantity NUMERIC(18,4) NOT NULL DEFAULT 0.0000,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE '✅ Table vehicle_stocks créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table vehicle_stocks existe déjà';
    END IF;
END $$;

-- =========================================================
-- 5. AJOUTER LES COLONNES MANQUANTES À vehicle_stocks
-- =========================================================
DO $$
BEGIN
    -- Vérifier et ajouter updated_at si manquante
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vehicle_stocks' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE vehicle_stocks 
        ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE '✅ Colonne updated_at ajoutée à vehicle_stocks';
    END IF;
    
    -- S'assurer que quantity a une valeur par défaut
    ALTER TABLE vehicle_stocks 
    ALTER COLUMN quantity SET DEFAULT 0.0000;
    
    -- Mettre à jour les valeurs NULL à 0
    UPDATE vehicle_stocks 
    SET quantity = 0.0000 
    WHERE quantity IS NULL;
    
    -- Rendre quantity NOT NULL si ce n'est pas déjà le cas
    ALTER TABLE vehicle_stocks 
    ALTER COLUMN quantity SET NOT NULL;
END $$;

-- =========================================================
-- 6. CONTRAINTES ET INDEX POUR vehicle_stocks
-- =========================================================
DO $$
BEGIN
    -- Contrainte unique (vehicle_id, stock_item_id)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_vehicle_stock'
    ) THEN
        ALTER TABLE vehicle_stocks 
        ADD CONSTRAINT uq_vehicle_stock 
        UNIQUE (vehicle_id, stock_item_id);
        RAISE NOTICE '✅ Contrainte unique uq_vehicle_stock ajoutée';
    END IF;
    
    -- FK vers vehicles
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_vehiclestock_vehicle'
    ) THEN
        ALTER TABLE vehicle_stocks 
        ADD CONSTRAINT fk_vehiclestock_vehicle 
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) 
        ON UPDATE CASCADE ON DELETE CASCADE;
        RAISE NOTICE '✅ FK fk_vehiclestock_vehicle ajoutée';
    END IF;
    
    -- FK vers stock_items
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_vehiclestock_item'
    ) THEN
        ALTER TABLE vehicle_stocks 
        ADD CONSTRAINT fk_vehiclestock_item 
        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
        ON UPDATE CASCADE ON DELETE CASCADE;
        RAISE NOTICE '✅ FK fk_vehiclestock_item ajoutée';
    END IF;
    
    -- Index sur vehicle_id
    CREATE INDEX IF NOT EXISTS idx_vehiclestock_vehicle ON vehicle_stocks(vehicle_id);
    
    -- Index sur stock_item_id
    CREATE INDEX IF NOT EXISTS idx_vehiclestock_item ON vehicle_stocks(stock_item_id);
    
    -- Index composite pour les requêtes fréquentes
    CREATE INDEX IF NOT EXISTS idx_vehiclestock_vehicle_item ON vehicle_stocks(vehicle_id, stock_item_id);
END $$;

-- =========================================================
-- 7. SYNCHRONISER LES DONNÉES DEPUIS stock_movements
-- =========================================================
-- Cette fonction recalcule les stocks depuis l'historique des mouvements
DO $$
BEGIN
    RAISE NOTICE '🔄 Synchronisation des stocks depuis stock_movements...';
    
    -- Synchroniser depot_stocks depuis stock_movements
    -- Pour chaque combinaison (depot_id, stock_item_id), calculer le stock
    INSERT INTO depot_stocks (depot_id, stock_item_id, quantity, updated_at)
    SELECT 
        depot_id,
        stock_item_id,
        COALESCE(SUM(
            CASE 
                WHEN to_depot_id = depot_id THEN quantity
                WHEN from_depot_id = depot_id THEN -ABS(quantity)
                ELSE 0
            END
        ), 0) as calculated_qty,
        CURRENT_TIMESTAMP
    FROM (
        SELECT DISTINCT 
            COALESCE(to_depot_id, from_depot_id) as depot_id,
            stock_item_id
        FROM stock_movements
        WHERE to_depot_id IS NOT NULL OR from_depot_id IS NOT NULL
    ) as depot_items
    CROSS JOIN LATERAL (
        SELECT 
            SUM(
                CASE 
                    WHEN sm.to_depot_id = depot_items.depot_id THEN sm.quantity
                    WHEN sm.from_depot_id = depot_items.depot_id THEN -ABS(sm.quantity)
                    ELSE 0
                END
            ) as quantity
        FROM stock_movements sm
        WHERE (sm.to_depot_id = depot_items.depot_id OR sm.from_depot_id = depot_items.depot_id)
        AND sm.stock_item_id = depot_items.stock_item_id
    ) as calc
    GROUP BY depot_id, stock_item_id
    ON CONFLICT (depot_id, stock_item_id) 
    DO UPDATE SET 
        quantity = EXCLUDED.quantity,
        updated_at = CURRENT_TIMESTAMP;
    
    -- Méthode plus simple et plus fiable : Recalculer tous les stocks depuis zéro
    -- Supprimer les données existantes pour recalculer proprement
    DELETE FROM depot_stocks;
    
    -- Recalculer depot_stocks depuis stock_movements
    INSERT INTO depot_stocks (depot_id, stock_item_id, quantity, updated_at)
    SELECT 
        depot_id,
        stock_item_id,
        COALESCE(SUM(quantity_change), 0) as quantity,
        CURRENT_TIMESTAMP
    FROM (
        -- Entrées dans les dépôts (quantités positives)
        SELECT 
            to_depot_id as depot_id,
            stock_item_id,
            quantity as quantity_change
        FROM stock_movements
        WHERE to_depot_id IS NOT NULL
        
        UNION ALL
        
        -- Sorties des dépôts (quantités négatives)
        SELECT 
            from_depot_id as depot_id,
            stock_item_id,
            -ABS(quantity) as quantity_change
        FROM stock_movements
        WHERE from_depot_id IS NOT NULL
    ) as stock_changes
    WHERE depot_id IS NOT NULL
    GROUP BY depot_id, stock_item_id;
    
    RAISE NOTICE '✅ depot_stocks synchronisé';
    
    -- Synchroniser vehicle_stocks depuis stock_movements
    DELETE FROM vehicle_stocks;
    
    -- Recalculer vehicle_stocks depuis stock_movements
    INSERT INTO vehicle_stocks (vehicle_id, stock_item_id, quantity, updated_at)
    SELECT 
        vehicle_id,
        stock_item_id,
        COALESCE(SUM(quantity_change), 0) as quantity,
        CURRENT_TIMESTAMP
    FROM (
        -- Entrées dans les véhicules (quantités positives)
        SELECT 
            to_vehicle_id as vehicle_id,
            stock_item_id,
            quantity as quantity_change
        FROM stock_movements
        WHERE to_vehicle_id IS NOT NULL
        
        UNION ALL
        
        -- Sorties des véhicules (quantités négatives)
        SELECT 
            from_vehicle_id as vehicle_id,
            stock_item_id,
            -ABS(quantity) as quantity_change
        FROM stock_movements
        WHERE from_vehicle_id IS NOT NULL
    ) as stock_changes
    WHERE vehicle_id IS NOT NULL
    GROUP BY vehicle_id, stock_item_id;
    
    RAISE NOTICE '✅ vehicle_stocks synchronisé';
    
    RAISE NOTICE '✅ Synchronisation terminée';
END $$;

-- =========================================================
-- 8. VÉRIFICATIONS FINALES
-- =========================================================
DO $$
DECLARE
    depot_stocks_count INTEGER;
    vehicle_stocks_count INTEGER;
    depot_stocks_with_data INTEGER;
    vehicle_stocks_with_data INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VÉRIFICATIONS FINALES';
    RAISE NOTICE '========================================';
    
    -- Vérifier depot_stocks
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'depot_stocks'
    ) THEN
        SELECT COUNT(*) INTO depot_stocks_count FROM depot_stocks;
        SELECT COUNT(*) INTO depot_stocks_with_data 
        FROM depot_stocks 
        WHERE quantity > 0;
        
        RAISE NOTICE '✅ Table depot_stocks: OK';
        RAISE NOTICE '   - Total enregistrements: %', depot_stocks_count;
        RAISE NOTICE '   - Avec stock > 0: %', depot_stocks_with_data;
    ELSE
        RAISE WARNING '❌ Table depot_stocks: MANQUANTE';
    END IF;
    
    -- Vérifier vehicle_stocks
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'vehicle_stocks'
    ) THEN
        SELECT COUNT(*) INTO vehicle_stocks_count FROM vehicle_stocks;
        SELECT COUNT(*) INTO vehicle_stocks_with_data 
        FROM vehicle_stocks 
        WHERE quantity > 0;
        
        RAISE NOTICE '✅ Table vehicle_stocks: OK';
        RAISE NOTICE '   - Total enregistrements: %', vehicle_stocks_count;
        RAISE NOTICE '   - Avec stock > 0: %', vehicle_stocks_with_data;
    ELSE
        RAISE WARNING '❌ Table vehicle_stocks: MANQUANTE';
    END IF;
    
    -- Vérifier les index
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'depot_stocks' 
        AND indexname = 'idx_depotstock_depot_item'
    ) THEN
        RAISE NOTICE '✅ Index depot_stocks: OK';
    ELSE
        RAISE WARNING '❌ Index depot_stocks: MANQUANTS';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'vehicle_stocks' 
        AND indexname = 'idx_vehiclestock_vehicle_item'
    ) THEN
        RAISE NOTICE '✅ Index vehicle_stocks: OK';
    ELSE
        RAISE WARNING '❌ Index vehicle_stocks: MANQUANTS';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'CORRECTION TERMINÉE';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

