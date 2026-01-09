# Scripts de Migration - Système de Supervision Commerciale et Confirmation des Ventes

## 📋 Vue d'ensemble

Ce dossier contient les scripts de migration pour le système de supervision commerciale et de confirmation des ventes.

## 📁 Fichiers disponibles

### 1. Scripts de migration de base de données

#### PostgreSQL
- **`create_commercial_teams_and_sales_postgresql.sql`** : Script complet et idempotent pour PostgreSQL
  - Crée toutes les tables nécessaires
  - Ajoute toutes les colonnes manquantes
  - Crée tous les index et contraintes
  - Compatible avec PostgreSQL 9.5+

#### MySQL
- **`create_commercial_teams_and_sales_mysql.sql`** : Script complet et idempotent pour MySQL
  - Crée toutes les tables nécessaires
  - Ajoute toutes les colonnes manquantes
  - Crée tous les index et contraintes
  - Compatible avec MySQL 5.7+ / MariaDB 10.2+

### 2. Scripts de permissions

- **`add_commercial_teams_sales_permissions_postgresql.sql`** : Ajoute les permissions nécessaires au rôle superviseur dans PostgreSQL

## 🚀 Instructions d'exécution

### Pour PostgreSQL

```bash
# 1. Exécuter le script de migration principal
psql -U votre_utilisateur -d votre_base_de_donnees -f scripts/create_commercial_teams_and_sales_postgresql.sql

# 2. Exécuter le script de permissions (optionnel, si vous utilisez le système de rôles)
psql -U votre_utilisateur -d votre_base_de_donnees -f scripts/add_commercial_teams_sales_permissions_postgresql.sql
```

### Pour MySQL

```bash
# Exécuter le script de migration principal
mysql -u votre_utilisateur -p votre_base_de_donnees < scripts/create_commercial_teams_and_sales_mysql.sql
```

## 📊 Tables créées/modifiées

### Tables créées
- `lockiste_teams` - Équipes de lockistes
- `lockiste_members` - Membres des équipes lockistes
- `vendeur_teams` - Équipes de vendeurs
- `vendeur_members` - Membres des équipes vendeurs
- `commercial_sales` - Ventes confirmées
- `commercial_sale_items` - Détails des ventes confirmées
- `sales_objectives` - Objectifs de vente
- `sales_objective_items` - Articles des objectifs de vente

### Tables modifiées
- `users` - Ajout de `supervised_team_id` et `supervised_team_type`
- `promotion_teams` - Ajout de `supervisor_id` et `region_id`
- `promotion_members` - Ajout de `home_latitude`, `home_longitude`, `intermediaire_id`
- `commercial_orders` - Ajout de `sale_confirmed`, `sale_confirmed_at`, `sale_confirmed_by_id`
- `sales_objectives` - Ajout de `forecast_id` (si la table existe déjà)

## ✅ Vérification post-migration

Après l'exécution des scripts, vérifiez que :

1. Toutes les tables existent :
```sql
-- PostgreSQL
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'lockiste_teams', 'lockiste_members', 
    'vendeur_teams', 'vendeur_members',
    'commercial_sales', 'commercial_sale_items',
    'sales_objectives', 'sales_objective_items'
);

-- MySQL
SHOW TABLES LIKE 'lockiste%';
SHOW TABLES LIKE 'vendeur%';
SHOW TABLES LIKE 'commercial_sales%';
SHOW TABLES LIKE 'sales_objective%';
```

2. Les colonnes ont été ajoutées :
```sql
-- PostgreSQL
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('supervised_team_id', 'supervised_team_type');

-- MySQL
DESCRIBE users;
```

## 🔒 Sécurité

- Les scripts sont idempotents et peuvent être exécutés plusieurs fois sans erreur
- Toutes les contraintes de clés étrangères sont définies avec les actions appropriées
- Les index sont créés pour optimiser les performances

## 📝 Notes importantes

- **Backup** : Toujours faire une sauvegarde de votre base de données avant d'exécuter les scripts de migration
- **Test** : Testez d'abord sur un environnement de développement
- **Permissions** : Assurez-vous d'avoir les permissions nécessaires pour créer des tables et modifier le schéma

## 🐛 Dépannage

Si vous rencontrez des erreurs :

1. Vérifiez que vous avez les permissions nécessaires
2. Vérifiez que toutes les tables référencées existent (users, regions, stock_items, forecasts, etc.)
3. Vérifiez les logs d'erreur de votre base de données
4. Assurez-vous que le script correspond à votre version de base de données

## 📞 Support

Pour toute question ou problème, consultez la documentation du projet ou contactez l'équipe de développement.

