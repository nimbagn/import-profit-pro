# 📋 Guide de Migration : Ajout colonne reference dans stock_movements

## 🎯 Objectif

Ajouter la colonne `reference` à la table `stock_movements` pour correspondre au modèle Python.

## 📊 Situation Actuelle

- **Modèle Python** : `reference = db.Column(db.String(50), nullable=True, unique=True, index=True)`
- **Base de données** : La colonne `reference` peut être absente dans certains schémas SQL
- **Incohérence** : Le modèle définit `reference` mais elle peut manquer dans la DB

## ✅ Solution

Ajouter la colonne `reference` à la table `stock_movements` si elle n'existe pas déjà.

---

## 🚀 Méthode 1 : Script Python (Recommandé)

### Exécution

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
python3 scripts/migration_add_reference_stock_movements.py
```

### Ce que fait le script

1. ✅ Vérifie si la colonne `reference` existe déjà
2. ✅ Ajoute la colonne si elle n'existe pas (MySQL ou PostgreSQL)
3. ✅ Crée l'index unique si nécessaire
4. ✅ Vérifie que la création a réussi

---

## 🚀 Méthode 2 : SQL Direct

### Pour MySQL

```bash
mysql -u votre_user -p votre_database < scripts/migration_add_reference_stock_movements_mysql.sql
```

Ou directement dans MySQL :

```sql
-- Vérifier si la colonne existe
SELECT COUNT(*) 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'stock_movements'
  AND COLUMN_NAME = 'reference';

-- Ajouter la colonne si elle n'existe pas
ALTER TABLE stock_movements 
ADD COLUMN reference VARCHAR(50) NULL UNIQUE AFTER id;

-- Créer l'index
CREATE INDEX idx_movement_reference ON stock_movements(reference);
```

### Pour PostgreSQL

```bash
psql -U votre_user -d votre_database -f scripts/migration_add_reference_stock_movements_postgresql.sql
```

Ou directement dans PostgreSQL :

```sql
-- Ajouter la colonne si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
          AND table_name = 'stock_movements'
          AND column_name = 'reference'
    ) THEN
        ALTER TABLE stock_movements 
        ADD COLUMN reference VARCHAR(50) NULL;
        
        CREATE UNIQUE INDEX idx_movement_reference ON stock_movements(reference);
    END IF;
END $$;
```

---

## 🔍 Vérification

### MySQL

```sql
SELECT 
    COLUMN_NAME,
    IS_NULLABLE,
    COLUMN_TYPE,
    COLUMN_KEY
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'stock_movements'
  AND COLUMN_NAME = 'reference';
```

**Résultat attendu :** Une ligne avec `COLUMN_NAME = 'reference'` et `COLUMN_KEY = 'UNI'`

### PostgreSQL

```sql
SELECT 
    column_name,
    is_nullable,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'stock_movements'
  AND column_name = 'reference';
```

**Résultat attendu :** Une ligne avec `column_name = 'reference'`

---

## ✅ Après la Migration

1. ✅ La colonne `reference` existe dans `stock_movements`
2. ✅ La colonne est unique (contrainte UNIQUE)
3. ✅ La colonne est indexée pour améliorer les performances
4. ✅ Le modèle Python et la base de données sont alignés
5. ✅ Les mouvements de stock peuvent avoir une référence unique

---

## 📝 Notes

- Cette migration est idempotente (peut être exécutée plusieurs fois sans problème)
- La colonne est `nullable=True` car certains mouvements peuvent ne pas avoir de référence
- L'index unique garantit qu'aucune référence n'est dupliquée
- Les mouvements existants auront `reference = NULL` jusqu'à ce qu'ils soient mis à jour

---

## 🔗 Relation avec les Transferts

La colonne `reference` est utilisée pour :
- ✅ Identifier de manière unique chaque mouvement de stock
- ✅ Générer des références automatiques pour les transferts (ex: `TRF-20260102-ABC123`)
- ✅ Tracer les mouvements dans l'historique
- ✅ Lier les mouvements SORTIE et ENTRÉE lors des transferts

---

## 🆘 En cas d'erreur

Si vous rencontrez une erreur, vérifiez :

1. ✅ Que vous êtes connecté à la bonne base de données
2. ✅ Que vous avez les permissions nécessaires (ALTER TABLE, CREATE INDEX)
3. ✅ Que la table `stock_movements` existe
4. ✅ Que la colonne n'existe pas déjà (le script le vérifie automatiquement)

Pour vérifier manuellement si la colonne existe :

**MySQL:**
```sql
SHOW COLUMNS FROM stock_movements LIKE 'reference';
```

**PostgreSQL:**
```sql
\d stock_movements
```

