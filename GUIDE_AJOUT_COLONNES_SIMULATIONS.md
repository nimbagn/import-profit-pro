# 🔧 Guide : Ajouter les colonnes manquantes à la table simulations

## ⚠️ Problème

L'erreur suivante apparaît dans les logs :
```
Unknown column 'simulations.rate_xof' in 'field list'
```

Cela signifie que la table `simulations` dans votre base de données MySQL n'a pas toutes les colonnes nécessaires définies dans le modèle Python.

## ✅ Solution

### Option 1 : Exécuter le script SQL manuellement

1. **Ouvrir un terminal MySQL** :
```bash
mysql -u root -p
```

2. **Sélectionner votre base de données** :
```sql
USE madargn;
-- OU
USE import_profit;
```

3. **Exécuter le script SQL** :
```bash
# Pour la base de données madargn (selon vos logs)
mysql -u root -p madargn < scripts/add_rate_xof_simple.sql

# OU pour la base de données import_profit
mysql -u root -p import_profit < scripts/add_rate_xof_simple.sql
```

**Note** : Si certaines colonnes existent déjà, vous obtiendrez une erreur "Duplicate column name". C'est normal, continuez avec les autres colonnes.

### Option 2 : Exécuter les commandes SQL directement

Connectez-vous à MySQL et exécutez ces commandes une par une :

```sql
USE madargn;  -- Remplacez par votre base de données

-- Ajouter rate_xof
ALTER TABLE simulations 
ADD COLUMN rate_xof DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER rate_eur;

-- Ajouter customs_gnf
ALTER TABLE simulations 
ADD COLUMN customs_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER rate_xof;

-- Ajouter handling_gnf
ALTER TABLE simulations 
ADD COLUMN handling_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER customs_gnf;

-- Ajouter others_gnf
ALTER TABLE simulations 
ADD COLUMN others_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER handling_gnf;

-- Ajouter transport_fixed_gnf
ALTER TABLE simulations 
ADD COLUMN transport_fixed_gnf DECIMAL(18,2) NOT NULL DEFAULT 0.00 AFTER others_gnf;

-- Ajouter transport_per_kg_gnf
ALTER TABLE simulations 
ADD COLUMN transport_per_kg_gnf DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER transport_fixed_gnf;

-- Ajouter basis
ALTER TABLE simulations 
ADD COLUMN basis ENUM('value', 'weight') NOT NULL DEFAULT 'value' AFTER transport_per_kg_gnf;

-- Ajouter truck_capacity_tons
ALTER TABLE simulations 
ADD COLUMN truck_capacity_tons DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER basis;

-- Ajouter target_mode
ALTER TABLE simulations 
ADD COLUMN target_mode ENUM('none', 'price', 'purchase', 'global') NOT NULL DEFAULT 'none' AFTER truck_capacity_tons;

-- Ajouter target_margin_pct
ALTER TABLE simulations 
ADD COLUMN target_margin_pct DECIMAL(18,4) NOT NULL DEFAULT 0.0000 AFTER target_mode;
```

### Option 3 : Vérifier les colonnes existantes

Pour voir quelles colonnes existent déjà :

```sql
SHOW COLUMNS FROM simulations;
```

## 📋 Colonnes à ajouter

Les colonnes suivantes doivent être présentes dans la table `simulations` :

1. `rate_xof` - Taux de change XOF vers GNF
2. `customs_gnf` - Coûts de douane
3. `handling_gnf` - Coûts de manutention
4. `others_gnf` - Autres coûts
5. `transport_fixed_gnf` - Transport fixe
6. `transport_per_kg_gnf` - Transport par kg
7. `basis` - Base de calcul (value/weight)
8. `truck_capacity_tons` - Capacité du camion
9. `target_mode` - Mode de cible
10. `target_margin_pct` - Marge cible en pourcentage

## ✅ Vérification

Après avoir exécuté les commandes, vérifiez que toutes les colonnes sont présentes :

```sql
SHOW COLUMNS FROM simulations;
```

Vous devriez voir toutes les colonnes listées ci-dessus.

## 🔄 Créer les tables des Fiches de Prix

Si vous venez d'ajouter la fonctionnalité des Fiches de Prix, créez aussi les tables nécessaires :

```bash
mysql -u root -p madargn < scripts/create_price_lists_tables.sql
```

## 🔄 Redémarrer l'application

Après avoir ajouté les colonnes et créé les tables, redémarrez l'application Flask :

```bash
python3 app.py
```

Les erreurs devraient disparaître.

