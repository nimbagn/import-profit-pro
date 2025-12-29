-- Création de la table promotion_stock_movements pour l'historique des mouvements de stock
-- Cette table enregistre tous les mouvements de stock (superviseur, équipe, membre) avec les dates

CREATE TABLE IF NOT EXISTS promotion_stock_movements (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    movement_type VARCHAR(50) NOT NULL COMMENT 'Type: approvisionnement, distribution, enlevement, retour, affectation, reception',
    movement_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Source (d'où vient le stock)
    from_supervisor_id BIGINT UNSIGNED NULL,
    from_team_id BIGINT UNSIGNED NULL,
    from_member_id BIGINT UNSIGNED NULL,
    
    -- Destination (où va le stock)
    to_supervisor_id BIGINT UNSIGNED NULL,
    to_team_id BIGINT UNSIGNED NULL,
    to_member_id BIGINT UNSIGNED NULL,
    
    gamme_id BIGINT UNSIGNED NOT NULL,
    quantity INT NOT NULL COMMENT 'Quantité en stock après le mouvement (toujours positive)',
    quantity_change INT NOT NULL COMMENT 'Changement réel (+ ou -)',
    
    -- Référence à l'opération source
    sale_id BIGINT UNSIGNED NULL,
    return_id BIGINT UNSIGNED NULL,
    
    -- Utilisateur qui a effectué l'opération
    performed_by_id BIGINT UNSIGNED NOT NULL,
    
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (from_supervisor_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (to_supervisor_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (from_team_id) REFERENCES promotion_teams(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (to_team_id) REFERENCES promotion_teams(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (from_member_id) REFERENCES promotion_members(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (to_member_id) REFERENCES promotion_members(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (gamme_id) REFERENCES promotion_gammes(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (sale_id) REFERENCES promotion_sales(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (return_id) REFERENCES promotion_returns(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (performed_by_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    
    INDEX idx_promomovement_date (movement_date),
    INDEX idx_promomovement_type (movement_type),
    INDEX idx_promomovement_gamme (gamme_id),
    INDEX idx_promomovement_from_supervisor (from_supervisor_id),
    INDEX idx_promomovement_to_supervisor (to_supervisor_id),
    INDEX idx_promomovement_from_team (from_team_id),
    INDEX idx_promomovement_to_team (to_team_id),
    INDEX idx_promomovement_from_member (from_member_id),
    INDEX idx_promomovement_to_member (to_member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historique des mouvements de stock pour la promotion (superviseur, équipe, membre)';

