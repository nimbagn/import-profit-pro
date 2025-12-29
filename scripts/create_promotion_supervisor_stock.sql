-- Création de la table promotion_supervisor_stock pour le suivi du stock central du superviseur
-- Cette table permet de suivre les quantités de gammes détenues par le superviseur/responsable promotion
-- Le stock du superviseur diminue lorsqu'il approvisionne une équipe

CREATE TABLE IF NOT EXISTS promotion_supervisor_stock (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    supervisor_id BIGINT UNSIGNED NOT NULL,
    gamme_id BIGINT UNSIGNED NOT NULL,
    quantity INT NOT NULL DEFAULT 0 COMMENT 'Quantité en stock actuelle',
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (supervisor_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (gamme_id) REFERENCES promotion_gammes(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY uq_supervisor_gamme_stock (supervisor_id, gamme_id),
    INDEX idx_promosupervisorstock_supervisor (supervisor_id),
    INDEX idx_promosupervisorstock_gamme (gamme_id),
    INDEX idx_promosupervisorstock_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Stock central de gammes détenu par le superviseur/responsable promotion';

