-- Script pour ajouter la colonne image_path à la table articles
-- Exécuter avec: mysql -u root -p madargn < scripts/add_image_path_to_articles.sql

USE madargn;

-- Vérifier si la colonne existe déjà avant de l'ajouter
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'madargn' 
    AND TABLE_NAME = 'articles' 
    AND COLUMN_NAME = 'image_path'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE articles ADD COLUMN image_path VARCHAR(500) NULL AFTER unit_weight_kg',
    'SELECT "La colonne image_path existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Colonne image_path ajoutée avec succès' AS result;

