-- Script SQL pour créer la table scheduled_reports
-- Compatible MySQL et PostgreSQL

-- Pour MySQL
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    report_type ENUM('stock_inventory', 'stock_summary', 'order_summary') NOT NULL,
    schedule_type ENUM('daily', 'weekly', 'monthly') NOT NULL DEFAULT 'daily',
    schedule VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Paramètres du rapport
    depot_id BIGINT UNSIGNED NULL,
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
    last_run DATETIME NULL,
    next_run DATETIME NULL,
    run_count INT NOT NULL DEFAULT 0,
    last_error TEXT NULL,
    
    -- Métadonnées
    created_by_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_scheduledreport_type (report_type),
    INDEX idx_scheduledreport_active (is_active),
    INDEX idx_scheduledreport_nextrun (next_run),
    
    FOREIGN KEY (depot_id) REFERENCES depots(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

