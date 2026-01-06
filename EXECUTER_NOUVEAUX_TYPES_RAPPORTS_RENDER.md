# 📊 Guide : Ajouter les Nouveaux Types de Rapports sur Render

## 🎯 Objectif

Ajouter les nouveaux types de rapports automatiques à la base de données PostgreSQL sur Render :
- `orders_summary` - Résumé des Commandes
- `sales_statistics` - Statistiques de Ventes
- `stock_alerts` - Alertes Stock Faible
- `daily_summary` - Résumé Quotidien

## 📋 Méthode 1 : SQL Editor (Recommandé)

1. **Accéder au SQL Editor sur Render** :
   - Connectez-vous à votre dashboard Render
   - Allez dans votre base de données PostgreSQL
   - Cliquez sur "SQL Editor" ou "Connect"

2. **Copier le script** :
   - Ouvrez le fichier `scripts/add_new_report_types_postgresql.sql`
   - Copiez tout le contenu

3. **Exécuter le script** :
   - Collez le script dans l'éditeur SQL
   - Cliquez sur "Run" ou exécutez la requête
   - Vérifiez qu'il n'y a pas d'erreurs

## 📋 Méthode 2 : Via psql (Ligne de commande)

Si vous avez accès à `psql` :

```bash
# Se connecter à la base de données
psql $DATABASE_URL

# Exécuter le script
\i scripts/add_new_report_types_postgresql.sql

# Ou directement :
psql $DATABASE_URL -f scripts/add_new_report_types_postgresql.sql
```

## ✅ Vérification

Après l'exécution, vérifiez que les nouveaux types ont été ajoutés :

```sql
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'report_type_enum')
ORDER BY enumsortorder;
```

Vous devriez voir :
- `stock_inventory`
- `stock_summary`
- `orders_summary` ✅
- `sales_statistics` ✅
- `stock_alerts` ✅
- `daily_summary` ✅

## 🚀 Après l'exécution

1. Redéployez l'application sur Render (ou attendez le redéploiement automatique)
2. Les nouveaux types de rapports seront disponibles dans le formulaire de création
3. Vous pourrez créer des rapports automatiques pour tous les types de statistiques

## ⚠️ Notes

- Le script est **idempotent** : il peut être exécuté plusieurs fois sans erreur
- Les types existants ne seront pas modifiés
- Seuls les nouveaux types seront ajoutés

