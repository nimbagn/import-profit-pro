# 🚀 Guide de Déploiement en Production

## 📋 Vue d'ensemble

Ce guide explique comment déployer toutes les nouvelles fonctionnalités en production, notamment la gestion de la flotte pour le magasinier.

## ⚠️ Problème Identifié

La gestion de la flotte côté magasinier fonctionne localement mais pas en ligne car :
1. Les permissions dans la base de données de production ne sont pas à jour
2. Les scripts SQL de migration n'ont pas été exécutés en production

## ✅ Solution

### Étape 1 : Exécuter le Script de Migration Complète

**Pour PostgreSQL (Render, Heroku, etc.) :**

```bash
# Option 1 : Via psql en ligne de commande
psql $DATABASE_URL -f scripts/MIGRATION_COMPLETE_PRODUCTION_POSTGRESQL.sql

# Option 2 : Via l'interface Render
# 1. Aller dans votre base de données PostgreSQL sur Render
# 2. Ouvrir l'onglet "SQL Editor"
# 3. Copier-coller le contenu de scripts/MIGRATION_COMPLETE_PRODUCTION_POSTGRESQL.sql
# 4. Exécuter le script
```

**Pour MySQL :**

```bash
mysql -u USERNAME -p DATABASE_NAME < scripts/create_commercial_teams_and_sales_mysql.sql
mysql -u USERNAME -p DATABASE_NAME < scripts/ajouter_permissions_flotte_magasinier_mysql.sql
```

### Étape 2 : Vérifier les Permissions

Après l'exécution du script, vérifiez que les permissions sont correctes :

**PostgreSQL :**
```sql
-- Vérifier les permissions du magasinier
SELECT code, permissions->'vehicles' as vehicles_permissions
FROM roles
WHERE code = 'warehouse';

-- Résultat attendu : ["read", "create", "update"]
```

**MySQL :**
```sql
SELECT code, JSON_EXTRACT(permissions, '$.vehicles') as vehicles_permissions
FROM roles
WHERE code = 'warehouse';
```

### Étape 3 : Redéployer l'Application

1. **Vérifier que tous les fichiers sont commités :**
```bash
git status
git add -A
git commit -m "feat: Mise à jour complète pour production"
```

2. **Pousser vers le dépôt distant :**
```bash
git push origin main
```

3. **Sur Render/Heroku :**
   - L'application se redéploiera automatiquement
   - Vérifier les logs pour s'assurer qu'il n'y a pas d'erreurs

### Étape 4 : Tester en Production

1. **Se connecter avec un compte magasinier**
2. **Accéder au module Flotte** (`/flotte/dashboard`)
3. **Vérifier que :**
   - ✅ Le magasinier peut voir tous les véhicules
   - ✅ Le magasinier peut créer des documents véhicules
   - ✅ Le magasinier peut modifier les documents véhicules
   - ✅ Le magasinier peut accéder aux maintenances
   - ✅ Le magasinier peut saisir l'odomètre

## 📊 Contenu de la Migration

Le script `MIGRATION_COMPLETE_PRODUCTION_POSTGRESQL.sql` inclut :

### 1. Permissions Flotte Magasinier
- ✅ Ajout de `vehicles.create` au rôle warehouse
- ✅ Permissions complètes : `read`, `create`, `update`

### 2. Système de Supervision Commerciale
- ✅ Colonnes dans `users` (supervised_team_id, supervised_team_type)
- ✅ Colonnes dans `promotion_teams` (supervisor_id, region_id)
- ✅ Colonnes dans `promotion_members` (home_latitude, home_longitude, intermediaire_id)
- ✅ Colonnes dans `commercial_orders` (sale_confirmed, sale_confirmed_at, sale_confirmed_by_id)

### 3. Tables Équipes Commerciales
- ✅ `lockiste_teams` et `lockiste_members`
- ✅ `vendeur_teams` et `vendeur_members`

### 4. Tables Ventes Confirmées
- ✅ `commercial_sales` et `commercial_sale_items`

### 5. Tables Objectifs de Vente
- ✅ `sales_objectives` et `sales_objective_items`

### 6. Permissions Superviseur
- ✅ `commercial_teams`, `sales`, `objectives`

## 🔍 Dépannage

### Problème : Le magasinier ne peut toujours pas accéder à la flotte

**Solution :**
1. Vérifier que le script SQL a été exécuté avec succès
2. Vérifier les logs de l'application pour les erreurs
3. Vérifier que l'utilisateur a bien le rôle `warehouse`
4. Vider le cache de l'application si nécessaire

### Problème : Erreur lors de l'exécution du script SQL

**Solution :**
1. Vérifier que vous êtes connecté à la bonne base de données
2. Vérifier que vous avez les droits d'administration
3. Exécuter le script section par section si nécessaire
4. Vérifier les logs PostgreSQL pour plus de détails

### Problème : L'application ne se redéploie pas

**Solution :**
1. Vérifier que le push Git a réussi
2. Vérifier les logs de déploiement sur Render/Heroku
3. Redémarrer manuellement l'application si nécessaire

## 📝 Checklist de Déploiement

- [ ] Script SQL exécuté avec succès
- [ ] Permissions vérifiées dans la base de données
- [ ] Code poussé vers le dépôt distant
- [ ] Application redéployée
- [ ] Tests fonctionnels effectués
- [ ] Magasinier peut accéder à la flotte
- [ ] Magasinier peut créer/modifier des documents
- [ ] Notifications automatiques fonctionnent
- [ ] Système de supervision commerciale opérationnel

## 🔗 Fichiers de Migration

- `scripts/MIGRATION_COMPLETE_PRODUCTION_POSTGRESQL.sql` : Script complet PostgreSQL
- `scripts/create_commercial_teams_and_sales_mysql.sql` : Script MySQL équivalent
- `scripts/ajouter_permissions_flotte_magasinier_postgresql.sql` : Permissions flotte PostgreSQL
- `scripts/ajouter_permissions_flotte_magasinier_mysql.sql` : Permissions flotte MySQL

## 📞 Support

En cas de problème, vérifier :
1. Les logs de l'application
2. Les logs de la base de données
3. La documentation dans `scripts/README_MIGRATION.md`
4. Les guides spécifiques dans `scripts/`

