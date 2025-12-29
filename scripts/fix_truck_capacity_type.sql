-- Script pour corriger le type de la colonne truck_capacity_tons
-- Exécuter avec: mysql -u root -p madargn < scripts/fix_truck_capacity_type.sql

USE madargn;

-- Modifier le type de truck_capacity_tons de DECIMAL(18,2) à DECIMAL(18,4)
ALTER TABLE simulations 
MODIFY COLUMN truck_capacity_tons DECIMAL(18,4) NOT NULL DEFAULT 0.0000;

-- Vérifier le type modifié
SHOW COLUMNS FROM simulations LIKE 'truck_capacity_tons';

