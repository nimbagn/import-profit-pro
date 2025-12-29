# Guide de Création des Tables Forecast

## 📋 Vue d'ensemble

Les tables `forecasts` et `forecast_items` seront créées automatiquement par SQLAlchemy lors du prochain démarrage de l'application Flask.

## ✅ Méthode Automatique (Recommandée)

Les modèles `Forecast` et `ForecastItem` ont été ajoutés dans `models.py`. SQLAlchemy créera automatiquement les tables lors du démarrage si elles n'existent pas déjà.

**Aucune action manuelle requise** - redémarrez simplement l'application Flask.

## 🔧 Méthode Manuelle (Alternative)

Si vous préférez créer les tables manuellement, vous pouvez exécuter le script SQL :

### Option 1 : Via MySQL en ligne de commande

```bash
mysql -h 127.0.0.1 -u root -p madargn < scripts/create_forecast_tables.sql
```

### Option 2 : Via un client MySQL (phpMyAdmin, MySQL Workbench, etc.)

1. Ouvrez le fichier `scripts/create_forecast_tables.sql`
2. Copiez le contenu
3. Exécutez-le dans votre client MySQL

## 📊 Structure des Tables

### Table `forecasts`
- `id` : Identifiant unique
- `name` : Nom de la prévision
- `description` : Description optionnelle
- `start_date` : Date de début
- `end_date` : Date de fin
- `status` : Statut (draft, active, completed, archived)
- `total_forecast_value` : Valeur prévisionnelle totale
- `total_realized_value` : Valeur réalisée totale
- `created_by_id` : Utilisateur créateur
- `created_at` / `updated_at` : Timestamps

### Table `forecast_items`
- `id` : Identifiant unique
- `forecast_id` : Référence à la prévision
- `stock_item_id` : Référence à l'article de stock
- `forecast_quantity` : Quantité prévue
- `selling_price_gnf` : Prix de vente en gros (GNF)
- `realized_quantity` : Quantité moyenne réalisée
- `realized_value_gnf` : Valeur réalisée (GNF)
- `realization_percentage` : Pourcentage de réalisation
- `equivalent_quantity` : Quantité équivalente (EQ)
- `evaluated_value` : Valeur évaluée (EVal)
- `evaluated_value_cfa` : Valeur évaluée en CFA
- `deviation_50pct` : Écart à 50%
- `quantity_available` : Quantité disponible (QAF)
- `number_of_days` : Nombre de jours
- `created_at` / `updated_at` : Timestamps

## 🚀 Vérification

Après le démarrage de l'application, vous pouvez vérifier que les tables existent :

1. Accédez à `http://localhost:5002/forecast`
2. Si le dashboard s'affiche sans erreur, les tables sont créées ✅
3. Si vous voyez une erreur de table manquante, exécutez le script SQL manuellement

## 📝 Notes

- Les tables sont créées avec les contraintes de clés étrangères appropriées
- Les index sont créés pour optimiser les requêtes
- Les relations avec `users` et `stock_items` sont configurées








