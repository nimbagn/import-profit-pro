# 🔧 GUIDE : CORRECTION stock_movements SUR RENDER

**Date :** 2 Janvier 2026

---

## 📋 PROBLÈME

La route `/stocks/movements` ne fonctionne pas sur Render car la table `stock_movements` n'est pas complètement configurée dans PostgreSQL.

---

## 🔧 SOLUTION

Le script `scripts/fix_stock_movements_postgresql.sql` corrige :
1. ✅ Type ENUM `movement_type` avec toutes les valeurs
2. ✅ Colonne `reference` (si manquante)
3. ✅ Toutes les contraintes de clés étrangères
4. ✅ Tous les index nécessaires pour les performances
5. ✅ Vérifications complètes

---

## 🚀 EXÉCUTION SUR RENDER

### Méthode 1 : Via Shell PostgreSQL

1. **Accéder au Shell PostgreSQL sur Render**
   - Dashboard Render → Service PostgreSQL → Shell/Connect

2. **Copier le contenu du script**
   - Ouvrir `scripts/fix_stock_movements_postgresql.sql`
   - Copier tout le contenu

3. **Coller et exécuter dans le terminal PostgreSQL**

```bash
# Se connecter à PostgreSQL
psql $DATABASE_URL

# Coller le contenu du script et exécuter
```

### Méthode 2 : Via commande directe

```bash
psql $DATABASE_URL < scripts/fix_stock_movements_postgresql.sql
```

---

## ✅ VÉRIFICATION

Après l'exécution, vérifiez que tout est correct :

```sql
-- Vérifier la structure de la table
\d stock_movements

-- Vérifier les index
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'stock_movements';

-- Vérifier les contraintes FK
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE conrelid = 'stock_movements'::regclass
AND contype = 'f';

-- Vérifier le type ENUM
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
ORDER BY enumsortorder;

-- Tester une requête simple
SELECT COUNT(*) FROM stock_movements;
```

---

## 📦 COLONNES VÉRIFIÉES

Le script vérifie et crée si nécessaire :

- ✅ `id` (BIGSERIAL PRIMARY KEY)
- ✅ `reference` (VARCHAR(50), nullable, unique)
- ✅ `movement_type` (ENUM avec toutes les valeurs)
- ✅ `movement_date` (TIMESTAMP)
- ✅ `stock_item_id` (BIGINT, FK vers stock_items)
- ✅ `quantity` (NUMERIC(18,4))
- ✅ `user_id` (BIGINT, FK vers users)
- ✅ `from_depot_id` (BIGINT, FK vers depots)
- ✅ `from_vehicle_id` (BIGINT, FK vers vehicles)
- ✅ `to_depot_id` (BIGINT, FK vers depots)
- ✅ `to_vehicle_id` (BIGINT, FK vers vehicles)
- ✅ `supplier_name` (VARCHAR(120))
- ✅ `bl_number` (VARCHAR(50))
- ✅ `reason` (TEXT)
- ✅ `inventory_session_id` (BIGINT, FK vers inventory_sessions)
- ✅ `created_at` (TIMESTAMP)

---

## 🔍 INDEX CRÉÉS

- ✅ `idx_movement_date` - Pour les filtres par date
- ✅ `idx_movement_type` - Pour les filtres par type
- ✅ `idx_movement_item` - Pour les jointures avec stock_items
- ✅ `idx_movement_user` - Pour les filtres par utilisateur
- ✅ `idx_movement_reference` - Unique pour les références
- ✅ `idx_movement_from_depot` - Pour les filtres par dépôt source
- ✅ `idx_movement_to_depot` - Pour les filtres par dépôt destination
- ✅ `idx_movement_from_vehicle` - Pour les filtres par véhicule source
- ✅ `idx_movement_to_vehicle` - Pour les filtres par véhicule destination

---

## 🔗 CONTRAINTES FK

- ✅ `fk_movements_item` → `stock_items(id)`
- ✅ `fk_movements_user` → `users(id)`
- ✅ `fk_movements_from_depot` → `depots(id)`
- ✅ `fk_movements_from_vehicle` → `vehicles(id)`
- ✅ `fk_movements_to_depot` → `depots(id)`
- ✅ `fk_movements_to_vehicle` → `vehicles(id)`
- ✅ `fk_movements_inventory_session` → `inventory_sessions(id)` (si la table existe)

---

## ⚠️ NOTES IMPORTANTES

1. **Idempotence** : Le script est idempotent et peut être exécuté plusieurs fois
2. **Transaction** : Utilise `BEGIN`/`COMMIT` pour garantir l'intégrité
3. **Index unique sur reference** : Créé avec `WHERE reference IS NOT NULL` pour permettre plusieurs NULL
4. **Type ENUM** : Ajoute `reception_return` si elle n'existe pas

---

## 🐛 EN CAS D'ERREUR

Si une erreur survient :

1. **Vérifier les logs** : Regardez les messages `RAISE NOTICE` dans le script
2. **Vérifier les dépendances** : Assurez-vous que les tables `stock_items`, `users`, `depots`, `vehicles` existent
3. **Vérifier les permissions** : L'utilisateur PostgreSQL doit avoir les droits nécessaires
4. **Rollback automatique** : Le script utilise une transaction, donc en cas d'erreur, tout sera annulé

---

## ✅ CHECKLIST

Avant d'exécuter :

- [ ] Backup de la base de données effectué
- [ ] Script téléchargé/copié
- [ ] Accès au shell PostgreSQL sur Render
- [ ] Tables dépendantes existent (stock_items, users, depots, vehicles)

Après l'exécution :

- [ ] Vérification de la structure de la table
- [ ] Vérification des index
- [ ] Vérification des contraintes FK
- [ ] Test de la route `/stocks/movements` dans l'application

---

**✅ Après l'exécution, la route `/stocks/movements` devrait fonctionner correctement !**

