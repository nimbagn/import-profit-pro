-- Migration MySQL : Ajout des champs pour retours fournisseurs
-- Date : 2 Janvier 2026
-- Description : Ajoute les colonnes nécessaires pour gérer les retours fournisseurs (mouvement inverse des réceptions)

-- 1. Ajouter la colonne return_type (type de retour : client ou supplier)
ALTER TABLE stock_returns 
ADD COLUMN return_type ENUM('client', 'supplier') NOT NULL DEFAULT 'client' AFTER return_date;

-- 2. Ajouter la colonne supplier_name (nom du fournisseur pour retours fournisseurs)
ALTER TABLE stock_returns 
ADD COLUMN supplier_name VARCHAR(120) NULL AFTER client_phone;

-- 3. Ajouter la colonne original_reception_id (lien avec la réception originale)
ALTER TABLE stock_returns 
ADD COLUMN original_reception_id BIGINT UNSIGNED NULL AFTER original_order_id,
ADD CONSTRAINT fk_return_reception 
    FOREIGN KEY (original_reception_id) 
    REFERENCES receptions(id) 
    ON UPDATE CASCADE 
    ON DELETE SET NULL;

-- 4. Modifier client_name pour être nullable (car optionnel pour retours fournisseurs)
ALTER TABLE stock_returns 
MODIFY COLUMN client_name VARCHAR(120) NULL;

-- 5. Ajouter un index sur return_type pour améliorer les performances
CREATE INDEX idx_return_type ON stock_returns(return_type);

-- 6. Ajouter un index sur original_reception_id
CREATE INDEX idx_return_reception ON stock_returns(original_reception_id);

-- Vérification
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'stock_returns'
    AND COLUMN_NAME IN ('return_type', 'supplier_name', 'original_reception_id', 'client_name')
ORDER BY ORDINAL_POSITION;

