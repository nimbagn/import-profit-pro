-- Création de la table promotion_daily_closures pour la clôture quotidienne des opérations
-- Cette table permet de marquer qu'une journée a été clôturée et de conserver un historique

CREATE TABLE IF NOT EXISTS promotion_daily_closures (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    closure_date DATE NOT NULL UNIQUE COMMENT 'Date de clôture (une seule clôture par jour)',
    closed_by_id BIGINT UNSIGNED NOT NULL COMMENT 'Utilisateur qui a effectué la clôture',
    closed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date et heure de la clôture',
    notes TEXT NULL COMMENT 'Notes ou commentaires sur la journée',
    
    FOREIGN KEY (closed_by_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    
    INDEX idx_closure_date (closure_date),
    INDEX idx_closure_closed_by (closed_by_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Clôture quotidienne des opérations de promotion';

