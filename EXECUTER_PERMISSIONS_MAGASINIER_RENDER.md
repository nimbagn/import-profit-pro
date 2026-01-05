# Guide : Exécuter les Permissions Magasinier sur Render

## 🔍 Problème

Le magasinier n'a pas accès à `/stocks/outgoings` car les permissions ne sont pas à jour dans la base de données PostgreSQL sur Render.

## ✅ Solution

Exécuter le script SQL `scripts/ajouter_permissions_magasinier_postgresql.sql` sur Render.

## 📋 Méthode 1 : SQL Editor (Recommandé)

1. **Connectez-vous à Render** : https://dashboard.render.com
2. **Allez dans votre base de données PostgreSQL**
3. **Ouvrez l'onglet "SQL Editor"**
4. **Copiez-collez le contenu** du fichier `scripts/ajouter_permissions_magasinier_postgresql.sql`
5. **Cliquez sur "Run"** pour exécuter le script
6. **Vérifiez le résultat** : Vous devriez voir un message de succès

## 📋 Méthode 2 : Via psql (Ligne de commande)

Si vous avez accès au shell de Render ou à votre machine locale avec `psql` :

```bash
# Récupérer la DATABASE_URL depuis Render
# Puis exécuter :
psql $DATABASE_URL -f scripts/ajouter_permissions_magasinier_postgresql.sql
```

Ou directement :

```bash
psql "postgresql://user:password@host:port/database" -f scripts/ajouter_permissions_magasinier_postgresql.sql
```

## ✅ Vérification

Après l'exécution du script, le magasinier devrait avoir accès à :
- ✅ `/stocks/outgoings` - Liste des sorties
- ✅ `/stocks/outgoings/new` - Créer une sortie
- ✅ `/stocks/receptions` - Liste des réceptions
- ✅ `/stocks/returns` - Liste des retours

## 🔄 Redémarrage

Après l'exécution du script, **redémarrez l'application** sur Render pour que les changements prennent effet :
1. Allez dans votre service web sur Render
2. Cliquez sur "Manual Deploy" → "Clear build cache & deploy"

## 📝 Permissions Ajoutées

Le script ajoute les permissions suivantes au rôle magasinier :
- `outgoings`: `read`, `create`, `update`
- `receptions`: `read`, `create`, `update`
- `returns`: `read`, `create`, `update`
- `orders`: `read`
- `stock_loading`: `read`, `verify`, `load`

## ⚠️ Note

Le script est **idempotent** : vous pouvez l'exécuter plusieurs fois sans problème. Il vérifie si les permissions existent déjà avant de les ajouter.

