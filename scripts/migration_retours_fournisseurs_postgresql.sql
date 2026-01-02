-- Migration PostgreSQL : Ajout des champs pour retours fournisseurs
-- Date : 2 Janvier 2026
-- Description : Ajoute les colonnes nécessaires pour gérer les retours fournisseurs (mouvement inverse des réceptions)

-- 1. Créer le type ENUM pour return_type si il n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'return_type') THEN
        CREATE TYPE return_type AS ENUM ('client', 'supplier');
    END IF;
END $$;

-- 2. Ajouter la colonne return_type
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'return_type'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN return_type return_type NOT NULL DEFAULT 'client';
    END IF;
END $$;

-- 3. Ajouter la colonne supplier_name
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'supplier_name'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN supplier_name VARCHAR(120) NULL;
    END IF;
END $$;

-- 4. Ajouter la colonne original_reception_id
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_returns' AND column_name = 'original_reception_id'
    ) THEN
        ALTER TABLE stock_returns 
        ADD COLUMN original_reception_id BIGINT NULL;
        
        -- Ajouter la contrainte de clé étrangère
        ALTER TABLE stock_returns 
        ADD CONSTRAINT fk_return_reception 
            FOREIGN KEY (original_reception_id) 
            REFERENCES receptions(id) 
            ON UPDATE CASCADE 
            ON DELETE SET NULL;
    END IF;
END $$;

-- 5. Modifier client_name pour être nullable
DO $$ 
BEGIN
    ALTER TABLE stock_returns 
    ALTER COLUMN client_name DROP NOT NULL;
EXCEPTION
    WHEN OTHERS THEN
        -- La colonne est peut-être déjà nullable, on continue
        NULL;
END $$;

-- 6. Ajouter les index
CREATE INDEX IF NOT EXISTS idx_return_type ON stock_returns(return_type);
CREATE INDEX IF NOT EXISTS idx_return_reception ON stock_returns(original_reception_id);

-- Vérification
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_schema = current_schema()
    AND table_name = 'stock_returns'
    AND column_name IN ('return_type', 'supplier_name', 'original_reception_id', 'client_name')
ORDER BY ordinal_position;

