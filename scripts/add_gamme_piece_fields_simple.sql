-- Script SIMPLE pour ajouter les champs de pièce/unitaire à la table promotion_gammes
-- Version simplifiée - Exécutez ce script dans votre base de données MySQL
-- Si les colonnes existent déjà, vous obtiendrez une erreur que vous pouvez ignorer

USE madargn;  -- Remplacez par le nom de votre base de données

-- Ajouter les colonnes pour les pièces/unités
-- Note: Si une colonne existe déjà, vous obtiendrez une erreur "Duplicate column name"
-- C'est normal, vous pouvez l'ignorer ou commenter la ligne correspondante

ALTER TABLE promotion_gammes
ADD COLUMN is_piece BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Indique si c''est une pièce/unitaire';

ALTER TABLE promotion_gammes
ADD COLUMN unit_type VARCHAR(100) NULL COMMENT 'Type d''unité: bouteille, pièce, sachet, etc.';

ALTER TABLE promotion_gammes
ADD COLUMN unit_description VARCHAR(500) NULL COMMENT 'Description de l''unité: 800 ml, 1 kg, etc.';

-- Ajouter des index pour améliorer les performances
-- Note: Si l'index existe déjà, vous obtiendrez une erreur "Duplicate key name"
-- C'est normal, vous pouvez l'ignorer ou commenter la ligne correspondante

CREATE INDEX idx_promogamme_piece ON promotion_gammes(is_piece);
CREATE INDEX idx_promogamme_unit_type ON promotion_gammes(unit_type);

-- Afficher la structure de la table pour vérification
DESCRIBE promotion_gammes;

