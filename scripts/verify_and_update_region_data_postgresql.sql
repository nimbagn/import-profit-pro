-- Script de vérification et mise à jour des données pour le filtrage par région
-- PostgreSQL - Import Profit Pro
-- Ce script vérifie et met à jour les données nécessaires pour le filtrage par région

-- ============================================================
-- 1. VÉRIFICATION ET MISE À JOUR DES UTILISATEURS
-- ============================================================
-- Les utilisateurs non-admin doivent avoir une région assignée

-- Afficher les utilisateurs sans région (sauf admins)
SELECT 
    u.id,
    u.username,
    u.email,
    r.name as role_name,
    r.code as role_code,
    u.region_id
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.region_id IS NULL 
  AND r.code NOT IN ('admin', 'superadmin')
  AND u.is_active = true;

-- Mise à jour : Assigner une région par défaut aux utilisateurs sans région
-- ATTENTION : Modifiez la région par défaut selon vos besoins
-- Cette requête assigne la première région disponible (vous devrez peut-être ajuster)
DO $$
DECLARE
    default_region_id BIGINT;
BEGIN
    -- Récupérer la première région disponible
    SELECT id INTO default_region_id FROM regions ORDER BY id LIMIT 1;
    
    IF default_region_id IS NOT NULL THEN
        -- Mettre à jour les utilisateurs non-admin sans région
        UPDATE users u
        SET region_id = default_region_id
        FROM roles r
        WHERE u.role_id = r.id
          AND u.region_id IS NULL
          AND r.code NOT IN ('admin', 'superadmin')
          AND u.is_active = true;
        
        RAISE NOTICE 'Mise à jour des utilisateurs sans région : % utilisateur(s) mis à jour', SQL%ROWCOUNT;
    ELSE
        RAISE NOTICE 'Aucune région trouvée dans la base de données. Veuillez créer au moins une région.';
    END IF;
END $$;

-- ============================================================
-- 2. VÉRIFICATION DES DÉPÔTS
-- ============================================================
-- Tous les dépôts doivent avoir une région (obligatoire dans le modèle)

-- Afficher les dépôts sans région (ne devrait pas y en avoir)
SELECT 
    d.id,
    d.name,
    d.region_id
FROM depots d
WHERE d.region_id IS NULL;

-- Si des dépôts n'ont pas de région, assigner la première région disponible
DO $$
DECLARE
    default_region_id BIGINT;
BEGIN
    SELECT id INTO default_region_id FROM regions ORDER BY id LIMIT 1;
    
    IF default_region_id IS NOT NULL THEN
        UPDATE depots
        SET region_id = default_region_id
        WHERE region_id IS NULL;
        
        RAISE NOTICE 'Mise à jour des dépôts sans région : % dépôt(s) mis à jour', SQL%ROWCOUNT;
    END IF;
END $$;

-- ============================================================
-- 3. VÉRIFICATION ET MISE À JOUR DES COMMANDES COMMERCIALES
-- ============================================================
-- Les commandes doivent avoir la région du commercial qui les a créées

-- Afficher les commandes sans région
SELECT 
    co.id,
    co.reference,
    co.commercial_id,
    u.username as commercial_username,
    u.region_id as commercial_region_id,
    co.region_id as order_region_id
FROM commercial_orders co
JOIN users u ON co.commercial_id = u.id
WHERE co.region_id IS NULL
  AND u.region_id IS NOT NULL;

-- Mettre à jour les commandes sans région avec la région du commercial
UPDATE commercial_orders co
SET region_id = u.region_id
FROM users u
WHERE co.commercial_id = u.id
  AND co.region_id IS NULL
  AND u.region_id IS NOT NULL;

-- Afficher le résultat
SELECT 
    COUNT(*) as commandes_mises_a_jour
FROM commercial_orders
WHERE region_id IS NOT NULL;

-- ============================================================
-- 4. VÉRIFICATION DES VÉHICULES
-- ============================================================
-- Les véhicules doivent être liés à un conducteur qui a une région

-- Afficher les véhicules dont le conducteur n'a pas de région
SELECT 
    v.id,
    v.plate_number,
    v.current_user_id,
    u.username as driver_username,
    u.region_id as driver_region_id
FROM vehicles v
JOIN users u ON v.current_user_id = u.id
WHERE u.region_id IS NULL
  AND v.status = 'active';

-- Note : Les véhicules sont filtrés via le conducteur, donc si le conducteur n'a pas de région,
-- le véhicule ne sera pas visible pour les utilisateurs filtrés par région.
-- C'est normal et attendu.

-- ============================================================
-- 5. VÉRIFICATION DES EMPLOYÉS (RH)
-- ============================================================
-- Les employés doivent avoir une région assignée

-- Afficher les employés sans région
SELECT 
    e.id,
    e.first_name,
    e.last_name,
    e.region_id
FROM employees e
WHERE e.region_id IS NULL
  AND e.employment_status = 'active';

-- Mise à jour : Assigner une région par défaut aux employés sans région
DO $$
DECLARE
    default_region_id BIGINT;
BEGIN
    SELECT id INTO default_region_id FROM regions ORDER BY id LIMIT 1;
    
    IF default_region_id IS NOT NULL THEN
        UPDATE employees
        SET region_id = default_region_id
        WHERE region_id IS NULL
          AND employment_status = 'active';
        
        RAISE NOTICE 'Mise à jour des employés sans région : % employé(s) mis à jour', SQL%ROWCOUNT;
    END IF;
END $$;

-- ============================================================
-- 6. RAPPORT FINAL DE VÉRIFICATION
-- ============================================================

-- Statistiques par région
SELECT 
    r.id,
    r.name as region_name,
    r.code as region_code,
    COUNT(DISTINCT u.id) as users_count,
    COUNT(DISTINCT d.id) as depots_count,
    COUNT(DISTINCT v.id) as vehicles_count,
    COUNT(DISTINCT co.id) as orders_count,
    COUNT(DISTINCT e.id) as employees_count
FROM regions r
LEFT JOIN users u ON r.id = u.region_id AND u.is_active = true
LEFT JOIN depots d ON r.id = d.region_id AND d.is_active = true
LEFT JOIN vehicles v ON v.current_user_id = u.id AND v.status = 'active'
LEFT JOIN commercial_orders co ON r.id = co.region_id
LEFT JOIN employees e ON r.id = e.region_id AND e.employment_status = 'active'
GROUP BY r.id, r.name, r.code
ORDER BY r.name;

-- Utilisateurs sans région (sauf admins)
SELECT 
    COUNT(*) as users_without_region
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.region_id IS NULL 
  AND r.code NOT IN ('admin', 'superadmin')
  AND u.is_active = true;

-- Dépôts sans région
SELECT 
    COUNT(*) as depots_without_region
FROM depots
WHERE region_id IS NULL;

-- Commandes sans région
SELECT 
    COUNT(*) as orders_without_region
FROM commercial_orders
WHERE region_id IS NULL;

-- Employés sans région
SELECT 
    COUNT(*) as employees_without_region
FROM employees
WHERE region_id IS NULL
  AND employment_status = 'active';

