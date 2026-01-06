-- Script SQL pour ajouter de nouveaux types de rapports automatiques
-- Version PostgreSQL

-- Ajouter les nouveaux types à l'ENUM existant
DO $$ 
BEGIN
    -- Vérifier si les valeurs existent déjà
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'orders_summary' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'report_type_enum')
    ) THEN
        ALTER TYPE report_type_enum ADD VALUE 'orders_summary';
        RAISE NOTICE '✅ Type orders_summary ajouté';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'sales_statistics' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'report_type_enum')
    ) THEN
        ALTER TYPE report_type_enum ADD VALUE 'sales_statistics';
        RAISE NOTICE '✅ Type sales_statistics ajouté';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'stock_alerts' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'report_type_enum')
    ) THEN
        ALTER TYPE report_type_enum ADD VALUE 'stock_alerts';
        RAISE NOTICE '✅ Type stock_alerts ajouté';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'daily_summary' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'report_type_enum')
    ) THEN
        ALTER TYPE report_type_enum ADD VALUE 'daily_summary';
        RAISE NOTICE '✅ Type daily_summary ajouté';
    END IF;
    
    RAISE NOTICE '✅ Tous les nouveaux types de rapports ont été ajoutés avec succès';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING '⚠️ Erreur lors de l''ajout des types: %', SQLERRM;
END $$;

COMMENT ON TYPE report_type_enum IS 'Types de rapports automatiques disponibles: stock_inventory, stock_summary, orders_summary, sales_statistics, stock_alerts, daily_summary';

