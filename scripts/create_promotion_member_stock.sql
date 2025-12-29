-- Création de la table promotion_member_stock pour le suivi du stock individuel de chaque membre
-- Cette table permet de suivre les quantités de gammes détenues par chaque membre

CREATE TABLE IF NOT EXISTS promotion_member_stock (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id BIGINT UNSIGNED NOT NULL,
    gamme_id BIGINT UNSIGNED NOT NULL,
    quantity INT NOT NULL DEFAULT 0 COMMENT 'Quantité en stock actuelle',
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (member_id) REFERENCES promotion_members(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (gamme_id) REFERENCES promotion_gammes(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY uq_member_gamme_stock (member_id, gamme_id),
    INDEX idx_promostock_member (member_id),
    INDEX idx_promostock_gamme (gamme_id),
    INDEX idx_promostock_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Stock de gammes détenu par chaque membre de l''équipe promotion';

