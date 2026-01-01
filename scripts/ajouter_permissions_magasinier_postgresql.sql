-- Script SQL pour ajouter les permissions manquantes au rôle magasinier (PostgreSQL)
-- Permissions à ajouter: receptions et returns

DO $$
DECLARE
    warehouse_role_id INTEGER;
    current_permissions JSONB;
    new_permissions JSONB;
BEGIN
    -- Récupérer l'ID du rôle magasinier
    SELECT id INTO warehouse_role_id
    FROM roles
    WHERE code = 'warehouse';
    
    IF warehouse_role_id IS NULL THEN
        RAISE EXCEPTION 'Le rôle magasinier (warehouse) n''existe pas';
    END IF;
    
    -- Récupérer les permissions actuelles
    SELECT permissions INTO current_permissions
    FROM roles
    WHERE id = warehouse_role_id;
    
    -- Initialiser new_permissions avec les permissions actuelles
    new_permissions := COALESCE(current_permissions, '{}'::JSONB);
    
    -- Ajouter les permissions receptions si elles n'existent pas
    IF NOT (new_permissions ? 'receptions') THEN
        new_permissions := new_permissions || '{"receptions": ["read", "create", "update"]}'::JSONB;
    ELSE
        -- Si receptions existe déjà, s'assurer qu'il contient read, create, update
        IF NOT (new_permissions->'receptions' ? 'read') THEN
            new_permissions := jsonb_set(new_permissions, '{receptions}', 
                (new_permissions->'receptions') || '["read"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'receptions' ? 'create') THEN
            new_permissions := jsonb_set(new_permissions, '{receptions}', 
                (new_permissions->'receptions') || '["create"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'receptions' ? 'update') THEN
            new_permissions := jsonb_set(new_permissions, '{receptions}', 
                (new_permissions->'receptions') || '["update"]'::JSONB);
        END IF;
    END IF;
    
    -- Ajouter les permissions outgoings si elles n'existent pas
    IF NOT (new_permissions ? 'outgoings') THEN
        new_permissions := new_permissions || '{"outgoings": ["read", "create", "update"]}'::JSONB;
    ELSE
        -- Si outgoings existe déjà, s'assurer qu'il contient read, create, update
        IF NOT (new_permissions->'outgoings' ? 'read') THEN
            new_permissions := jsonb_set(new_permissions, '{outgoings}', 
                (new_permissions->'outgoings') || '["read"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'outgoings' ? 'create') THEN
            new_permissions := jsonb_set(new_permissions, '{outgoings}', 
                (new_permissions->'outgoings') || '["create"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'outgoings' ? 'update') THEN
            new_permissions := jsonb_set(new_permissions, '{outgoings}', 
                (new_permissions->'outgoings') || '["update"]'::JSONB);
        END IF;
    END IF;
    
    -- Ajouter les permissions returns si elles n'existent pas
    IF NOT (new_permissions ? 'returns') THEN
        new_permissions := new_permissions || '{"returns": ["read", "create", "update"]}'::JSONB;
    ELSE
        -- Si returns existe déjà, s'assurer qu'il contient read, create, update
        IF NOT (new_permissions->'returns' ? 'read') THEN
            new_permissions := jsonb_set(new_permissions, '{returns}', 
                (new_permissions->'returns') || '["read"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'returns' ? 'create') THEN
            new_permissions := jsonb_set(new_permissions, '{returns}', 
                (new_permissions->'returns') || '["create"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'returns' ? 'update') THEN
            new_permissions := jsonb_set(new_permissions, '{returns}', 
                (new_permissions->'returns') || '["update"]'::JSONB);
        END IF;
    END IF;
    
    -- Ajouter les permissions orders si elles n'existent pas
    IF NOT (new_permissions ? 'orders') THEN
        new_permissions := new_permissions || '{"orders": ["read"]}'::JSONB;
    ELSE
        -- Si orders existe déjà, s'assurer qu'il contient read
        IF NOT (new_permissions->'orders' ? 'read') THEN
            new_permissions := jsonb_set(new_permissions, '{orders}', 
                (new_permissions->'orders') || '["read"]'::JSONB);
        END IF;
    END IF;
    
    -- Ajouter les permissions stock_loading si elles n'existent pas
    IF NOT (new_permissions ? 'stock_loading') THEN
        new_permissions := new_permissions || '{"stock_loading": ["read", "verify", "load"]}'::JSONB;
    ELSE
        -- Si stock_loading existe déjà, s'assurer qu'il contient read, verify, load
        IF NOT (new_permissions->'stock_loading' ? 'read') THEN
            new_permissions := jsonb_set(new_permissions, '{stock_loading}', 
                (new_permissions->'stock_loading') || '["read"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'stock_loading' ? 'verify') THEN
            new_permissions := jsonb_set(new_permissions, '{stock_loading}', 
                (new_permissions->'stock_loading') || '["verify"]'::JSONB);
        END IF;
        IF NOT (new_permissions->'stock_loading' ? 'load') THEN
            new_permissions := jsonb_set(new_permissions, '{stock_loading}', 
                (new_permissions->'stock_loading') || '["load"]'::JSONB);
        END IF;
    END IF;
    
    -- Mettre à jour les permissions
    UPDATE roles
    SET permissions = new_permissions
    WHERE id = warehouse_role_id;
    
    RAISE NOTICE 'Permissions du rôle magasinier mises à jour avec succès';
    RAISE NOTICE 'Nouvelles permissions: %', new_permissions;
END $$;

