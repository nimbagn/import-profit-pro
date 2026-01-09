-- =========================================================
-- SCRIPT DE MIGRATION COMPLÈTE POUR PRODUCTION
-- Compatible PostgreSQL (Render, Heroku, etc.)
-- =========================================================
-- Date : 2026-01-03
-- Description : Migration complète de toutes les fonctionnalités
--               - Permissions flotte pour magasinier
--               - Système de supervision commerciale
--               - Notifications automatiques
-- =========================================================
-- IMPORTANT : Exécutez ce script dans votre base de données PostgreSQL de production
-- Ce script est idempotent et peut être exécuté plusieurs fois
-- =========================================================

BEGIN;

-- =========================================================
-- 1. PERMISSIONS FLOTTE POUR MAGASINIER
-- =========================================================

DO $$ 
DECLARE
    warehouse_permissions JSONB;
    vehicles_perms JSONB;
BEGIN
    -- Récupérer les permissions actuelles du magasinier
    SELECT permissions INTO warehouse_permissions
    FROM roles
    WHERE code = 'warehouse';
    
    -- Si le rôle existe
    IF warehouse_permissions IS NOT NULL THEN
        -- Récupérer les permissions véhicules actuelles
        vehicles_perms := warehouse_permissions->'vehicles';
        
        -- Si les permissions véhicules existent
        IF vehicles_perms IS NOT NULL THEN
            -- Vérifier si 'create' est déjà présent
            IF NOT (vehicles_perms ? 'create' OR vehicles_perms @> '["create"]'::jsonb) THEN
                -- Ajouter 'create' aux permissions existantes
                warehouse_permissions := jsonb_set(
                    warehouse_permissions,
                    '{vehicles}',
                    vehicles_perms || '["create"]'::jsonb
                );
                
                UPDATE roles
                SET permissions = warehouse_permissions
                WHERE code = 'warehouse';
                
                RAISE NOTICE 'Permission "create" ajoutée pour vehicles au rôle warehouse';
            ELSE
                RAISE NOTICE 'Permission "create" déjà présente pour vehicles au rôle warehouse';
            END IF;
        ELSE
            -- Créer les permissions véhicules avec read, create, update
            warehouse_permissions := jsonb_set(
                warehouse_permissions,
                '{vehicles}',
                '["read", "create", "update"]'::jsonb
            );
            
            UPDATE roles
            SET permissions = warehouse_permissions
            WHERE code = 'warehouse';
            
            RAISE NOTICE 'Permissions vehicles créées pour le rôle warehouse';
        END IF;
    ELSE
        RAISE WARNING 'Rôle warehouse non trouvé';
    END IF;
END $$;

-- =========================================================
-- 2. SYSTÈME DE SUPERVISION COMMERCIALE ET CONFIRMATION DES VENTES
-- =========================================================

-- Vérifier et créer les colonnes dans users
DO $$ 
BEGIN
    -- Colonne supervised_team_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'supervised_team_id'
    ) THEN
        ALTER TABLE users ADD COLUMN supervised_team_id BIGINT;
        RAISE NOTICE 'Colonne supervised_team_id ajoutée à users';
    END IF;
    
    -- Colonne supervised_team_type
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'supervised_team_type'
    ) THEN
        ALTER TABLE users ADD COLUMN supervised_team_type VARCHAR(50);
        RAISE NOTICE 'Colonne supervised_team_type ajoutée à users';
    END IF;
END $$;

-- Vérifier et créer les colonnes dans promotion_teams
DO $$ 
BEGIN
    -- Colonne supervisor_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_teams' AND column_name = 'supervisor_id'
    ) THEN
        ALTER TABLE promotion_teams ADD COLUMN supervisor_id BIGINT;
        RAISE NOTICE 'Colonne supervisor_id ajoutée à promotion_teams';
    END IF;
    
    -- Colonne region_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_teams' AND column_name = 'region_id'
    ) THEN
        ALTER TABLE promotion_teams ADD COLUMN region_id BIGINT;
        RAISE NOTICE 'Colonne region_id ajoutée à promotion_teams';
    END IF;
END $$;

-- Vérifier et créer les colonnes dans promotion_members
DO $$ 
BEGIN
    -- Colonne home_latitude
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_members' AND column_name = 'home_latitude'
    ) THEN
        ALTER TABLE promotion_members ADD COLUMN home_latitude DECIMAL(10, 8);
        RAISE NOTICE 'Colonne home_latitude ajoutée à promotion_members';
    END IF;
    
    -- Colonne home_longitude
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_members' AND column_name = 'home_longitude'
    ) THEN
        ALTER TABLE promotion_members ADD COLUMN home_longitude DECIMAL(11, 8);
        RAISE NOTICE 'Colonne home_longitude ajoutée à promotion_members';
    END IF;
    
    -- Colonne intermediaire_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'promotion_members' AND column_name = 'intermediaire_id'
    ) THEN
        ALTER TABLE promotion_members ADD COLUMN intermediaire_id BIGINT;
        RAISE NOTICE 'Colonne intermediaire_id ajoutée à promotion_members';
    END IF;
END $$;

-- Vérifier et créer les colonnes dans commercial_orders
DO $$ 
BEGIN
    -- Colonne sale_confirmed
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'commercial_orders' AND column_name = 'sale_confirmed'
    ) THEN
        ALTER TABLE commercial_orders ADD COLUMN sale_confirmed BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Colonne sale_confirmed ajoutée à commercial_orders';
    END IF;
    
    -- Colonne sale_confirmed_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'commercial_orders' AND column_name = 'sale_confirmed_at'
    ) THEN
        ALTER TABLE commercial_orders ADD COLUMN sale_confirmed_at TIMESTAMP;
        RAISE NOTICE 'Colonne sale_confirmed_at ajoutée à commercial_orders';
    END IF;
    
    -- Colonne sale_confirmed_by_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'commercial_orders' AND column_name = 'sale_confirmed_by_id'
    ) THEN
        ALTER TABLE commercial_orders ADD COLUMN sale_confirmed_by_id BIGINT;
        RAISE NOTICE 'Colonne sale_confirmed_by_id ajoutée à commercial_orders';
    END IF;
END $$;

-- Créer les tables pour les équipes commerciales si elles n'existent pas
DO $$ 
BEGIN
    -- Table lockiste_teams
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lockiste_teams') THEN
        CREATE TABLE lockiste_teams (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            supervisor_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE INDEX idx_lockiste_teams_supervisor ON lockiste_teams(supervisor_id);
        CREATE INDEX idx_lockiste_teams_region ON lockiste_teams(region_id);
        RAISE NOTICE 'Table lockiste_teams créée';
    END IF;
    
    -- Table lockiste_members
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lockiste_members') THEN
        CREATE TABLE lockiste_members (
            id BIGSERIAL PRIMARY KEY,
            team_id BIGINT NOT NULL REFERENCES lockiste_teams(id) ON UPDATE CASCADE ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            full_name VARCHAR(255),
            phone VARCHAR(50),
            email VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team_id, user_id)
        );
        CREATE INDEX idx_lockiste_members_team ON lockiste_members(team_id);
        CREATE INDEX idx_lockiste_members_user ON lockiste_members(user_id);
        RAISE NOTICE 'Table lockiste_members créée';
    END IF;
    
    -- Table vendeur_teams
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vendeur_teams') THEN
        CREATE TABLE vendeur_teams (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            supervisor_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            region_id BIGINT REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE INDEX idx_vendeur_teams_supervisor ON vendeur_teams(supervisor_id);
        CREATE INDEX idx_vendeur_teams_region ON vendeur_teams(region_id);
        RAISE NOTICE 'Table vendeur_teams créée';
    END IF;
    
    -- Table vendeur_members
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vendeur_members') THEN
        CREATE TABLE vendeur_members (
            id BIGSERIAL PRIMARY KEY,
            team_id BIGINT NOT NULL REFERENCES vendeur_teams(id) ON UPDATE CASCADE ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            full_name VARCHAR(255),
            phone VARCHAR(50),
            email VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team_id, user_id)
        );
        CREATE INDEX idx_vendeur_members_team ON vendeur_members(team_id);
        CREATE INDEX idx_vendeur_members_user ON vendeur_members(user_id);
        RAISE NOTICE 'Table vendeur_members créée';
    END IF;
    
    -- Table commercial_sales
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'commercial_sales') THEN
        CREATE TABLE commercial_sales (
            id BIGSERIAL PRIMARY KEY,
            order_id BIGINT REFERENCES commercial_orders(id) ON UPDATE CASCADE ON DELETE SET NULL,
            order_client_id BIGINT REFERENCES commercial_order_clients(id) ON UPDATE CASCADE ON DELETE SET NULL,
            commercial_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            supervisor_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            invoice_number VARCHAR(50) NOT NULL,
            invoice_date DATE NOT NULL,
            sale_date DATE NOT NULL,
            total_amount_gnf DECIMAL(18, 2) NOT NULL,
            payment_method VARCHAR(20) NOT NULL DEFAULT 'cash',
            payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            payment_due_date DATE,
            confirmed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE INDEX idx_commercial_sales_order ON commercial_sales(order_id);
        CREATE INDEX idx_commercial_sales_commercial ON commercial_sales(commercial_id);
        CREATE INDEX idx_commercial_sales_supervisor ON commercial_sales(supervisor_id);
        CREATE INDEX idx_commercial_sales_invoice ON commercial_sales(invoice_number);
        CREATE INDEX idx_commercial_sales_date ON commercial_sales(sale_date);
        CREATE INDEX idx_commercial_sales_status ON commercial_sales(status);
        RAISE NOTICE 'Table commercial_sales créée';
    END IF;
    
    -- Table commercial_sale_items
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'commercial_sale_items') THEN
        CREATE TABLE commercial_sale_items (
            id BIGSERIAL PRIMARY KEY,
            sale_id BIGINT NOT NULL REFERENCES commercial_sales(id) ON UPDATE CASCADE ON DELETE CASCADE,
            stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            quantity DECIMAL(10, 2) NOT NULL,
            unit_price_gnf DECIMAL(18, 2) NOT NULL,
            total_price_gnf DECIMAL(18, 2) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_sale_items_sale ON commercial_sale_items(sale_id);
        CREATE INDEX idx_sale_items_stock_item ON commercial_sale_items(stock_item_id);
        RAISE NOTICE 'Table commercial_sale_items créée';
    END IF;
    
    -- Table sales_objectives
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sales_objectives') THEN
        CREATE TABLE sales_objectives (
            id BIGSERIAL PRIMARY KEY,
            commercial_id BIGINT NOT NULL REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            supervisor_id BIGINT REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            target_amount_gnf DECIMAL(18, 2) NOT NULL,
            target_quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
            achieved_amount_gnf DECIMAL(18, 2) DEFAULT 0,
            achieved_quantity DECIMAL(10, 2) DEFAULT 0,
            forecast_id BIGINT REFERENCES forecasts(id) ON UPDATE CASCADE ON DELETE SET NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE INDEX idx_sales_objectives_commercial ON sales_objectives(commercial_id);
        CREATE INDEX idx_sales_objectives_supervisor ON sales_objectives(supervisor_id);
        CREATE INDEX idx_sales_objectives_period ON sales_objectives(period_start, period_end);
        CREATE INDEX idx_sales_objectives_status ON sales_objectives(status);
        RAISE NOTICE 'Table sales_objectives créée';
    END IF;
    
    -- Table sales_objective_items
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sales_objective_items') THEN
        CREATE TABLE sales_objective_items (
            id BIGSERIAL PRIMARY KEY,
            objective_id BIGINT NOT NULL REFERENCES sales_objectives(id) ON UPDATE CASCADE ON DELETE CASCADE,
            stock_item_id BIGINT NOT NULL REFERENCES stock_items(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            target_quantity DECIMAL(10, 2) NOT NULL,
            target_price_gnf DECIMAL(18, 2) NOT NULL,
            achieved_quantity DECIMAL(10, 2) DEFAULT 0,
            achieved_amount_gnf DECIMAL(18, 2) DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_objective_items_objective ON sales_objective_items(objective_id);
        CREATE INDEX idx_objective_items_stock_item ON sales_objective_items(stock_item_id);
        RAISE NOTICE 'Table sales_objective_items créée';
    END IF;
END $$;

-- =========================================================
-- 3. PERMISSIONS SUPERVISEUR POUR NOUVEAUX MODULES
-- =========================================================

DO $$ 
DECLARE
    supervisor_permissions JSONB;
BEGIN
    -- Récupérer les permissions actuelles du superviseur
    SELECT permissions INTO supervisor_permissions
    FROM roles
    WHERE code = 'supervisor';
    
    -- Si le rôle existe
    IF supervisor_permissions IS NOT NULL THEN
        -- Ajouter commercial_teams si absent
        IF NOT (supervisor_permissions ? 'commercial_teams') THEN
            supervisor_permissions := jsonb_set(
                supervisor_permissions,
                '{commercial_teams}',
                '["read", "write"]'::jsonb
            );
            RAISE NOTICE 'Permissions commercial_teams ajoutées au superviseur';
        END IF;
        
        -- Ajouter sales si absent
        IF NOT (supervisor_permissions ? 'sales') THEN
            supervisor_permissions := jsonb_set(
                supervisor_permissions,
                '{sales}',
                '["confirm", "view_confirmed"]'::jsonb
            );
            RAISE NOTICE 'Permissions sales ajoutées au superviseur';
        END IF;
        
        -- Ajouter objectives si absent
        IF NOT (supervisor_permissions ? 'objectives') THEN
            supervisor_permissions := jsonb_set(
                supervisor_permissions,
                '{objectives}',
                '["read", "write"]'::jsonb
            );
            RAISE NOTICE 'Permissions objectives ajoutées au superviseur';
        END IF;
        
        -- Mettre à jour les permissions
        UPDATE roles
        SET permissions = supervisor_permissions
        WHERE code = 'supervisor';
    ELSE
        RAISE WARNING 'Rôle supervisor non trouvé';
    END IF;
END $$;

COMMIT;

-- =========================================================
-- RÉSUMÉ DE LA MIGRATION
-- =========================================================
-- ✅ Permissions flotte pour magasinier (vehicles.create ajouté)
-- ✅ Colonnes supervision dans users, promotion_teams, promotion_members
-- ✅ Colonnes confirmation vente dans commercial_orders
-- ✅ Tables équipes commerciales (lockiste_teams, lockiste_members, vendeur_teams, vendeur_members)
-- ✅ Tables ventes confirmées (commercial_sales, commercial_sale_items)
-- ✅ Tables objectifs de vente (sales_objectives, sales_objective_items)
-- ✅ Permissions superviseur pour nouveaux modules
-- =========================================================

