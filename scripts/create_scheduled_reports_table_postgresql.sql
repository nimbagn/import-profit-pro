-- Script SQL pour créer la table scheduled_reports
-- Version PostgreSQL

-- Créer les types ENUM si nécessaire
DO $$ BEGIN
    CREATE TYPE report_type_enum AS ENUM ('stock_inventory', 'stock_summary', 'order_summary');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE schedule_type_enum AS ENUM ('daily', 'weekly', 'monthly');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Créer la table
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
    updated_at TIMESTAMP WITH TIME ZONE NULL,
    
    CONSTRAINT fk_scheduledreport_depot FOREIGN KEY (depot_id) REFERENCES depots(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_scheduledreport_created_by FOREIGN KEY (created_by_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Créer les index
CREATE INDEX IF NOT EXISTS idx_scheduledreport_type ON scheduled_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_scheduledreport_active ON scheduled_reports(is_active);
CREATE INDEX IF NOT EXISTS idx_scheduledreport_nextrun ON scheduled_reports(next_run);

-- Commentaires
COMMENT ON TABLE scheduled_reports IS 'Configuration des rapports automatiques à envoyer via WhatsApp';
COMMENT ON COLUMN scheduled_reports.schedule IS 'Format: "HH:MM" pour daily, "DAY HH:MM" pour weekly, "DD HH:MM" pour monthly';
COMMENT ON COLUMN scheduled_reports.recipients IS 'Numéros séparés par des virgules';
COMMENT ON COLUMN scheduled_reports.group_ids IS 'IDs de groupes Message Pro séparés par des virgules';

