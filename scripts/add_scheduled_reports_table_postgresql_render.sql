-- =========================================================
-- SCRIPT POSTGRESQL POUR RENDER
-- Création de la table scheduled_reports pour les rapports automatiques
-- =========================================================
-- Ce script est idempotent : peut être exécuté plusieurs fois sans erreur
-- Compatible PostgreSQL 12+

-- =========================================================
-- 1. CRÉATION DES TYPES ENUM
-- =========================================================

DO $$ BEGIN
    CREATE TYPE report_type_enum AS ENUM ('stock_inventory', 'stock_summary', 'order_summary');
EXCEPTION
    WHEN duplicate_object THEN 
        RAISE NOTICE 'Type report_type_enum existe déjà';
END $$;

DO $$ BEGIN
    CREATE TYPE schedule_type_enum AS ENUM ('daily', 'weekly', 'monthly');
EXCEPTION
    WHEN duplicate_object THEN 
        RAISE NOTICE 'Type schedule_type_enum existe déjà';
END $$;

-- =========================================================
-- 2. CRÉATION DE LA TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS scheduled_reports (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    report_type report_type_enum NOT NULL,
    schedule_type schedule_type_enum NOT NULL DEFAULT 'daily',
    schedule VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Paramètres du rapport
    depot_id BIGINT NULL,
    period VARCHAR(50) DEFAULT 'all',
    start_date DATE NULL,
    end_date DATE NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'GNF',
    
    -- Destinataires WhatsApp
    whatsapp_account_id VARCHAR(100) NOT NULL,
    recipients TEXT NULL,
    group_ids TEXT NULL,
    message TEXT NULL,
    
    -- Suivi d'exécution
    last_run TIMESTAMP WITH TIME ZONE NULL,
    next_run TIMESTAMP WITH TIME ZONE NULL,
    run_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NULL,
    
    -- Métadonnées
    created_by_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NULL
);

-- =========================================================
-- 3. CRÉATION DES INDEX
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_scheduledreport_type ON scheduled_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_scheduledreport_active ON scheduled_reports(is_active);
CREATE INDEX IF NOT EXISTS idx_scheduledreport_nextrun ON scheduled_reports(next_run);
CREATE INDEX IF NOT EXISTS idx_scheduledreport_depot ON scheduled_reports(depot_id);
CREATE INDEX IF NOT EXISTS idx_scheduledreport_created_by ON scheduled_reports(created_by_id);

-- =========================================================
-- 4. CONTRAINTES DE CLÉS ÉTRANGÈRES
-- =========================================================

-- Supprimer la contrainte si elle existe déjà
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_scheduledreport_depot' 
        AND table_name = 'scheduled_reports'
    ) THEN
        ALTER TABLE scheduled_reports DROP CONSTRAINT fk_scheduledreport_depot;
    END IF;
END $$;

-- Ajouter la contrainte pour depot_id
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'depots') THEN
        ALTER TABLE scheduled_reports 
        ADD CONSTRAINT fk_scheduledreport_depot 
        FOREIGN KEY (depot_id) 
        REFERENCES depots(id) 
        ON UPDATE CASCADE 
        ON DELETE SET NULL;
        RAISE NOTICE '✅ Contrainte FK depot_id ajoutée';
    ELSE
        RAISE WARNING '⚠️ Table depots n''existe pas encore, contrainte FK depot_id ignorée';
    END IF;
END $$;

-- Supprimer la contrainte si elle existe déjà
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_scheduledreport_created_by' 
        AND table_name = 'scheduled_reports'
    ) THEN
        ALTER TABLE scheduled_reports DROP CONSTRAINT fk_scheduledreport_created_by;
    END IF;
END $$;

-- Ajouter la contrainte pour created_by_id
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE scheduled_reports 
        ADD CONSTRAINT fk_scheduledreport_created_by 
        FOREIGN KEY (created_by_id) 
        REFERENCES users(id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT;
        RAISE NOTICE '✅ Contrainte FK created_by_id ajoutée';
    ELSE
        RAISE WARNING '⚠️ Table users n''existe pas encore, contrainte FK created_by_id ignorée';
    END IF;
END $$;

-- =========================================================
-- 5. COMMENTAIRES
-- =========================================================

COMMENT ON TABLE scheduled_reports IS 'Configuration des rapports automatiques à envoyer via WhatsApp';
COMMENT ON COLUMN scheduled_reports.name IS 'Nom descriptif du rapport';
COMMENT ON COLUMN scheduled_reports.report_type IS 'Type de rapport: stock_inventory, stock_summary, order_summary';
COMMENT ON COLUMN scheduled_reports.schedule_type IS 'Fréquence: daily, weekly, monthly';
COMMENT ON COLUMN scheduled_reports.schedule IS 'Format: "HH:MM" pour daily, "DAY HH:MM" pour weekly, "DD HH:MM" pour monthly';
COMMENT ON COLUMN scheduled_reports.period IS 'Période: all, today, week, month, year, custom';
COMMENT ON COLUMN scheduled_reports.recipients IS 'Numéros de téléphone séparés par des virgules';
COMMENT ON COLUMN scheduled_reports.group_ids IS 'IDs de groupes Message Pro séparés par des virgules';
COMMENT ON COLUMN scheduled_reports.last_run IS 'Date et heure de la dernière exécution';
COMMENT ON COLUMN scheduled_reports.next_run IS 'Date et heure de la prochaine exécution';
COMMENT ON COLUMN scheduled_reports.run_count IS 'Nombre total d''exécutions réussies';
COMMENT ON COLUMN scheduled_reports.last_error IS 'Message de la dernière erreur (si applicable)';

-- =========================================================
-- 6. VÉRIFICATION
-- =========================================================

DO $$ 
DECLARE
    table_exists BOOLEAN;
    row_count INTEGER;
BEGIN
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'scheduled_reports'
    ) INTO table_exists;
    
    IF table_exists THEN
        SELECT COUNT(*) INTO row_count FROM scheduled_reports;
        RAISE NOTICE '✅ Table scheduled_reports créée avec succès';
        RAISE NOTICE '📊 Nombre de rapports configurés: %', row_count;
    ELSE
        RAISE WARNING '❌ Table scheduled_reports n''a pas pu être créée';
    END IF;
END $$;

-- Afficher la structure de la table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'scheduled_reports'
ORDER BY ordinal_position;

