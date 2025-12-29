-- Script pour ajouter la colonne reference à la table stock_movements
-- Exécuter ce script dans MySQL si la colonne reference n'existe pas

USE madargn;

-- Vérifier et ajouter la colonne reference si elle n'existe pas
SET @dbname = DATABASE();
SET @tablename = 'stock_movements';
SET @columnname = 'reference';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(50) NULL UNIQUE, ADD INDEX idx_movement_reference (', @columnname, ')')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SELECT 'Colonne reference ajoutée avec succès à stock_movements' AS result;

