-- Script pour ajouter les fonctionnalités de cartographie au module promotion
-- Ajouter la colonne region à promotion_teams
ALTER TABLE promotion_teams 
ADD COLUMN region VARCHAR(100) NULL AFTER description;

-- Créer un index sur la colonne region
CREATE INDEX idx_promoteam_region ON promotion_teams(region);

-- Créer la table promotion_member_locations pour le suivi des déplacements
CREATE TABLE IF NOT EXISTS promotion_member_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    latitude DECIMAL(18,4) NOT NULL,
    longitude DECIMAL(18,4) NOT NULL,
    address VARCHAR(500) NULL,
    activity_type VARCHAR(50) NULL,
    notes TEXT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recorded_by_id INT NULL,
    FOREIGN KEY (member_id) REFERENCES promotion_members(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (recorded_by_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_promoloc_member (member_id),
    INDEX idx_promoloc_recorded (recorded_at),
    INDEX idx_promoloc_coords (latitude, longitude),
    INDEX idx_promoloc_activity (activity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

