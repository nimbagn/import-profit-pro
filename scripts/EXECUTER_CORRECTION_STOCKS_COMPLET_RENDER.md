# 🔧 Guide : Corriger TOUTES les Permissions STOCKS du Magasinier sur Render

## 🎯 Problème Identifié

Le magasinier ne parvient pas à travailler sur `/stocks` - il n'a pas accès à toutes les fonctionnalités nécessaires.

## ✅ Solution Complète

### 1. Modifications du Code Python

Le code Python a été modifié pour garantir l'accès du magasinier à **TOUTES** les fonctionnalités STOCKS :
- ✅ Stocks (dépôt, véhicule, résumé)
- ✅ Mouvements (liste, création, modification, suppression)
- ✅ Réceptions (liste, création, détails, PDF, Excel)
- ✅ Sorties (liste, création, détails, PDF, Excel)
- ✅ Retours (liste, création, détails, PDF, Excel)

### 2. Script SQL pour Production

Exécuter le script SQL `scripts/CORRIGER_PERMISSIONS_STOCKS_COMPLET_POSTGRESQL.sql` sur Render.

## 📋 Méthode : SQL Editor sur Render (Recommandé)

1. **Connectez-vous à Render** : https://dashboard.render.com
2. **Allez dans votre base de données PostgreSQL**
3. **Ouvrez l'onglet "SQL Editor"**
4. **Copiez-collez le contenu** du fichier `scripts/CORRIGER_PERMISSIONS_STOCKS_COMPLET_POSTGRESQL.sql`
5. **Cliquez sur "Run"** pour exécuter le script
6. **Vérifiez le résultat** : Vous devriez voir un message de succès

## 📋 Méthode Alternative : Via psql

```bash
# Récupérer la DATABASE_URL depuis Render
# Puis exécuter :
psql $DATABASE_URL -f scripts/CORRIGER_PERMISSIONS_STOCKS_COMPLET_POSTGRESQL.sql
```

## ✅ Vérification

Après l'exécution du script, vérifiez que le magasinier peut :

### Stocks
- ✅ Accéder à `/stocks/depot/<id>` - Stock d'un dépôt
- ✅ Accéder à `/stocks/vehicle/<id>` - Stock d'un véhicule
- ✅ Accéder à `/stocks/summary` - Résumé des stocks
- ✅ Exporter les données (PDF, Excel)

### Mouvements
- ✅ Accéder à `/stocks/movements` - Liste des mouvements
- ✅ Créer des mouvements (`/stocks/movements/new`)
- ✅ Modifier des mouvements (`/stocks/movements/<id>/edit`)
- ✅ Supprimer des mouvements (`/stocks/movements/<id>/delete`)
- ✅ Exporter les mouvements (Excel)

### Réceptions
- ✅ Accéder à `/stocks/receptions` - Liste des réceptions
- ✅ Créer des réceptions (`/stocks/receptions/new`)
- ✅ Voir les détails (`/stocks/receptions/<id>`)
- ✅ Générer des PDF (`/stocks/receptions/<id>/pdf`)
- ✅ Exporter (Excel)

### Sorties
- ✅ Accéder à `/stocks/outgoings` - Liste des sorties
- ✅ Créer des sorties (`/stocks/outgoings/new`)
- ✅ Voir les détails (`/stocks/outgoings/<id>`)
- ✅ Générer des PDF (`/stocks/outgoings/<id>/pdf`)
- ✅ Exporter (Excel)

### Retours
- ✅ Accéder à `/stocks/returns` - Liste des retours
- ✅ Créer des retours (`/stocks/returns/new`)
- ✅ Voir les détails (`/stocks/returns/<id>`)
- ✅ Générer des PDF (`/stocks/returns/<id>/pdf`)
- ✅ Exporter (Excel)

## 🔄 Redémarrage

Après l'exécution du script, **redémarrez l'application** sur Render :
1. Allez dans votre service web sur Render
2. Cliquez sur "Manual Deploy" → "Clear build cache & deploy"

## 📝 Ce que le Script Fait

Le script garantit que le magasinier a **TOUTES** les permissions suivantes :

- ✅ `stocks`: `read`, `create`, `update`
- ✅ `movements`: `read`, `create`, `update`
- ✅ `inventory`: `read`, `create`, `update`
- ✅ `receptions`: `read`, `create`, `update`
- ✅ `outgoings`: `read`, `create`, `update`
- ✅ `returns`: `read`, `create`, `update`
- ✅ `vehicles`: `read`, `create`, `update`
- ✅ `regions`: `read`
- ✅ `depots`: `read`
- ✅ `families`: `read`
- ✅ `stock_items`: `read`
- ✅ `orders`: `read`
- ✅ `stock_loading`: `read`, `verify`, `load`

## ⚠️ Note Importante

Le code Python a également été modifié pour garantir l'accès :
- **Fonctions helper** : `can_access_stocks()`, `can_access_movements()`, etc.
- **Vérification explicite** : Le magasinier (`warehouse`) a toujours accès complet
- **Toutes les routes** : Utilisent maintenant ces nouvelles fonctions

Ces modifications sont dans les commits récents et seront déployées automatiquement après le push Git.

## 🔍 Vérification SQL

Après l'exécution, vous pouvez vérifier avec :

```sql
-- Vérifier les permissions du magasinier
SELECT 
    code,
    permissions->'stocks' as stocks_permissions,
    permissions->'movements' as movements_permissions,
    permissions->'receptions' as receptions_permissions,
    permissions->'outgoings' as outgoings_permissions,
    permissions->'returns' as returns_permissions,
    permissions->'inventory' as inventory_permissions
FROM roles
WHERE code = 'warehouse';
```

## 📞 Support

Si les problèmes persistent après l'exécution du script :
1. Vérifiez les logs de l'application sur Render
2. Vérifiez que les permissions sont bien mises à jour dans la base de données
3. Redémarrez l'application
4. Videz le cache du navigateur
5. Testez avec un compte magasinier

