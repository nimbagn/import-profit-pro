-- Script d'optimisation : Ajout d'index pour améliorer les performances
-- Date : 30 Décembre 2025
-- Usage : Exécuter sur Render via psql ou via Python

-- Index pour le dashboard (simulations)
CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_simulations_completed ON simulations(is_completed) WHERE is_completed = true;
CREATE INDEX IF NOT EXISTS idx_simulations_region ON simulations(region_id) WHERE region_id IS NOT NULL;

-- Index pour les mouvements de stock
CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_depot ON stock_movements(depot_id) WHERE depot_id IS NOT NULL;

-- Index pour les véhicules
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_vehicles_region ON vehicles(region_id) WHERE region_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_vehicles_active ON vehicles(status) WHERE status = 'active';

-- Index pour les commandes
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_region ON orders(region_id) WHERE region_id IS NOT NULL;

-- Index pour les articles et stocks
CREATE INDEX IF NOT EXISTS idx_stock_items_code ON stock_items(code);
CREATE INDEX IF NOT EXISTS idx_depot_stocks_depot ON depot_stocks(depot_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_stocks_vehicle ON vehicle_stocks(vehicle_id);

-- Index pour les inventaires
CREATE INDEX IF NOT EXISTS idx_inventory_sessions_date ON inventory_sessions(session_date DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_sessions_status ON inventory_sessions(status);

-- Index pour les réceptions
CREATE INDEX IF NOT EXISTS idx_receptions_date ON receptions(reception_date DESC);
CREATE INDEX IF NOT EXISTS idx_receptions_depot ON receptions(depot_id) WHERE depot_id IS NOT NULL;

-- Index pour les utilisateurs et activités
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id) WHERE role_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user ON user_activity_logs(user_id);

-- Index pour les employés RH
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(employment_status);
CREATE INDEX IF NOT EXISTS idx_employee_contracts_status ON employee_contracts(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_employee_absences_status ON employee_absences(status) WHERE status = 'pending';

-- Index composites pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_simulations_region_created ON simulations(region_id, created_at DESC) WHERE region_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_region_status ON orders(region_id, status) WHERE region_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stock_movements_depot_date ON stock_movements(depot_id, movement_date DESC) WHERE depot_id IS NOT NULL;

-- Afficher les index créés
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

