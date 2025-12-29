-- Script SQL pour vérifier le calcul du stock de l'équipe "Equipe Promo Siradjou"
-- Exécutez ce script dans votre client MySQL (phpMyAdmin, MySQL Workbench, etc.)

-- 1. Trouver l'ID de l'équipe
SELECT id, name, region, is_active 
FROM promotion_teams 
WHERE name LIKE '%Siradjou%' OR name LIKE '%Equipe Promo%';

-- 2. Pour chaque équipe trouvée, remplacer TEAM_ID dans les requêtes suivantes
-- Exemple pour l'équipe ID 1 :

-- 3. Récupérer tous les mouvements pour cette équipe avec calcul du solde progressif
SET @team_id = 1;  -- ⚠️ REMPLACEZ PAR L'ID DE VOTRE ÉQUIPE
SET @solde = 0;

SELECT 
    m.id,
    m.movement_date AS 'Date',
    m.movement_type AS 'Type',
    g.name AS 'Gamme',
    m.quantity_change AS 'Changement',
    CASE 
        WHEN m.to_team_id = @team_id THEN 'ENTRANT'
        WHEN m.from_team_id = @team_id THEN 'SORTANT'
        ELSE 'N/A'
    END AS 'Direction',
    CASE 
        WHEN m.to_team_id = @team_id THEN 
            CASE 
                WHEN m.movement_type = 'approvisionnement' THEN m.quantity_change
                WHEN m.movement_type = 'retour' THEN ABS(m.quantity_change)
                ELSE ABS(m.quantity_change)
            END
        WHEN m.from_team_id = @team_id THEN -ABS(m.quantity_change)
        ELSE 0
    END AS 'Impact',
    @solde := @solde + CASE 
        WHEN m.to_team_id = @team_id THEN 
            CASE 
                WHEN m.movement_type = 'approvisionnement' THEN m.quantity_change
                WHEN m.movement_type = 'retour' THEN ABS(m.quantity_change)
                ELSE ABS(m.quantity_change)
            END
        WHEN m.from_team_id = @team_id THEN -ABS(m.quantity_change)
        ELSE 0
    END AS 'Solde Progressif',
    CASE 
        WHEN m.from_supervisor_id IS NOT NULL THEN CONCAT('Superviseur #', m.from_supervisor_id)
        WHEN m.from_team_id IS NOT NULL THEN CONCAT('Équipe #', m.from_team_id)
        WHEN m.from_member_id IS NOT NULL THEN CONCAT('Membre #', m.from_member_id)
        ELSE '-'
    END AS 'Source',
    CASE 
        WHEN m.to_supervisor_id IS NOT NULL THEN CONCAT('Superviseur #', m.to_supervisor_id)
        WHEN m.to_team_id IS NOT NULL THEN CONCAT('Équipe #', m.to_team_id)
        WHEN m.to_member_id IS NOT NULL THEN CONCAT('Membre #', m.to_member_id)
        ELSE '-'
    END AS 'Destination'
FROM promotion_stock_movements m
LEFT JOIN promotion_gammes g ON m.gamme_id = g.id
WHERE (m.from_team_id = @team_id OR m.to_team_id = @team_id)
ORDER BY m.movement_date ASC, m.id ASC;

-- 4. Résumé par gamme avec solde calculé
SELECT 
    g.id AS gamme_id,
    g.name AS gamme_name,
    SUM(CASE 
        WHEN m.to_team_id = @team_id THEN 
            CASE 
                WHEN m.movement_type = 'approvisionnement' THEN m.quantity_change
                WHEN m.movement_type = 'retour' THEN ABS(m.quantity_change)
                ELSE ABS(m.quantity_change)
            END
        WHEN m.from_team_id = @team_id THEN -ABS(m.quantity_change)
        ELSE 0
    END) AS solde_calcule,
    COUNT(*) AS nombre_mouvements
FROM promotion_stock_movements m
LEFT JOIN promotion_gammes g ON m.gamme_id = g.id
WHERE (m.from_team_id = @team_id OR m.to_team_id = @team_id)
GROUP BY g.id, g.name
ORDER BY g.name;

-- 5. Comparer avec le stock actuel dans promotion_team_stock
SELECT 
    ts.gamme_id,
    g.name AS gamme_name,
    ts.quantity AS stock_actuel_table,
    (SELECT SUM(CASE 
        WHEN m.to_team_id = @team_id THEN 
            CASE 
                WHEN m.movement_type = 'approvisionnement' THEN m.quantity_change
                WHEN m.movement_type = 'retour' THEN ABS(m.quantity_change)
                ELSE ABS(m.quantity_change)
            END
        WHEN m.from_team_id = @team_id THEN -ABS(m.quantity_change)
        ELSE 0
    END)
    FROM promotion_stock_movements m
    WHERE (m.from_team_id = @team_id OR m.to_team_id = @team_id)
    AND m.gamme_id = ts.gamme_id) AS solde_calcule_mouvements,
    ts.quantity - (SELECT SUM(CASE 
        WHEN m.to_team_id = @team_id THEN 
            CASE 
                WHEN m.movement_type = 'approvisionnement' THEN m.quantity_change
                WHEN m.movement_type = 'retour' THEN ABS(m.quantity_change)
                ELSE ABS(m.quantity_change)
            END
        WHEN m.from_team_id = @team_id THEN -ABS(m.quantity_change)
        ELSE 0
    END)
    FROM promotion_stock_movements m
    WHERE (m.from_team_id = @team_id OR m.to_team_id = @team_id)
    AND m.gamme_id = ts.gamme_id) AS difference
FROM promotion_team_stock ts
JOIN promotion_teams t ON ts.team_id = t.id
LEFT JOIN promotion_gammes g ON ts.gamme_id = g.id
WHERE t.id = @team_id
ORDER BY g.name;

