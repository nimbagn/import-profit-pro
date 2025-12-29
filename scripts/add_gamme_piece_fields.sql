-- Script pour ajouter les champs de pièce/unitaire à la table promotion_gammes
-- Exécutez ce script dans votre base de données MySQL
-- Compatible MySQL 5.7+

USE madargn;  -- Remplacez par le nom de votre base de données

-- Vérifier et ajouter la colonne is_piece
SET @dbname = DATABASE();
SET @tablename = 'promotion_gammes';
SET @columnname = 'is_piece';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1', -- Colonne existe déjà
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' BOOLEAN NOT NULL DEFAULT FALSE COMMENT ''Indique si c''est une pièce/unitaire''')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Vérifier et ajouter la colonne unit_type
SET @columnname = 'unit_type';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1', -- Colonne existe déjà
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(100) NULL COMMENT ''Type d''unité: bouteille, pièce, sachet, etc.''')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Vérifier et ajouter la colonne unit_description
SET @columnname = 'unit_description';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1', -- Colonne existe déjà
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(500) NULL COMMENT ''Description de l''unité: 800 ml, 1 kg, etc.''')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Ajouter des index (ignore l'erreur si l'index existe déjà)
-- Note: MySQL ne supporte pas IF NOT EXISTS pour CREATE INDEX, donc on utilise une procédure
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS add_index_if_not_exists()
BEGIN
  DECLARE index_exists INT DEFAULT 0;
  
  -- Vérifier et créer l'index idx_promogamme_piece
  SELECT COUNT(*) INTO index_exists
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE table_schema = @dbname
    AND table_name = @tablename
    AND index_name = 'idx_promogamme_piece';
  
  IF index_exists = 0 THEN
    SET @sql = CONCAT('CREATE INDEX idx_promogamme_piece ON ', @tablename, '(is_piece)');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
  
  -- Vérifier et créer l'index idx_promogamme_unit_type
  SELECT COUNT(*) INTO index_exists
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE table_schema = @dbname
    AND table_name = @tablename
    AND index_name = 'idx_promogamme_unit_type';
  
  IF index_exists = 0 THEN
    SET @sql = CONCAT('CREATE INDEX idx_promogamme_unit_type ON ', @tablename, '(unit_type)');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END$$

DELIMITER ;

CALL add_index_if_not_exists();
DROP PROCEDURE IF EXISTS add_index_if_not_exists;

-- Afficher la structure de la table pour vérification
DESCRIBE promotion_gammes;

-- Afficher un message de confirmation
SELECT '✅ Colonnes ajoutées avec succès!' AS Message;

