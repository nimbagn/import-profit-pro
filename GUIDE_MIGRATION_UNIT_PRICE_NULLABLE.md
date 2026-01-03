# 📋 Guide de Migration : unit_price_gnf nullable

## 🎯 Objectif

Aligner la base de données locale avec le modèle Python en permettant `NULL` pour la colonne `unit_price_gnf` dans la table `reception_details`.

## 📊 Situation Actuelle

- **Modèle Python** : `unit_price_gnf = db.Column(N18_2, nullable=True)`
- **Base de données** : `unit_price_gnf DECIMAL(18,2) NOT NULL`
- **Incohérence** : Le modèle permet NULL mais la DB ne le permet pas

## ✅ Solution

Modifier la base de données pour permettre NULL, ce qui correspond au modèle Python et offre plus de flexibilité.

---

## 🚀 Méthode 1 : Script Python (Recommandé)

### Exécution

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
python3 scripts/migration_unit_price_gnf_nullable.py
```

### Ce que fait le script

1. ✅ Met à jour les valeurs NULL existantes avec 0
2. ✅ Modifie la colonne pour permettre NULL (MySQL ou PostgreSQL)
3. ✅ Vérifie que la modification a réussi

---

## 🚀 Méthode 2 : SQL Direct

### Pour MySQL

```bash
mysql -u votre_user -p votre_database < scripts/migration_unit_price_gnf_nullable_mysql.sql
```

Ou directement dans MySQL :

```sql
-- Mettre à jour les valeurs NULL existantes
UPDATE reception_details
SET unit_price_gnf = 0
WHERE unit_price_gnf IS NULL;

-- Modifier la colonne pour permettre NULL
ALTER TABLE reception_details
MODIFY COLUMN unit_price_gnf DECIMAL(18,2) NULL;
```

### Pour PostgreSQL

```bash
psql -U votre_user -d votre_database -f scripts/migration_unit_price_gnf_nullable_postgresql.sql
```

Ou directement dans PostgreSQL :

```sql
-- Mettre à jour les valeurs NULL existantes
UPDATE reception_details
SET unit_price_gnf = 0
WHERE unit_price_gnf IS NULL;

-- Modifier la colonne pour permettre NULL
ALTER TABLE reception_details
ALTER COLUMN unit_price_gnf DROP NOT NULL;
```

---

## 🔍 Vérification

### MySQL

```sql
SELECT 
    COLUMN_NAME,
    IS_NULLABLE,
    COLUMN_TYPE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'reception_details'
  AND COLUMN_NAME = 'unit_price_gnf';
```

**Résultat attendu :** `IS_NULLABLE = 'YES'`

### PostgreSQL

```sql
SELECT 
    column_name,
    is_nullable,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'reception_details'
  AND column_name = 'unit_price_gnf';
```

**Résultat attendu :** `is_nullable = true`

---

## ✅ Après la Migration

1. ✅ La colonne `unit_price_gnf` permet maintenant NULL
2. ✅ Le modèle Python et la base de données sont alignés
3. ✅ Le code gère automatiquement les valeurs NULL en utilisant le prix d'achat du StockItem
4. ✅ Plus d'erreur `IntegrityError: Column 'unit_price_gnf' cannot be null`

---

## 📝 Notes

- Les valeurs NULL existantes sont mises à jour avec 0 avant la modification
- Le code dans `stocks.py` garantit qu'une valeur est toujours fournie (soit depuis le formulaire, soit depuis le StockItem, soit 0 par défaut)
- Cette migration est idempotente (peut être exécutée plusieurs fois sans problème)

---

## 🆘 En cas d'erreur

Si vous rencontrez une erreur, vérifiez :

1. ✅ Que vous êtes connecté à la bonne base de données
2. ✅ Que vous avez les permissions nécessaires (ALTER TABLE)
3. ✅ Que la table `reception_details` existe
4. ✅ Que la colonne `unit_price_gnf` existe

Pour annuler la migration (remettre NOT NULL) :

**MySQL:**
```sql
ALTER TABLE reception_details
MODIFY COLUMN unit_price_gnf DECIMAL(18,2) NOT NULL DEFAULT 0;
```

**PostgreSQL:**
```sql
ALTER TABLE reception_details
ALTER COLUMN unit_price_gnf SET NOT NULL;
ALTER TABLE reception_details
ALTER COLUMN unit_price_gnf SET DEFAULT 0;
```

