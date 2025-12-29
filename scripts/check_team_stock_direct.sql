-- Script SQL pour vérifier directement le stock d'une équipe dans la base de données
-- Utilisation: mysql -u root -p import_profit < scripts/check_team_stock_direct.sql

-- Vérifier le stock de l'équipe ID 1
SELECT 
    pts.id,
    pts.team_id,
    pt.name as team_name,
    pts.gamme_id,
    pg.name as gamme_name,
    pts.quantity,
    pts.last_updated,
    pts.created_at
FROM promotion_team_stock pts
LEFT JOIN promotion_teams pt ON pts.team_id = pt.id
LEFT JOIN promotion_gammes pg ON pts.gamme_id = pg.id
WHERE pts.team_id = 1
ORDER BY pts.gamme_id;

-- Compter le nombre total d'enregistrements
SELECT COUNT(*) as total_stock_records
FROM promotion_team_stock
WHERE team_id = 1;

-- Vérifier toutes les équipes
SELECT 
    pt.id as team_id,
    pt.name as team_name,
    COUNT(pts.id) as nombre_gammes,
    SUM(pts.quantity) as total_quantite
FROM promotion_teams pt
LEFT JOIN promotion_team_stock pts ON pt.id = pts.team_id
GROUP BY pt.id, pt.name
ORDER BY pt.id;

