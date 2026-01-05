-- Script SQL pour créer la table api_configs (PostgreSQL)
-- Cette table stocke les configurations des APIs externes (Message Pro, etc.)

-- Créer la table api_configs
CREATE TABLE IF NOT EXISTS api_configs (
    id BIGSERIAL PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL UNIQUE,
    api_secret TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    updated_by_id BIGINT
);

-- Créer les index
CREATE INDEX IF NOT EXISTS idx_apiconfig_name ON api_configs(api_name);
CREATE INDEX IF NOT EXISTS idx_apiconfig_active ON api_configs(is_active);

-- Ajouter la contrainte de clé étrangère pour updated_by_id
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE api_configs 
        ADD CONSTRAINT fk_apiconfig_updated_by 
        FOREIGN KEY (updated_by_id) 
        REFERENCES users(id) 
        ON UPDATE CASCADE 
        ON DELETE SET NULL;
        RAISE NOTICE '✅ Contrainte FK updated_by_id ajoutée';
    ELSE
        RAISE WARNING '⚠️ Table users n''existe pas encore, contrainte FK updated_by_id ignorée';
    END IF;
END $$;

-- Commentaires
COMMENT ON TABLE api_configs IS 'Configuration des APIs externes (Message Pro, etc.)';
COMMENT ON COLUMN api_configs.api_name IS 'Nom de l''API (ex: messagepro)';
COMMENT ON COLUMN api_configs.api_secret IS 'Clé secrète de l''API';
COMMENT ON COLUMN api_configs.is_active IS 'Indique si la configuration est active';
COMMENT ON COLUMN api_configs.updated_by_id IS 'ID de l''utilisateur qui a effectué la dernière mise à jour';

