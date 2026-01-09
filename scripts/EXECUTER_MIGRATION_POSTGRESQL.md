# 🚀 Guide d'exécution des migrations PostgreSQL

## 📋 Scripts à exécuter dans l'ordre

### 1. Migration principale (OBLIGATOIRE)

Ce script crée toutes les tables et colonnes nécessaires pour le système de supervision commerciale et de confirmation des ventes.

```bash
psql -U votre_utilisateur -d votre_base_de_donnees -f scripts/create_commercial_teams_and_sales_postgresql.sql
```

**Ce script crée/modifie :**
- ✅ Tables `lockiste_teams` et `lockiste_members`
- ✅ Tables `vendeur_teams` et `vendeur_members`
- ✅ Table `commercial_sales` et `commercial_sale_items`
- ✅ Table `sales_objectives` et `sales_objective_items`
- ✅ Colonnes dans `users` (`supervised_team_id`, `supervised_team_type`)
- ✅ Colonnes dans `promotion_teams` (`supervisor_id`, `region_id`)
- ✅ Colonnes dans `promotion_members` (`home_latitude`, `home_longitude`, `intermediaire_id`)
- ✅ Colonnes dans `commercial_orders` (`sale_confirmed`, `sale_confirmed_at`, `sale_confirmed_by_id`)
- ✅ Colonne `forecast_id` dans `sales_objectives` (si la table existe déjà)
- ✅ Tous les index et contraintes nécessaires

### 2. Permissions (OPTIONNEL - si vous utilisez le système de rôles)

Ce script ajoute les permissions nécessaires au rôle superviseur.

```bash
psql -U votre_utilisateur -d votre_base_de_donnees -f scripts/add_commercial_teams_sales_permissions_postgresql.sql
```

**Ce script ajoute :**
- ✅ Permission `commercial_teams.read` et `commercial_teams.write`
- ✅ Permission `sales.confirm` et `sales.view_confirmed`
- ✅ Permission `objectives.read` et `objectives.write`

## 📝 Exemple d'exécution complète

```bash
# Se connecter à PostgreSQL
psql -U postgres -d madargn

# Exécuter la migration principale
\i scripts/create_commercial_teams_and_sales_postgresql.sql

# Exécuter le script de permissions (optionnel)
\i scripts/add_commercial_teams_sales_permissions_postgresql.sql

# Vérifier que tout s'est bien passé
\dt lockiste*
\dt vendeur*
\dt commercial_sales*
\dt sales_objective*

# Quitter
\q
```

## ✅ Vérification post-migration

### Vérifier les tables créées

```sql
-- Lister toutes les nouvelles tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'lockiste_teams', 'lockiste_members', 
    'vendeur_teams', 'vendeur_members',
    'commercial_sales', 'commercial_sale_items',
    'sales_objectives', 'sales_objective_items'
)
ORDER BY table_name;
```

### Vérifier les colonnes ajoutées

```sql
-- Vérifier les colonnes dans users
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('supervised_team_id', 'supervised_team_type');

-- Vérifier les colonnes dans promotion_teams
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'promotion_teams' 
AND column_name IN ('supervisor_id', 'region_id');

-- Vérifier les colonnes dans promotion_members
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'promotion_members' 
AND column_name IN ('home_latitude', 'home_longitude', 'intermediaire_id');

-- Vérifier les colonnes dans commercial_orders
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'commercial_orders' 
AND column_name IN ('sale_confirmed', 'sale_confirmed_at', 'sale_confirmed_by_id');

-- Vérifier la colonne forecast_id dans sales_objectives
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'sales_objectives' 
AND column_name = 'forecast_id';
```

### Vérifier les index créés

```sql
-- Vérifier les index sur lockiste_teams
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'lockiste_teams';

-- Vérifier les index sur commercial_sales
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'commercial_sales';

-- Vérifier les index sur sales_objectives
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'sales_objectives';
```

### Vérifier les contraintes de clés étrangères

```sql
-- Vérifier les FK sur lockiste_teams
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_name IN (
    'lockiste_teams', 'lockiste_members',
    'vendeur_teams', 'vendeur_members',
    'commercial_sales', 'commercial_sale_items',
    'sales_objectives', 'sales_objective_items'
)
ORDER BY tc.table_name, kcu.column_name;
```

## 🔒 Sécurité et bonnes pratiques

1. **Sauvegarde** : Toujours faire une sauvegarde avant d'exécuter les migrations
   ```bash
   pg_dump -U votre_utilisateur -d votre_base_de_donnees > backup_avant_migration_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test** : Tester d'abord sur un environnement de développement

3. **Permissions** : S'assurer d'avoir les droits nécessaires
   ```sql
   -- Vérifier les permissions
   SELECT current_user, current_database();
   ```

4. **Transaction** : Les scripts utilisent `BEGIN` et `COMMIT` pour garantir l'intégrité

## 🐛 Dépannage

### Erreur : "relation already exists"
- ✅ Normal si vous réexécutez le script (idempotent)
- Le script utilise `CREATE TABLE IF NOT EXISTS` donc c'est sans danger

### Erreur : "column already exists"
- ✅ Normal si vous réexécutez le script (idempotent)
- Le script vérifie l'existence avant d'ajouter les colonnes

### Erreur : "permission denied"
- Vérifiez que vous avez les droits CREATE, ALTER sur la base de données
- Contactez votre administrateur de base de données

### Erreur : "foreign key constraint fails"
- Vérifiez que toutes les tables référencées existent (users, regions, stock_items, forecasts, etc.)
- Vérifiez que les données existantes respectent les contraintes

## 📊 Statistiques post-migration

```sql
-- Compter les tables créées
SELECT COUNT(*) as nombre_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'lockiste_teams', 'lockiste_members', 
    'vendeur_teams', 'vendeur_members',
    'commercial_sales', 'commercial_sale_items',
    'sales_objectives', 'sales_objective_items'
);

-- Vérifier la taille des nouvelles tables
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'lockiste_teams', 'lockiste_members', 
    'vendeur_teams', 'vendeur_members',
    'commercial_sales', 'commercial_sale_items',
    'sales_objectives', 'sales_objective_items'
)
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## ✅ Checklist de migration

- [ ] Sauvegarde de la base de données effectuée
- [ ] Script de migration principale exécuté avec succès
- [ ] Script de permissions exécuté (si nécessaire)
- [ ] Toutes les tables créées vérifiées
- [ ] Toutes les colonnes ajoutées vérifiées
- [ ] Tous les index créés vérifiés
- [ ] Application redémarrée et testée
- [ ] Fonctionnalités testées dans l'interface

## 📞 Support

En cas de problème, consultez :
- Les logs PostgreSQL : `/var/log/postgresql/` ou `journalctl -u postgresql`
- La documentation du projet
- L'équipe de développement

---

**Date de création** : 2026-01-03  
**Version** : 1.0  
**Compatibilité** : PostgreSQL 9.5+

