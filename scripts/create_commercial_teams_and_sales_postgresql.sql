-- =========================================================
-- SCRIPT DE MIGRATION : ÉQUIPES COMMERCIALES ET CONFIRMATION DES VENTES
-- =========================================================
-- Date : 2026-01-03
-- Description : Création des tables pour la gestion des équipes commerciales
--               (lockistes, vendeurs) et le système de confirmation des ventes
-- Compatible PostgreSQL
-- =========================================================
-- IMPORTANT : Exécutez ce script dans votre base de données PostgreSQL
-- Ce script est idempotent et peut être exécuté plusieurs fois
-- =========================================================

BEGIN;

-- =========================================================
-- 1. MODIFICATIONS TABLE USERS
-- =========================================================

-- Ajouter colonnes pour la supervision d'équipes
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'supervised_team_id'
    ) THEN
        ALTER TABLE users ADD COLUMN supervised_team_id BIGINT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'supervised_team_type'
    ) THEN
        ALTER TABLE users ADD COLUMN supervised_team_type VARCHAR(20);
    END IF;
END $$;

-- Créer index pour supervised_team_id
CREATE INDEX IF NOT EXISTS idx_users_supervised_team ON users(supervised_team_id);

-- =========================================================
-- 2. MODIFICATIONS TABLE PROMOTION_TEAMS
-- =========================================================

-- Ajouter colonne supervisor_id à promotion_teams
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_teams' AND column_name = 'supervisor_id'
    ) THEN
        ALTER TABLE promotion_teams ADD COLUMN supervisor_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_promoteam_supervisor ON promotion_teams(supervisor_id);
    END IF;
    
    -- Ajouter region_id si elle n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_teams' AND column_name = 'region_id'
    ) THEN
        ALTER TABLE promotion_teams ADD COLUMN region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_promoteam_region_id ON promotion_teams(region_id);
    END IF;
END $$;

-- =========================================================
-- 2.5. MODIFICATIONS TABLE PROMOTION_MEMBERS
-- =========================================================

-- Ajouter colonnes de géolocalisation
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_members' AND column_name = 'home_latitude'
    ) THEN
        ALTER TABLE promotion_members ADD COLUMN home_latitude DECIMAL(18,4);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_members' AND column_name = 'home_longitude'
    ) THEN
        ALTER TABLE promotion_members ADD COLUMN home_longitude DECIMAL(18,4);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_members' AND column_name = 'intermediaire_id'
    ) THEN
        ALTER TABLE promotion_members ADD COLUMN intermediaire_id BIGINT REFERENCES promotion_members(id) ON UPDATE CASCADE ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_promomember_intermediary ON promotion_members(intermediaire_id);
    END IF;
END $$;

-- Créer index pour géolocalisation
CREATE INDEX IF NOT EXISTS idx_promomember_location ON promotion_members(home_latitude, home_longitude);

-- =========================================================
-- 3. TABLES ÉQUIPES LOCKISTES
-- =========================================================

-- Table des équipes lockistes
CREATE TABLE IF NOT EXISTS lockiste_teams (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    team_leader_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    supervisor_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lockiste_team_name ON lockiste_teams(name);
CREATE INDEX IF NOT EXISTS idx_lockiste_team_leader ON lockiste_teams(team_leader_id);
CREATE INDEX IF NOT EXISTS idx_lockiste_team_supervisor ON lockiste_teams(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_lockiste_team_region ON lockiste_teams(region_id);
CREATE INDEX IF NOT EXISTS idx_lockiste_team_active ON lockiste_teams(is_active);

-- Table des membres lockistes
CREATE TABLE IF NOT EXISTS lockiste_members (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES lockiste_teams(id) ON UPDATE CASCADE ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lockiste_member_team ON lockiste_members(team_id);
CREATE INDEX IF NOT EXISTS idx_lockiste_member_user ON lockiste_members(user_id);
CREATE INDEX IF NOT EXISTS idx_lockiste_member_name ON lockiste_members(full_name);
CREATE INDEX IF NOT EXISTS idx_lockiste_member_phone ON lockiste_members(phone);
CREATE INDEX IF NOT EXISTS idx_lockiste_member_active ON lockiste_members(is_active);

-- =========================================================
-- 4. TABLES ÉQUIPES VANDEURS
-- =========================================================

-- Table des équipes vendeurs
CREATE TABLE IF NOT EXISTS vendeur_teams (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
    team_leader_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    supervisor_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vendeur_team_name ON vendeur_teams(name);
CREATE INDEX IF NOT EXISTS idx_vendeur_team_leader ON vendeur_teams(team_leader_id);
CREATE INDEX IF NOT EXISTS idx_vendeur_team_supervisor ON vendeur_teams(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_vendeur_team_region ON vendeur_teams(region_id);
CREATE INDEX IF NOT EXISTS idx_vendeur_team_active ON vendeur_teams(is_active);

-- Table des membres vendeurs
CREATE TABLE IF NOT EXISTS vendeur_members (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES vendeur_teams(id) ON UPDATE CASCADE ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vendeur_member_team ON vendeur_members(team_id);
CREATE INDEX IF NOT EXISTS idx_vendeur_member_user ON vendeur_members(user_id);
CREATE INDEX IF NOT EXISTS idx_vendeur_member_name ON vendeur_members(full_name);
CREATE INDEX IF NOT EXISTS idx_vendeur_member_phone ON vendeur_members(phone);
CREATE INDEX IF NOT EXISTS idx_vendeur_member_active ON vendeur_members(is_active);

-- =========================================================
-- 5. MODIFICATIONS TABLE COMMERCIAL_ORDERS
-- =========================================================

-- Ajouter colonnes pour la confirmation de vente
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'commercial_orders' AND column_name = 'sale_confirmed'
    ) THEN
        ALTER TABLE commercial_orders ADD COLUMN sale_confirmed BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'commercial_orders' AND column_name = 'sale_confirmed_at'
    ) THEN
        ALTER TABLE commercial_orders ADD COLUMN sale_confirmed_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'commercial_orders' AND column_name = 'sale_confirmed_by_id'
    ) THEN
        ALTER TABLE commercial_orders ADD COLUMN sale_confirmed_by_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_order_sale_confirmed_by ON commercial_orders(sale_confirmed_by_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_order_sale_confirmed ON commercial_orders(sale_confirmed);

-- =========================================================
-- 6. TABLE COMMERCIAL_SALES (VENTES FINALES CONFIRMÉES)
-- =========================================================

CREATE TABLE IF NOT EXISTS commercial_sales (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES commercial_orders(id) ON UPDATE CASCADE ON DELETE SET NULL,
    order_client_id BIGINT REFERENCES commercial_order_clients(id) ON UPDATE CASCADE ON DELETE SET NULL,
    commercial_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    supervisor_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    invoice_number VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL,
    sale_date DATE NOT NULL,
    total_amount_gnf DECIMAL(18,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL DEFAULT 'cash',
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_due_date DATE,
    confirmed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_commercial_sale_order ON commercial_sales(order_id);
CREATE INDEX IF NOT EXISTS idx_commercial_sale_commercial ON commercial_sales(commercial_id);
CREATE INDEX IF NOT EXISTS idx_commercial_sale_supervisor ON commercial_sales(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_commercial_sale_date ON commercial_sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_commercial_sale_invoice ON commercial_sales(invoice_number);
CREATE INDEX IF NOT EXISTS idx_commercial_sale_status ON commercial_sales(status);
CREATE INDEX IF NOT EXISTS idx_commercial_sale_payment_status ON commercial_sales(payment_status);

-- =========================================================
-- 7. TABLE COMMERCIAL_SALE_ITEMS (DÉTAILS DES VENTES)
-- =========================================================

CREATE TABLE IF NOT EXISTS commercial_sale_items (
    id BIGSERIAL PRIMARY KEY,
    sale_id BIGINT NOT NULL REFERENCES commercial_sales(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity DECIMAL(18,4) NOT NULL,
    unit_price_gnf DECIMAL(18,2) NOT NULL,
    total_price_gnf DECIMAL(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sale_item_sale ON commercial_sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_item_stock ON commercial_sale_items(stock_item_id);

-- =========================================================
-- 8. TABLE SALES_OBJECTIVES (OBJECTIFS DE VENTE)
-- =========================================================

CREATE TABLE IF NOT EXISTS sales_objectives (
    id BIGSERIAL PRIMARY KEY,
    commercial_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    supervisor_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    target_amount_gnf DECIMAL(18,2) NOT NULL,
    target_quantity DECIMAL(18,4),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_objective_commercial ON sales_objectives(commercial_id);
CREATE INDEX IF NOT EXISTS idx_objective_supervisor ON sales_objectives(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_objective_period ON sales_objectives(period_start, period_end);

-- Ajouter colonne forecast_id si la table existe déjà
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sales_objectives' AND column_name = 'forecast_id'
    ) THEN
        ALTER TABLE sales_objectives ADD COLUMN forecast_id BIGINT REFERENCES forecasts(id) ON UPDATE CASCADE ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_objective_forecast ON sales_objectives(forecast_id);
    END IF;
END $$;

-- =========================================================
-- 9. TABLE SALES_OBJECTIVE_ITEMS (ARTICLES DES OBJECTIFS)
-- =========================================================

CREATE TABLE IF NOT EXISTS sales_objective_items (
    id BIGSERIAL PRIMARY KEY,
    objective_id BIGINT NOT NULL REFERENCES sales_objectives(id) ON UPDATE CASCADE ON DELETE CASCADE,
    stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    target_quantity DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    selling_price_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE (objective_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS idx_objectiveitem_objective ON sales_objective_items(objective_id);
CREATE INDEX IF NOT EXISTS idx_objectiveitem_stock ON sales_objective_items(stock_item_id);

COMMIT;

-- =========================================================
-- FIN DU SCRIPT DE MIGRATION
-- =========================================================

