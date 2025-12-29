-- Ajout des colonnes reference et transaction_type à la table promotion_sales
-- Ces colonnes sont CRUCIALES pour identifier de manière unique chaque opération
-- Format reference: ENL-YYYYMMDD-NNNN pour enlèvements, RET-YYYYMMDD-NNNN pour retours

-- 1. Ajouter la colonne reference si elle n'existe pas
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_sales' 
    AND COLUMN_NAME = 'reference'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE promotion_sales ADD COLUMN reference VARCHAR(50) NULL AFTER id',
    'SELECT "La colonne reference existe déjà" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. Ajouter la colonne transaction_type si elle n'existe pas
SET @col_exists2 = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'promotion_sales' 
    AND COLUMN_NAME = 'transaction_type'
);

SET @sql2 = IF(@col_exists2 = 0,
    'ALTER TABLE promotion_sales ADD COLUMN transaction_type ENUM("enlevement", "retour") NOT NULL DEFAULT "enlevement" AFTER gamme_id',
    'SELECT "La colonne transaction_type existe déjà" AS message'
);

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- 3. Créer un index unique sur la colonne reference si elle n'existe pas déjà
CREATE UNIQUE INDEX IF NOT EXISTS idx_promosale_reference_unique ON promotion_sales(reference);

-- 4. Mettre à jour les ventes existantes sans référence avec des références générées
-- Format: ENL-YYYYMMDD-NNNN pour enlèvements, RET-YYYYMMDD-NNNN pour retours
UPDATE promotion_sales 
SET reference = CONCAT(
    IF(transaction_type = 'retour', 'RET', 'ENL'), 
    '-', 
    DATE_FORMAT(sale_date, '%Y%m%d'), 
    '-', 
    LPAD(id, 4, '0')
)
WHERE reference IS NULL OR reference = '';

-- 5. Afficher un message de confirmation
SELECT CONCAT('Colonnes ajoutées avec succès. ', COUNT(*), ' ventes mises à jour.') AS resultat
FROM promotion_sales;

