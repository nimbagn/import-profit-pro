-- Création de la table promotion_team_stock pour le suivi du stock au niveau de l'équipe
-- Cette table permet de suivre les quantités de gammes détenues par chaque équipe
-- Les membres reçoivent ensuite leur stock depuis le stock de l'équipe

CREATE TABLE IF NOT EXISTS promotion_team_stock (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    team_id BIGINT UNSIGNED NOT NULL,
    gamme_id BIGINT UNSIGNED NOT NULL,
    quantity INT NOT NULL DEFAULT 0 COMMENT 'Quantité en stock actuelle',
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES promotion_teams(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (gamme_id) REFERENCES promotion_gammes(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    UNIQUE KEY uq_team_gamme_stock (team_id, gamme_id),
    INDEX idx_promoteamstock_team (team_id),
    INDEX idx_promoteamstock_gamme (gamme_id),
    INDEX idx_promoteamstock_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Stock de gammes détenu par chaque équipe de promotion';

