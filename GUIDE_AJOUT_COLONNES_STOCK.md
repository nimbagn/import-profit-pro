# Guide d'ajout des colonnes manquantes aux tables de stock

## Problème

Les tables `stock_movements` et `stock_returns` ont des colonnes manquantes dans la base de données MySQL :
- `stock_movements.reference` : Référence unique pour chaque mouvement
- `stock_returns.original_outgoing_id` : Lien vers la sortie originale
- `stock_returns.reference` : Référence unique pour chaque retour

## Solution

### Option 1 : Script SQL (Recommandé)

Exécutez les scripts SQL suivants dans MySQL :

```bash
mysql -u root -p madargn < scripts/add_stock_movements_reference.sql
mysql -u root -p madargn < scripts/add_stock_returns_columns.sql
```

### Option 2 : Script Python

Exécutez le script Python (nécessite que la connexion MySQL fonctionne) :

```bash
python3 scripts/fix_stock_tables.py
```

### Option 3 : SQL manuel

Connectez-vous à MySQL et exécutez :

```sql
USE madargn;

-- Ajouter reference à stock_movements
ALTER TABLE stock_movements 
ADD COLUMN reference VARCHAR(50) NULL,
ADD UNIQUE INDEX idx_movement_reference (reference);

-- Ajouter original_outgoing_id à stock_returns
ALTER TABLE stock_returns 
ADD COLUMN original_outgoing_id BIGINT UNSIGNED NULL,
ADD INDEX idx_return_outgoing (original_outgoing_id),
ADD CONSTRAINT fk_returns_outgoing 
    FOREIGN KEY (original_outgoing_id) 
    REFERENCES stock_outgoings(id) 
    ON UPDATE CASCADE ON DELETE SET NULL;

-- Ajouter reference à stock_returns (si elle n'existe pas)
ALTER TABLE stock_returns 
ADD COLUMN reference VARCHAR(50) NULL,
ADD UNIQUE INDEX idx_return_reference (reference);
```

## Note

L'application fonctionne maintenant même si ces colonnes n'existent pas grâce aux gestionnaires d'erreur ajoutés. Cependant, pour une fonctionnalité complète, il est recommandé d'ajouter ces colonnes.

