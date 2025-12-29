-- Script SQL pour recalculer les écarts d'inventaire
-- Formule corrigée : ÉCART = stock actuel - (QUANTITÉ COMPTÉE + PILE)
-- La quantité comptée inclut déjà la pile si elle a été calculée

USE madargn;

-- Afficher les détails avant modification (pour vérification)
SELECT 
    id,
    session_id,
    stock_item_id,
    system_quantity AS 'Stock Système',
    counted_quantity AS 'Quantité Comptée',
    variance AS 'Ancien Écart',
    (system_quantity - counted_quantity) AS 'Nouvel Écart',
    pile_dimensions AS 'Pile'
FROM inventory_details
ORDER BY session_id, stock_item_id;

-- Mettre à jour tous les écarts avec la nouvelle formule
UPDATE inventory_details
SET variance = system_quantity - counted_quantity
WHERE variance != (system_quantity - counted_quantity);

-- Afficher le nombre de lignes modifiées
SELECT ROW_COUNT() AS 'Lignes modifiées';

-- Vérification : Afficher les détails après modification
SELECT 
    id,
    session_id,
    stock_item_id,
    system_quantity AS 'Stock Système',
    counted_quantity AS 'Quantité Comptée',
    variance AS 'Écart (corrigé)',
    pile_dimensions AS 'Pile'
FROM inventory_details
ORDER BY session_id, stock_item_id;

