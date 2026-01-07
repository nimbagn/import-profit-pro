-- =========================================================
-- CRÉATION TABLE COMMERCIAL_CLIENTS - POSTGRESQL
-- Table pour stocker les clients des commerciaux avec géolocalisation GPS
-- =========================================================

-- Créer la table commercial_clients
CREATE TABLE IF NOT EXISTS commercial_clients (
    id BIGSERIAL PRIMARY KEY,
    commercial_id BIGINT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- Contraintes
    CONSTRAINT fk_commercialclient_commercial 
        FOREIGN KEY (commercial_id) 
        REFERENCES users(id) 
        ON UPDATE CASCADE 
        ON DELETE CASCADE,
    
    -- Un numéro de téléphone unique par commercial
    CONSTRAINT uq_commercial_phone 
        UNIQUE (commercial_id, phone)
);

-- Créer les index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_commercialclient_commercial 
    ON commercial_clients(commercial_id);

CREATE INDEX IF NOT EXISTS idx_commercialclient_phone 
    ON commercial_clients(phone);

CREATE INDEX IF NOT EXISTS idx_commercialclient_active 
    ON commercial_clients(is_active);

-- Index composite pour recherche rapide par commercial et téléphone
CREATE INDEX IF NOT EXISTS idx_commercialclient_commercial_phone 
    ON commercial_clients(commercial_id, phone) 
    WHERE is_active = TRUE;

-- Commentaires sur la table et les colonnes
COMMENT ON TABLE commercial_clients IS 'Clients des commerciaux avec géolocalisation GPS';
COMMENT ON COLUMN commercial_clients.commercial_id IS 'ID du commercial propriétaire du client';
COMMENT ON COLUMN commercial_clients.first_name IS 'Prénom du client';
COMMENT ON COLUMN commercial_clients.last_name IS 'Nom du client';
COMMENT ON COLUMN commercial_clients.phone IS 'Numéro de téléphone (indexé pour recherche rapide)';
COMMENT ON COLUMN commercial_clients.address IS 'Adresse complète du client';
COMMENT ON COLUMN commercial_clients.latitude IS 'Coordonnée GPS latitude (entre -90 et 90)';
COMMENT ON COLUMN commercial_clients.longitude IS 'Coordonnée GPS longitude (entre -180 et 180)';
COMMENT ON COLUMN commercial_clients.notes IS 'Notes supplémentaires sur le client';
COMMENT ON COLUMN commercial_clients.is_active IS 'Indique si le client est actif (soft delete)';

