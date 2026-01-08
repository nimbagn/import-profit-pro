# 📋 Guide : Exécuter la Vérification des Statistiques de Stock sur Render

## 🎯 Objectif

Ce script vérifie et met à jour la base de données PostgreSQL pour s'assurer que :
- Le type `movement_type` inclut bien `'reception_return'`
- Les statistiques de stock sont calculées correctement
- Les sorties incluent bien les ventes et les retours fournisseurs

## 📁 Fichier

`scripts/verify_and_update_stock_statistics_postgresql.sql`

## 🚀 Méthode 1 : Via le Terminal Render (Recommandé)

### Étape 1 : Se connecter au service Render

```bash
# Via SSH (si activé)
render ssh <service-name>

# Ou via le shell du service
# Dans le dashboard Render, allez dans votre service web
# Cliquez sur "Shell" dans le menu latéral
```

### Étape 2 : Naviguer vers le répertoire du projet

```bash
cd ~/project/src
```

### Étape 3 : Exécuter le script SQL

```bash
# Méthode 1 : Via psql avec DATABASE_URL
psql $DATABASE_URL -f scripts/verify_and_update_stock_statistics_postgresql.sql

# Méthode 2 : Si DATABASE_URL n'est pas défini, utilisez la connexion directe
# (Récupérez les credentials depuis le dashboard Render > Database > Internal Database URL)
psql "postgresql://user:password@host:port/database" -f scripts/verify_and_update_stock_statistics_postgresql.sql
```

### Étape 4 : Vérifier les résultats

Le script affichera :
- ✅ Les valeurs de l'enum `movement_type`
- 📊 La répartition des mouvements par type
- 📦 Les statistiques globales (entrées, sorties, stock total)
- ⚠️ Les avertissements éventuels (données incohérentes)

## 🖥️ Méthode 2 : Via le SQL Editor de Render

### Étape 1 : Accéder au SQL Editor

1. Connectez-vous à votre dashboard Render
2. Allez dans votre base de données PostgreSQL
3. Cliquez sur "Connect" ou "SQL Editor"

### Étape 2 : Copier le contenu du script

Ouvrez le fichier `scripts/verify_and_update_stock_statistics_postgresql.sql` et copiez tout son contenu.

### Étape 3 : Coller et exécuter

1. Collez le contenu dans l'éditeur SQL
2. Cliquez sur "Run" ou "Execute"
3. Vérifiez les résultats dans la console

## 📊 Résultats Attendus

### ✅ Succès

Le script devrait afficher :

```
✅ Type movement_type existe déjà
ℹ️  Valeur reception_return existe déjà
📊 Valeurs de movement_type : transfer, reception, reception_return, adjustment, inventory
📦 Total des mouvements de stock : XXX
📊 Répartition des mouvements par type :
   - adjustment : X mouvements (Entrées: X, Sorties: X)
   - reception : X mouvements (Entrées: X, Sorties: 0)
   - reception_return : X mouvements (Entrées: 0, Sorties: X)
   - transfer : X mouvements (Entrées: X, Sorties: X)
📊 STATISTIQUES GLOBALES :
   - Total Entrées : XXX
   - Total Sorties : XXX (inclut ventes + retours fournisseurs)
   - Stock Total (Balance) : XXX
✅ VÉRIFICATION TERMINÉE
```

### ⚠️ Avertissements Possibles

Si vous voyez des avertissements :
- `⚠️ ATTENTION : X réceptions avec quantité négative` → Données incohérentes à corriger
- `⚠️ ATTENTION : X retours fournisseurs avec quantité positive` → Données incohérentes à corriger

## 🔍 Vérification Manuelle (Optionnel)

### Vérifier les valeurs de l'enum

```sql
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
ORDER BY enumsortorder;
```

Résultat attendu :
```
enumlabel
----------
transfer
reception
reception_return
adjustment
inventory
```

### Vérifier les mouvements par type

```sql
SELECT 
    movement_type,
    COUNT(*) as count,
    SUM(CASE WHEN quantity < 0 THEN ABS(quantity) ELSE 0 END) as total_exits,
    SUM(CASE WHEN quantity > 0 THEN quantity ELSE 0 END) as total_entries
FROM stock_movements
GROUP BY movement_type
ORDER BY movement_type;
```

## 🎯 Après l'Exécution

Une fois le script exécuté avec succès :

1. ✅ Le type `reception_return` est disponible dans l'enum
2. ✅ Les statistiques de stock sont calculées correctement
3. ✅ Les sorties incluent bien les ventes et retours fournisseurs
4. ✅ Le code Python (stocks.py, analytics.py) fonctionne correctement

## 🐛 Dépannage

### Erreur : "type movement_type does not exist"

Le script créera automatiquement le type. Si l'erreur persiste, exécutez d'abord :
```sql
CREATE TYPE movement_type AS ENUM ('transfer', 'reception', 'adjustment', 'inventory');
```

### Erreur : "cannot add value to enum type"

Cela signifie que `reception_return` existe déjà. C'est normal, le script gère ce cas.

### Erreur : "permission denied"

Assurez-vous d'être connecté avec un utilisateur ayant les droits `ALTER TYPE` et `SELECT` sur la base de données.

## 📝 Notes

- Ce script est **idempotent** : il peut être exécuté plusieurs fois sans erreur
- Il ne modifie **pas** les données existantes, seulement le schéma si nécessaire
- Il affiche des **statistiques** pour vérifier la cohérence des données

## ✅ Validation

Après exécution, testez dans l'application :
1. Allez sur `/stocks/summary`
2. Vérifiez que les sorties incluent bien les ventes
3. Vérifiez que les retours fournisseurs sont comptabilisés dans les sorties
4. Vérifiez les statistiques sur `/analytics/`

---

**Date de création** : 8 Janvier 2026  
**Dernière mise à jour** : 8 Janvier 2026

