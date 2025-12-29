-- Script pour ajouter les colonnes manquantes à la table stock_returns
-- Exécuter ce script dans MySQL si la colonne original_outgoing_id n'existe pas

USE madargn;

-- Vérifier et ajouter la colonne original_outgoing_id si elle n'existe pas
SET @dbname = DATABASE();
SET @tablename = 'stock_returns';
SET @columnname = 'original_outgoing_id';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' BIGINT UNSIGNED NULL, ADD INDEX idx_return_outgoing (', @columnname, '), ADD CONSTRAINT fk_returns_outgoing FOREIGN KEY (', @columnname, ') REFERENCES stock_outgoings(id) ON UPDATE CASCADE ON DELETE SET NULL')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Vérifier et ajouter la colonne reference si elle n'existe pas
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
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(50) NULL UNIQUE, ADD INDEX idx_return_reference (', @columnname, ')')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SELECT 'Colonnes ajoutées avec succès' AS result;

