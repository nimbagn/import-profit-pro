-- =========================================================
-- SCRIPT DE MIGRATION COMPLÈTE POSTGRESQL POUR RENDER
-- =========================================================
-- Date : 4 Janvier 2026
-- Description : Script complet et idempotent pour créer/mettre à jour
--                la base de données PostgreSQL avec toutes les
--                fonctionnalités du projet Import Profit Pro
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================
-- UTILISATION SUR RENDER :
-- 1. Connectez-vous à votre base PostgreSQL sur Render
-- 2. Exécutez ce script via psql ou l'interface Render
-- 3. Le script créera toutes les tables nécessaires
-- =========================================================

BEGIN;

-- =========================================================
-- 1. EXTENSIONS POSTGRESQL
-- =========================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =========================================================
-- 2. CRÉATION DES TABLES DE BASE
-- =========================================================

-- Table des rôles
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- Table des régions
CREATE TABLE IF NOT EXISTS regions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    phone VARCHAR(20),
    role_id BIGINT REFERENCES roles(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP,
    additional_permissions JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_user_region ON users(region_id);

-- Table des catégories
CREATE TABLE IF NOT EXISTS categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table des articles
CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    purchase_price DECIMAL(15,2) NOT NULL,
    purchase_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    unit_weight_kg DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    selling_price DECIMAL(15,2),
    selling_currency VARCHAR(3) DEFAULT 'GNF',
    description TEXT,
    image_path VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category_id);

-- Table des familles d'articles
CREATE TABLE IF NOT EXISTS families (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table des dépôts
CREATE TABLE IF NOT EXISTS depots (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20),
    region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    address TEXT,
    phone VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_depots_region ON depots(region_id);

-- Table des véhicules
CREATE TABLE IF NOT EXISTS vehicles (
    id BIGSERIAL PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL UNIQUE,
    brand VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    capacity_kg DECIMAL(10,2),
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicles_region ON vehicles(region_id);

-- Table des articles de stock
CREATE TABLE IF NOT EXISTS stock_items (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    family_id BIGINT REFERENCES families(id) ON DELETE SET NULL,
    unit_price_gnf DECIMAL(18,2),
    unit_weight_kg DECIMAL(10,3) DEFAULT 0.000,
    min_stock_level DECIMAL(18,4) DEFAULT 0,
    max_stock_level DECIMAL(18,4),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_items_sku ON stock_items(sku);
CREATE INDEX IF NOT EXISTS idx_stock_items_family ON stock_items(family_id);

-- Table des stocks par dépôt
CREATE TABLE IF NOT EXISTS depot_stocks (
    id BIGSERIAL PRIMARY KEY,
    depot_id BIGINT NOT NULL REFERENCES depots(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(depot_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_depot_stocks_depot ON depot_stocks(depot_id);
CREATE INDEX IF NOT EXISTS idx_depot_stocks_item ON depot_stocks(stock_item_id);

-- Table des stocks par véhicule
CREATE TABLE IF NOT EXISTS vehicle_stocks (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vehicle_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_vehicle_stocks_vehicle ON vehicle_stocks(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_stocks_item ON vehicle_stocks(stock_item_id);

-- Table des mouvements de stock
CREATE TABLE IF NOT EXISTS stock_movements (
    id BIGSERIAL PRIMARY KEY,
    movement_type VARCHAR(50) NOT NULL,
    reference VARCHAR(50),
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL,
    from_depot_id BIGINT REFERENCES depots(id) ON UPDATE CASCADE ON DELETE SET NULL,
    from_vehicle_id BIGINT REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE SET NULL,
    to_depot_id BIGINT REFERENCES depots(id) ON UPDATE CASCADE ON DELETE SET NULL,
    to_vehicle_id BIGINT REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE SET NULL,
    user_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    supplier_name VARCHAR(120),
    bl_number VARCHAR(50),
    notes TEXT,
    movement_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_item ON stock_movements(stock_item_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date);
CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference);

-- Table des réceptions
CREATE TABLE IF NOT EXISTS receptions (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    reception_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    depot_id BIGINT NOT NULL REFERENCES depots(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    supplier_name VARCHAR(120) NOT NULL,
    bl_number VARCHAR(50) NOT NULL,
    user_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reception_date ON receptions(reception_date);
CREATE INDEX IF NOT EXISTS idx_reception_depot ON receptions(depot_id);
CREATE INDEX IF NOT EXISTS idx_reception_reference ON receptions(reference);

-- Table des détails de réception
CREATE TABLE IF NOT EXISTS reception_details (
    id BIGSERIAL PRIMARY KEY,
    reception_id BIGINT NOT NULL REFERENCES receptions(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL,
    unit_price_gnf DECIMAL(18,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reception_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_receptiondetail_reception ON reception_details(reception_id);
CREATE INDEX IF NOT EXISTS idx_receptiondetail_item ON reception_details(stock_item_id);

-- Table des sorties de stock
CREATE TABLE IF NOT EXISTS stock_outgoings (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    outgoing_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    client_name VARCHAR(120) NOT NULL,
    client_phone VARCHAR(20),
    commercial_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    from_depot_id BIGINT REFERENCES depots(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    from_vehicle_id BIGINT REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    user_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outgoing_date ON stock_outgoings(outgoing_date);
CREATE INDEX IF NOT EXISTS idx_outgoing_reference ON stock_outgoings(reference);

-- Table des détails de sortie
CREATE TABLE IF NOT EXISTS stock_outgoing_details (
    id BIGSERIAL PRIMARY KEY,
    outgoing_id BIGINT NOT NULL REFERENCES stock_outgoings(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL,
    unit_price_gnf DECIMAL(18,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(outgoing_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_outgoingdetail_outgoing ON stock_outgoing_details(outgoing_id);
CREATE INDEX IF NOT EXISTS idx_outgoingdetail_item ON stock_outgoing_details(stock_item_id);

-- Table des retours de stock
CREATE TABLE IF NOT EXISTS stock_returns (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    return_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    client_name VARCHAR(120) NOT NULL,
    client_phone VARCHAR(20),
    original_outgoing_id BIGINT REFERENCES stock_outgoings(id) ON UPDATE CASCADE ON DELETE SET NULL,
    commercial_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    to_depot_id BIGINT REFERENCES depots(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    to_vehicle_id BIGINT REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    reason TEXT,
    user_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_return_date ON stock_returns(return_date);
CREATE INDEX IF NOT EXISTS idx_return_reference ON stock_returns(reference);

-- Table des détails de retour
CREATE TABLE IF NOT EXISTS stock_return_details (
    id BIGSERIAL PRIMARY KEY,
    return_id BIGINT NOT NULL REFERENCES stock_returns(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(return_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_returndetail_return ON stock_return_details(return_id);
CREATE INDEX IF NOT EXISTS idx_returndetail_item ON stock_return_details(stock_item_id);

-- Table des sessions d'inventaire
CREATE TABLE IF NOT EXISTS inventory_sessions (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    depot_id BIGINT NOT NULL REFERENCES depots(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    vehicle_id BIGINT REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE SET NULL,
    session_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_session_date ON inventory_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_inventory_session_depot ON inventory_sessions(depot_id);

-- Table des détails d'inventaire
CREATE TABLE IF NOT EXISTS inventory_details (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES inventory_sessions(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    counted_quantity DECIMAL(18,4) NOT NULL,
    system_quantity DECIMAL(18,4) NOT NULL,
    variance DECIMAL(18,4) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_inventorydetail_session ON inventory_details(session_id);
CREATE INDEX IF NOT EXISTS idx_inventorydetail_item ON inventory_details(stock_item_id);

-- Table des documents véhicule
CREATE TABLE IF NOT EXISTS vehicle_documents (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    document_number VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    file_path VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicle_documents_vehicle ON vehicle_documents(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_documents_type ON vehicle_documents(document_type);

-- Table des maintenances véhicule
CREATE TABLE IF NOT EXISTS vehicle_maintenances (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE CASCADE,
    maintenance_type VARCHAR(50) NOT NULL,
    scheduled_date DATE,
    performed_date DATE,
    cost DECIMAL(18,2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicle_maintenances_vehicle ON vehicle_maintenances(vehicle_id);

-- Table des relevés kilométriques
CREATE TABLE IF NOT EXISTS vehicle_odometers (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicles(id) ON UPDATE CASCADE ON DELETE CASCADE,
    reading_date DATE NOT NULL,
    odometer_value INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vehicle_id, reading_date)
);

CREATE INDEX IF NOT EXISTS idx_vehicle_odometers_vehicle ON vehicle_odometers(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_odometers_date ON vehicle_odometers(reading_date);

-- Table des simulations
CREATE TABLE IF NOT EXISTS simulations (
    id BIGSERIAL PRIMARY KEY,
    rate_usd DECIMAL(18,2) NOT NULL,
    rate_eur DECIMAL(18,2),
    rate_xof DECIMAL(18,2),
    customs_gnf DECIMAL(18,2) DEFAULT 0,
    handling_gnf DECIMAL(18,2) DEFAULT 0,
    transport_fixed_gnf DECIMAL(18,2) DEFAULT 0,
    transport_per_kg_gnf DECIMAL(18,2) DEFAULT 0,
    others_gnf DECIMAL(18,2) DEFAULT 0,
    basis VARCHAR(20) NOT NULL DEFAULT 'value',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table des articles de simulation
CREATE TABLE IF NOT EXISTS simulation_items (
    id BIGSERIAL PRIMARY KEY,
    simulation_id BIGINT NOT NULL REFERENCES simulations(id) ON UPDATE CASCADE ON DELETE CASCADE,
    article_id BIGINT REFERENCES articles(id) ON UPDATE CASCADE ON DELETE SET NULL,
    article_name VARCHAR(200),
    quantity DECIMAL(18,4) NOT NULL,
    purchase_price DECIMAL(18,2) NOT NULL,
    purchase_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    unit_weight_kg DECIMAL(10,3) DEFAULT 0.000,
    selling_price_gnf DECIMAL(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_simulation_items_simulation ON simulation_items(simulation_id);

-- Table des commandes commerciales
CREATE TABLE IF NOT EXISTS commercial_orders (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commercial_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    arrival_date DATE,
    region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_commercial_orders_date ON commercial_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_commercial_orders_status ON commercial_orders(status);

-- Table des clients de commande
CREATE TABLE IF NOT EXISTS commercial_order_clients (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES commercial_orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    client_id BIGINT,
    client_name VARCHAR(120) NOT NULL,
    client_phone VARCHAR(20),
    is_rejected BOOLEAN NOT NULL DEFAULT FALSE,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_clients_order ON commercial_order_clients(order_id);

-- Table des articles de commande
CREATE TABLE IF NOT EXISTS commercial_order_items (
    id BIGSERIAL PRIMARY KEY,
    order_client_id BIGINT NOT NULL REFERENCES commercial_order_clients(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL,
    unit_price_gnf DECIMAL(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_items_client ON commercial_order_items(order_client_id);
CREATE INDEX IF NOT EXISTS idx_order_items_stock ON commercial_order_items(stock_item_id);

-- Table des prévisions
CREATE TABLE IF NOT EXISTS forecasts (
    id BIGSERIAL PRIMARY KEY,
    commercial_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    period VARCHAR(50),
    start_date DATE,
    end_date DATE,
    rate_usd DECIMAL(18,2),
    rate_eur DECIMAL(18,2),
    rate_xof DECIMAL(18,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forecasts_commercial ON forecasts(commercial_id);

-- Table des articles de prévision
CREATE TABLE IF NOT EXISTS forecast_items (
    id BIGSERIAL PRIMARY KEY,
    forecast_id BIGINT NOT NULL REFERENCES forecasts(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE SET NULL,
    article_id BIGINT REFERENCES articles(id) ON UPDATE CASCADE ON DELETE SET NULL,
    forecast_quantity DECIMAL(18,4) NOT NULL,
    realized_quantity DECIMAL(18,4) DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forecast_items_forecast ON forecast_items(forecast_id);

-- Table des listes de prix
CREATE TABLE IF NOT EXISTS price_lists (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table des articles de liste de prix
CREATE TABLE IF NOT EXISTS price_list_items (
    id BIGSERIAL PRIMARY KEY,
    price_list_id BIGINT NOT NULL REFERENCES price_lists(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    unit_price_gnf DECIMAL(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(price_list_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_price_list_items_list ON price_list_items(price_list_id);
CREATE INDEX IF NOT EXISTS idx_price_list_items_stock ON price_list_items(stock_item_id);

-- Table des préférences utilisateur
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    theme VARCHAR(50) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'fr',
    preferences JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Table des tokens de réinitialisation de mot de passe
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens(user_id);

-- Table de recherche
CREATE TABLE IF NOT EXISTS search_index (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    search_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_index_type ON search_index(entity_type);
CREATE INDEX IF NOT EXISTS idx_search_index_text ON search_index USING gin(to_tsvector('french', search_text));

-- =========================================================
-- 3. INSERTION DES DONNÉES INITIALES
-- =========================================================

-- Insertion des rôles de base
INSERT INTO roles (name, description, permissions, is_active) VALUES
('admin', 'Administrateur système', '{"*": ["*"]}', TRUE),
('commercial', 'Commercial', '{"orders": ["*"], "clients": ["*"], "forecasts": ["*"]}', TRUE),
('magasinier', 'Magasinier', '{"stocks": ["*"], "receptions": ["*"], "outgoings": ["*"], "returns": ["*"], "inventories": ["*"]}', TRUE),
('supervisor', 'Superviseur', '{"stocks": ["read"], "inventory": ["read", "validate"], "vehicles": ["read", "update"], "reports": ["read"], "regions": ["read"], "depots": ["read"], "families": ["read"], "stock_items": ["read"], "promotion": ["read", "write"], "orders": ["read", "validate", "update"], "price_lists": ["view", "create", "edit", "delete"]}', TRUE),
('rh', 'Ressources Humaines', '{"rh": ["*"]}', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insertion d'une région par défaut
INSERT INTO regions (name, code) VALUES
('Région par défaut', 'REG001')
ON CONFLICT (name) DO NOTHING;

-- =========================================================
-- 4. COMMENTAIRES SUR LES TABLES
-- =========================================================

COMMENT ON TABLE roles IS 'Rôles utilisateurs avec permissions JSON';
COMMENT ON TABLE users IS 'Utilisateurs du système avec authentification';
COMMENT ON TABLE stock_items IS 'Articles de stock avec SKU unique';
COMMENT ON TABLE stock_movements IS 'Mouvements de stock (transferts, réceptions, ajustements)';
COMMENT ON TABLE receptions IS 'Réceptions de stock en dépôt';
COMMENT ON TABLE stock_outgoings IS 'Sorties de stock vers clients';
COMMENT ON TABLE stock_returns IS 'Retours de stock depuis clients';
COMMENT ON TABLE inventory_sessions IS 'Sessions d''inventaire physique';

COMMIT;

-- =========================================================
-- FIN DU SCRIPT
-- =========================================================
-- Vérification : SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
-- =========================================================

