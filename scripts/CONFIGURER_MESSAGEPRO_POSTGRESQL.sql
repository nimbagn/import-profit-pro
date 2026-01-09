-- =========================================================
-- Script pour Configurer Message Pro dans PostgreSQL
-- =========================================================
-- Date : 2026-01-09
-- Description : Crée la table api_configs si elle n'existe pas
--               et configure Message Pro
-- Compatible PostgreSQL
-- =========================================================

BEGIN;

-- Créer la table api_configs si elle n'existe pas
CREATE TABLE IF NOT EXISTS api_configs (
    id BIGSERIAL PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL UNIQUE,
    api_secret TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    updated_by_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- Créer les index
CREATE INDEX IF NOT EXISTS idx_apiconfig_name ON api_configs(api_name);
CREATE INDEX IF NOT EXISTS idx_apiconfig_active ON api_configs(is_active);

-- Insérer ou mettre à jour la configuration Message Pro
-- ⚠️ REMPLACEZ 'VOTRE_CLE_API_ICI' par votre vraie clé API
INSERT INTO api_configs (api_name, api_secret, is_active, created_at)
VALUES ('messagepro', 'VOTRE_CLE_API_ICI', TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (api_name) 
DO UPDATE SET 
    api_secret = EXCLUDED.api_secret,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Vérification
SELECT 
    api_name,
    CASE 
        WHEN api_secret IS NOT NULL THEN '✅ Configuré'
        ELSE '❌ Non configuré'
    END as status,
    is_active,
    created_at,
    updated_at
FROM api_configs
WHERE api_name = 'messagepro';

COMMIT;

-- =========================================================
-- INSTRUCTIONS :
-- =========================================================
-- 1. Remplacez 'VOTRE_CLE_API_ICI' par votre vraie clé API
-- 2. Exécutez ce script dans votre base de données PostgreSQL
-- 3. Vérifiez le résultat avec la requête SELECT ci-dessus
-- 4. Testez la configuration via l'interface web : /messaging/config
-- =========================================================

