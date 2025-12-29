-- Script SQL simple pour ajouter la colonne client_phone
-- À exécuter: mysql -u root -p import_profit < add_client_phone_mysql_simple.sql

USE import_profit;

-- Ajouter client_phone à stock_outgoings (ignore l'erreur si la colonne existe déjà)
ALTER TABLE stock_outgoings 
ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name;

-- Ajouter client_phone à stock_returns (ignore l'erreur si la colonne existe déjà)
ALTER TABLE stock_returns 
ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name;

SELECT 'Colonnes client_phone ajoutées avec succès' AS result;
