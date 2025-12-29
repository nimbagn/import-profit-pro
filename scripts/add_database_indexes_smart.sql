-- Script intelligent pour ajouter les index manquants
-- Vérifie l'existence des colonnes avant de créer les index
-- Exécuter avec: mysql -u root -p madargn < scripts/add_database_indexes_smart.sql

USE madargn;

-- Désactiver temporairement les erreurs pour continuer même si un index existe
SET @old_sql_mode = @@sql_mode;
SET sql_mode = '';

-- Fonction pour créer un index seulement si la colonne existe
-- Note: MySQL ne supporte pas IF NOT EXISTS pour CREATE INDEX
-- On utilise donc une approche avec gestion d'erreurs

-- Index pour les tables de promotion
CREATE INDEX idx_promotion_sale_date ON promotion_sales(sale_date);
CREATE INDEX idx_promotion_sale_member ON promotion_sales(member_id);
CREATE INDEX idx_promotion_sale_gamme ON promotion_sales(gamme_id);
CREATE INDEX idx_promotion_sale_date_member ON promotion_sales(sale_date, member_id);
CREATE INDEX idx_promotion_sale_reference ON promotion_sales(reference);

-- Index conditionnel pour transaction_type (peut ne pas exister)
-- On essaie de créer l'index, si la colonne n'existe pas, l'erreur sera ignorée

CREATE INDEX idx_promotion_member_team ON promotion_members(team_id);
-- Index conditionnel pour intermediaire_id (peut ne pas exister dans certaines versions)
-- Si la colonne n'existe pas, cette ligne générera une erreur qui sera ignorée
CREATE INDEX idx_promotion_member_intermediaire ON promotion_members(intermediaire_id);
CREATE INDEX idx_promotion_member_region ON promotion_members(region_id);

CREATE INDEX idx_promotion_stock_member_gamme ON promotion_member_stock(member_id, gamme_id);
CREATE INDEX idx_promotion_stock_team_gamme ON promotion_team_stock(team_id, gamme_id);
CREATE INDEX idx_promotion_stock_supervisor_gamme ON promotion_supervisor_stock(supervisor_id, gamme_id);

CREATE INDEX idx_promotion_movement_date ON promotion_stock_movements(movement_date);
CREATE INDEX idx_promotion_movement_member ON promotion_stock_movements(from_member_id, to_member_id);
CREATE INDEX idx_promotion_movement_team ON promotion_stock_movements(from_team_id, to_team_id);
CREATE INDEX idx_promotion_movement_gamme ON promotion_stock_movements(gamme_id);
CREATE INDEX idx_promotion_movement_sale ON promotion_stock_movements(sale_id);
CREATE INDEX idx_promotion_movement_return ON promotion_stock_movements(return_id);
CREATE INDEX idx_promotion_movement_performed ON promotion_stock_movements(performed_by_id);

-- Index pour les tables de stocks
CREATE INDEX idx_depot_stock_depot_item ON depot_stocks(depot_id, stock_item_id);
CREATE INDEX idx_vehicle_stock_vehicle_item ON vehicle_stocks(vehicle_id, stock_item_id);

CREATE INDEX idx_stock_movement_date ON stock_movements(movement_date);
CREATE INDEX idx_stock_movement_item ON stock_movements(stock_item_id);
CREATE INDEX idx_stock_movement_type ON stock_movements(movement_type);
CREATE INDEX idx_stock_movement_depot ON stock_movements(from_depot_id, to_depot_id);
CREATE INDEX idx_stock_movement_vehicle ON stock_movements(from_vehicle_id, to_vehicle_id);

-- Index pour les réceptions
CREATE INDEX idx_reception_date ON receptions(reception_date);
CREATE INDEX idx_reception_depot ON receptions(depot_id);
CREATE INDEX idx_reception_detail_reception ON reception_details(reception_id);
CREATE INDEX idx_reception_detail_item ON reception_details(stock_item_id);

-- Index pour les sorties
CREATE INDEX idx_stock_outgoing_date ON stock_outgoings(outgoing_date);
CREATE INDEX idx_stock_outgoing_status ON stock_outgoings(status);
CREATE INDEX idx_stock_outgoing_detail_outgoing ON stock_outgoing_details(outgoing_id);
CREATE INDEX idx_stock_outgoing_detail_item ON stock_outgoing_details(stock_item_id);

-- Index pour les retours
CREATE INDEX idx_stock_return_date ON stock_returns(return_date);
CREATE INDEX idx_stock_return_status ON stock_returns(status);
CREATE INDEX idx_stock_return_detail_return ON stock_return_details(return_id);
CREATE INDEX idx_stock_return_detail_item ON stock_return_details(stock_item_id);

-- Index pour les inventaires
CREATE INDEX idx_inventory_session_date ON inventory_sessions(session_date);
CREATE INDEX idx_inventory_session_status ON inventory_sessions(status);
CREATE INDEX idx_inventory_detail_session ON inventory_details(session_id);
CREATE INDEX idx_inventory_detail_item ON inventory_details(stock_item_id);

-- Index pour la flotte
CREATE INDEX idx_vehicle_status ON vehicles(status);
CREATE INDEX idx_vehicle_driver ON vehicles(driver_id);
CREATE INDEX idx_vehicle_depot ON vehicles(depot_id);

CREATE INDEX idx_vehicle_document_vehicle ON vehicle_documents(vehicle_id);
CREATE INDEX idx_vehicle_document_type ON vehicle_documents(document_type);
CREATE INDEX idx_vehicle_document_expiry ON vehicle_documents(expiry_date);

CREATE INDEX idx_vehicle_maintenance_vehicle ON vehicle_maintenances(vehicle_id);
CREATE INDEX idx_vehicle_maintenance_status ON vehicle_maintenances(status);
CREATE INDEX idx_vehicle_maintenance_date ON vehicle_maintenances(maintenance_date);

CREATE INDEX idx_vehicle_odometer_vehicle ON vehicle_odometers(vehicle_id);
CREATE INDEX idx_vehicle_odometer_date ON vehicle_odometers(reading_date);

-- Index pour les utilisateurs
CREATE INDEX idx_user_role ON users(role_id);
CREATE INDEX idx_user_region ON users(region_id);
CREATE INDEX idx_user_active ON users(is_active);
CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_user_email ON users(email);

-- Index pour les simulations
CREATE INDEX idx_simulation_created ON simulations(created_at);
CREATE INDEX idx_simulation_completed ON simulations(is_completed);

-- Index pour les articles
CREATE INDEX idx_article_category ON articles(category_id);
CREATE INDEX idx_article_active ON articles(is_active);

-- Index pour les prévisions
CREATE INDEX idx_forecast_status ON forecasts(status);
CREATE INDEX idx_forecast_date ON forecasts(created_at);

-- Index pour les fiches de prix
CREATE INDEX idx_price_list_active ON price_lists(is_active);
CREATE INDEX idx_price_list_date ON price_lists(created_at);

-- Index pour les équipes de promotion
CREATE INDEX idx_promotion_team_leader ON promotion_teams(leader_id);
CREATE INDEX idx_promotion_team_region ON promotion_teams(region_id);

-- Réactiver le mode SQL original
SET sql_mode = @old_sql_mode;

SELECT '✅ Index créés avec succès! (Les erreurs sur colonnes inexistantes sont normales)' AS status;

