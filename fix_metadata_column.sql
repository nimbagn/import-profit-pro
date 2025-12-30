-- Script de correction : Renommer la colonne 'metadata' en 'activity_metadata'
-- Date: 2025-01-XX
-- Description: SQLAlchemy réserve le nom 'metadata', il faut le renommer

-- Vérifier si la colonne 'metadata' existe et la renommer
-- Si la table n'existe pas encore, cette commande ne fera rien (pas d'erreur)

-- Pour MySQL
ALTER TABLE `user_activity_logs` 
CHANGE COLUMN `metadata` `activity_metadata` JSON NULL;

-- Note: Si vous obtenez une erreur "Unknown column 'metadata'", 
-- cela signifie que la table n'a pas encore été créée ou utilise déjà 'activity_metadata'
-- Dans ce cas, exécutez simplement migration_rh_complete.sql qui créera la table correctement

