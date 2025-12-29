# Guide d'Ajout des Colonnes Multi-Devises à la Table Forecasts

## ⚠️ Erreur Actuelle

```
OperationalError: (1054, "Unknown column 'forecasts.currency' in 'field list'")
```

Cette erreur indique que les colonnes `currency`, `rate_usd`, `rate_eur`, et `rate_xof` n'existent pas encore dans la table `forecasts`.

## ✅ Solution

### Option 1 : Script SQL Sécurisé (Recommandé)

Exécutez le script SQL sécurisé qui vérifie l'existence des colonnes avant de les ajouter :

```bash
mysql -h 127.0.0.1 -u root -p madargn < scripts/add_forecast_currency_columns_safe.sql
```

### Option 2 : Script SQL Simple

Si vous êtes sûr que les colonnes n'existent pas :

```bash
mysql -h 127.0.0.1 -u root -p madargn < scripts/add_forecast_currency_columns.sql
```

### Option 3 : Via Client MySQL (phpMyAdmin, MySQL Workbench, etc.)

1. Connectez-vous à votre base de données MySQL
2. Sélectionnez la base `madargn`
3. Exécutez les commandes suivantes :

```sql
-- Ajouter la colonne currency
ALTER TABLE `forecasts` 
ADD COLUMN `currency` VARCHAR(8) NOT NULL DEFAULT 'GNF' AFTER `status`;

-- Ajouter les colonnes de taux de change
ALTER TABLE `forecasts` 
ADD COLUMN `rate_usd` DECIMAL(18,2) NULL AFTER `currency`,
ADD COLUMN `rate_eur` DECIMAL(18,2) NULL AFTER `rate_usd`,
ADD COLUMN `rate_xof` DECIMAL(18,2) NULL AFTER `rate_eur`;
```

## 📋 Colonnes à Ajouter

1. **`currency`** : VARCHAR(8) NOT NULL DEFAULT 'GNF'
   - Devise principale de la prévision (GNF, USD, EUR, XOF)

2. **`rate_usd`** : DECIMAL(18,2) NULL
   - Taux de change USD vers GNF au moment de la création

3. **`rate_eur`** : DECIMAL(18,2) NULL
   - Taux de change EUR vers GNF au moment de la création

4. **`rate_xof`** : DECIMAL(18,2) NULL
   - Taux de change XOF vers GNF au moment de la création

## 🔄 Après l'Ajout

Une fois les colonnes ajoutées, redémarrez l'application Flask. Les routes ont été modifiées pour gérer gracieusement l'absence de ces colonnes, mais elles fonctionneront mieux une fois les colonnes créées.

## ✅ Vérification

Pour vérifier que les colonnes ont été ajoutées :

```sql
DESCRIBE forecasts;
```

Vous devriez voir les colonnes `currency`, `rate_usd`, `rate_eur`, et `rate_xof` dans la liste.

