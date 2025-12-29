-- Script simple pour ajouter les colonnes manquantes à la table simulations
-- Exécuter avec: mysql -u root -p madargn < scripts/add_rate_xof_simple.sql

USE madargn;

-- Ajouter rate_xof (ignorer l'erreur si la colonne existe déjà)
ALTER TABLE simulations 
ADD COLUMN rate_xof DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER rate_eur;

-- Ajouter customs_gnf
ALTER TABLE simulations 
ADD COLUMN customs_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER rate_xof;

-- Ajouter handling_gnf
ALTER TABLE simulations 
ADD COLUMN handling_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER customs_gnf;

-- Ajouter others_gnf
ALTER TABLE simulations 
ADD COLUMN others_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER handling_gnf;

-- Ajouter transport_fixed_gnf
ALTER TABLE simulations 
ADD COLUMN transport_fixed_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER others_gnf;

-- Ajouter transport_per_kg_gnf
ALTER TABLE simulations 
ADD COLUMN transport_per_kg_gnf DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER transport_fixed_gnf;

-- Ajouter basis
ALTER TABLE simulations 
ADD COLUMN basis ENUM('value', 'weight') NOT NULL DEFAULT 'value' AFTER transport_per_kg_gnf;

-- Ajouter truck_capacity_tons
ALTER TABLE simulations 
ADD COLUMN truck_capacity_tons DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER basis;

-- Ajouter target_mode
ALTER TABLE simulations 
ADD COLUMN target_mode ENUM('none', 'price', 'purchase', 'global') NOT NULL DEFAULT 'none' AFTER truck_capacity_tons;

-- Ajouter target_margin_pct
ALTER TABLE simulations 
ADD COLUMN target_margin_pct DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER target_mode;

-- Vérifier les colonnes
SHOW COLUMNS FROM simulations;
