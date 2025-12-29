-- Script SQL pour vérifier les mouvements de stock de l'équipe "Equipe Promo Siradjou"
-- Exécutez ce script dans votre client MySQL

-- 1. Trouver l'ID de l'équipe
SELECT id, name, region, is_active 
FROM promotion_teams 
WHERE name LIKE '%Siradjou%' OR name LIKE '%Equipe Promo%';

-- 2. Récupérer tous les mouvements pour cette équipe (remplacez TEAM_ID par l'ID trouvé)
-- Pour l'équipe ID 1 (exemple)
SELECT 
    m.id,
    m.movement_type,
    m.movement_date,
    m.gamme_id,
    g.name AS gamme_name,
    m.quantity,
    m.quantity_change,
    m.from_supervisor_id,
    m.from_team_id,
    m.from_member_id,
    m.to_supervisor_id,
    m.to_team_id,
    m.to_member_id,
    m.sale_id,
    m.return_id,
    m.performed_by_id,
    u.full_name AS performed_by_name
FROM promotion_stock_movements m
LEFT JOIN promotion_gammes g ON m.gamme_id = g.id
LEFT JOIN users u ON m.performed_by_id = u.id
WHERE (m.from_team_id = 1 OR m.to_team_id = 1)
ORDER BY m.movement_date ASC;

-- 3. Calculer le solde progressif par gamme pour l'équipe
SELECT 
    g.id AS gamme_id,
    g.name AS gamme_name,
    SUM(CASE 
        WHEN m.to_team_id = 1 THEN ABS(m.quantity_change)  -- Approvisionnement ou Retour
        WHEN m.from_team_id = 1 THEN -ABS(m.quantity_change)  -- Enlèvement
        ELSE 0
    END) AS solde_calcule,
    SUM(CASE 
        WHEN m.movement_type = 'approvisionnement' AND m.to_team_id = 1 THEN ABS(m.quantity_change)
        WHEN m.movement_type = 'retour' AND m.to_team_id = 1 THEN ABS(m.quantity_change)
        WHEN (m.movement_type = 'enlevement' OR m.movement_type = 'distribution') AND m.from_team_id = 1 THEN -ABS(m.quantity_change)
        ELSE 0
    END) AS solde_calcule_detail
FROM promotion_stock_movements m
LEFT JOIN promotion_gammes g ON m.gamme_id = g.id
WHERE (m.from_team_id = 1 OR m.to_team_id = 1)
GROUP BY g.id, g.name
ORDER BY g.name;

-- 4. Vérifier le stock actuel dans promotion_team_stock
SELECT 
    ts.team_id,
    t.name AS team_name,
    ts.gamme_id,
    g.name AS gamme_name,
    ts.quantity AS stock_actuel,
    ts.last_updated
FROM promotion_team_stock ts
JOIN promotion_teams t ON ts.team_id = t.id
LEFT JOIN promotion_gammes g ON ts.gamme_id = g.id
WHERE t.name LIKE '%Siradjou%' OR t.name LIKE '%Equipe Promo%'
ORDER BY g.name;

-- 5. Détail des mouvements avec calcul du solde progressif
SET @team_id = 1;  -- Remplacez par l'ID de l'équipe
SET @solde = 0;

SELECT 
    m.id,
    m.movement_date,
    m.movement_type,
    g.name AS gamme_name,
    m.quantity_change,
    CASE 
        WHEN m.to_team_id = @team_id THEN 'ENTRANT'
        WHEN m.from_team_id = @team_id THEN 'SORTANT'
        ELSE 'N/A'
    END AS direction,
    @solde := @solde + CASE 
        WHEN m.to_team_id = @team_id THEN ABS(m.quantity_change)
        WHEN m.from_team_id = @team_id THEN m.quantity_change  -- Déjà négatif
        ELSE 0
    END AS solde_progressif,
    m.from_supervisor_id,
    m.from_team_id,
    m.from_member_id,
    m.to_supervisor_id,
    m.to_team_id,
    m.to_member_id
FROM promotion_stock_movements m
LEFT JOIN promotion_gammes g ON m.gamme_id = g.id
WHERE (m.from_team_id = @team_id OR m.to_team_id = @team_id)
ORDER BY m.movement_date ASC, m.id ASC;

