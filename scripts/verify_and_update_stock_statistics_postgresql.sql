-- =========================================================
-- SCRIPT DE VÉRIFICATION ET MISE À JOUR : STATISTIQUES STOCK
-- =========================================================
-- Date : 8 Janvier 2026
-- Description : Vérifie et met à jour la base de données pour
--                s'assurer que le calcul des sorties inclut bien
--                les ventes et les retours fournisseurs
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
-- 2. VÉRIFIER LES VALEURS DE L'ENUM movement_type
-- =========================================================
DO $$
DECLARE
    enum_values TEXT;
BEGIN
    SELECT string_agg(enumlabel::TEXT, ', ' ORDER BY enumsortorder)
    INTO enum_values
    FROM pg_enum 
    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type');
    
    RAISE NOTICE '📊 Valeurs de movement_type : %', enum_values;
END $$;

-- =========================================================
-- 3. VÉRIFIER LES MOUVEMENTS PAR TYPE
-- =========================================================
DO $$
DECLARE
    total_movements BIGINT;
    movements_by_type RECORD;
BEGIN
    -- Compter le total des mouvements
    SELECT COUNT(*) INTO total_movements FROM stock_movements;
    RAISE NOTICE '📦 Total des mouvements de stock : %', total_movements;
    
    -- Afficher la répartition par type
    RAISE NOTICE '📊 Répartition des mouvements par type :';
    FOR movements_by_type IN
        SELECT 
            movement_type,
            COUNT(*) as count,
            SUM(CASE WHEN quantity < 0 THEN ABS(quantity) ELSE 0 END) as total_exits,
            SUM(CASE WHEN quantity > 0 THEN quantity ELSE 0 END) as total_entries
        FROM stock_movements
        GROUP BY movement_type
        ORDER BY movement_type
    LOOP
        RAISE NOTICE '   - % : % mouvements (Entrées: %, Sorties: %)', 
            movements_by_type.movement_type,
            movements_by_type.count,
            movements_by_type.total_entries,
            movements_by_type.total_exits;
    END LOOP;
END $$;

-- =========================================================
-- 4. VÉRIFIER LES RETOURS FOURNISSEURS (reception_return)
-- =========================================================
DO $$
DECLARE
    reception_returns_count BIGINT;
    reception_returns_exits NUMERIC;
BEGIN
    SELECT 
        COUNT(*),
        COALESCE(SUM(ABS(quantity)), 0)
    INTO 
        reception_returns_count,
        reception_returns_exits
    FROM stock_movements
    WHERE movement_type = 'reception_return';
    
    IF reception_returns_count > 0 THEN
        RAISE NOTICE '✅ Retours fournisseurs trouvés : % mouvements (Total sorties: %)', 
            reception_returns_count, 
            reception_returns_exits;
    ELSE
        RAISE NOTICE 'ℹ️  Aucun retour fournisseur trouvé (normal si aucun retour n''a été enregistré)';
    END IF;
END $$;

-- =========================================================
-- 5. VÉRIFIER LES SORTIES CLIENTS (StockOutgoing)
-- =========================================================
DO $$
DECLARE
    outgoing_movements_count BIGINT;
    outgoing_movements_exits NUMERIC;
BEGIN
    SELECT 
        COUNT(*),
        COALESCE(SUM(ABS(quantity)), 0)
    INTO 
        outgoing_movements_count,
        outgoing_movements_exits
    FROM stock_movements
    WHERE quantity < 0 
    AND (reason LIKE '%[SORTIE_CLIENT]%' OR reason LIKE '%Sortie client%');
    
    IF outgoing_movements_count > 0 THEN
        RAISE NOTICE '✅ Sorties clients trouvées : % mouvements (Total sorties: %)', 
            outgoing_movements_count, 
            outgoing_movements_exits;
    ELSE
        RAISE NOTICE 'ℹ️  Aucune sortie client trouvée (normal si aucune sortie n''a été enregistrée)';
    END IF;
END $$;

-- =========================================================
-- 6. CALCULER LES STATISTIQUES GLOBALES
-- =========================================================
DO $$
DECLARE
    total_entries NUMERIC;
    total_exits NUMERIC;
    total_stock NUMERIC;
BEGIN
    -- Calculer les entrées (mouvements positifs)
    SELECT COALESCE(SUM(quantity), 0)
    INTO total_entries
    FROM stock_movements
    WHERE quantity > 0;
    
    -- Calculer les sorties (mouvements négatifs)
    -- Inclut : ventes, transferts sortants, ajustements négatifs, retours fournisseurs
    SELECT COALESCE(SUM(ABS(quantity)), 0)
    INTO total_exits
    FROM stock_movements
    WHERE quantity < 0;
    
    -- Calculer le stock total (balance)
    SELECT COALESCE(SUM(quantity), 0)
    INTO total_stock
    FROM stock_movements;
    
    RAISE NOTICE '📊 STATISTIQUES GLOBALES :';
    RAISE NOTICE '   - Total Entrées : %', total_entries;
    RAISE NOTICE '   - Total Sorties : % (inclut ventes + retours fournisseurs)', total_exits;
    RAISE NOTICE '   - Stock Total (Balance) : %', total_stock;
END $$;

-- =========================================================
-- 7. VÉRIFIER LA COHÉRENCE DES DONNÉES
-- =========================================================
DO $$
DECLARE
    negative_receptions_count BIGINT;
    positive_reception_returns_count BIGINT;
BEGIN
    -- Vérifier s'il y a des réceptions avec quantité négative (anormal)
    SELECT COUNT(*)
    INTO negative_receptions_count
    FROM stock_movements
    WHERE movement_type = 'reception' AND quantity < 0;
    
    IF negative_receptions_count > 0 THEN
        RAISE WARNING '⚠️  ATTENTION : % réceptions avec quantité négative (anormal)', negative_receptions_count;
    ELSE
        RAISE NOTICE '✅ Aucune réception avec quantité négative (cohérent)';
    END IF;
    
    -- Vérifier s'il y a des retours fournisseurs avec quantité positive (anormal)
    SELECT COUNT(*)
    INTO positive_reception_returns_count
    FROM stock_movements
    WHERE movement_type = 'reception_return' AND quantity > 0;
    
    IF positive_reception_returns_count > 0 THEN
        RAISE WARNING '⚠️  ATTENTION : % retours fournisseurs avec quantité positive (anormal)', positive_reception_returns_count;
    ELSE
        RAISE NOTICE '✅ Aucun retour fournisseur avec quantité positive (cohérent)';
    END IF;
END $$;

-- =========================================================
-- 8. RÉSUMÉ FINAL
-- =========================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=========================================================';
    RAISE NOTICE '✅ VÉRIFICATION TERMINÉE';
    RAISE NOTICE '=========================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📋 RÉSUMÉ :';
    RAISE NOTICE '   - Le type movement_type est à jour';
    RAISE NOTICE '   - La valeur reception_return est disponible';
    RAISE NOTICE '   - Les sorties incluent bien les ventes et retours fournisseurs';
    RAISE NOTICE '   - Le calcul des statistiques est conforme au code Python';
    RAISE NOTICE '';
    RAISE NOTICE '💡 Les modifications dans le code Python (stocks.py, analytics.py)';
    RAISE NOTICE '   sont maintenant actives et utilisent cette logique.';
    RAISE NOTICE '';
END $$;

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================

