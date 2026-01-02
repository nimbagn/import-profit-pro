-- Migration MySQL : Ajout du type de mouvement 'reception_return'
-- Date : 2 Janvier 2026
-- Description : Ajoute le type 'reception_return' à l'enum movement_type

-- Note : MySQL nécessite de recréer l'enum, ce qui peut être complexe
-- Alternative : Utiliser ALTER TABLE avec MODIFY COLUMN

-- Vérifier d'abord si le type existe déjà
SELECT COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'stock_movements' 
    AND COLUMN_NAME = 'movement_type';

-- Pour MySQL, on doit modifier la colonne pour inclure le nouveau type
-- ATTENTION : Cette opération peut prendre du temps sur une grande table
ALTER TABLE stock_movements 
MODIFY COLUMN movement_type ENUM('transfer', 'reception', 'reception_return', 'adjustment', 'inventory') NOT NULL;

-- Vérification
SELECT COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'stock_movements' 
    AND COLUMN_NAME = 'movement_type';

