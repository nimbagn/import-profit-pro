-- Migration PostgreSQL : Ajout du type de mouvement 'reception_return'
-- Date : 2 Janvier 2026
-- Description : Ajoute le type 'reception_return' à l'enum movement_type

-- 1. Ajouter la valeur 'reception_return' à l'enum existant
DO $$ 
BEGIN
    -- Vérifier si la valeur existe déjà
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'reception_return' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
    ) THEN
        ALTER TYPE movement_type ADD VALUE 'reception_return';
    END IF;
END $$;

-- Vérification
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
ORDER BY enumsortorder;

