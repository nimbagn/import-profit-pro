-- Ajout de la colonne reference à la table promotion_sales
-- Cette colonne est CRUCIALE pour identifier de manière unique chaque opération
-- Format: ENL-YYYYMMDD-NNNN pour enlèvements, RET-YYYYMMDD-NNNN pour retours

-- Vérifier si la colonne existe déjà avant de l'ajouter
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_sales' 
    AND COLUMN_NAME = 'reference'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_sales ADD COLUMN reference VARCHAR(50) NULL UNIQUE AFTER id',
    'SELECT "La colonne reference existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Créer un index unique sur la colonne reference si elle n'existe pas déjà
CREATE UNIQUE INDEX IF NOT EXISTS idx_promosale_reference_unique ON promotion_sales(reference);

-- Mettre à jour les ventes existantes sans référence avec des références générées
-- Format: ENL-YYYYMMDD-NNNN pour enlèvements, RET-YYYYMMDD-NNNN pour retours
UPDATE promotion_sales 
SET reference = CONCAT('ENL-', DATE_FORMAT(sale_date, '%Y%m%d'), '-', LPAD(id, 4, '0'))
WHERE reference IS NULL OR reference = '';

-- Afficher un message de confirmation
SELECT CONCAT('Colonne reference ajoutée avec succès. ', COUNT(*), ' ventes mises à jour.') AS resultat
FROM promotion_sales;

