# 🔧 Guide : Corriger les Permissions Admin et Magasinier sur Render

## 🎯 Problèmes Identifiés

1. **Admin** : Erreur 500 sur `/automated-reports/1/edit` - L'admin n'a plus accès
2. **Magasinier** : Ne peut pas faire de sorties de stock sur `/stocks/outgoings`

## ✅ Solution

Exécuter le script SQL `scripts/CORRIGER_PERMISSIONS_PRODUCTION_POSTGRESQL.sql` sur Render.

## 📋 Méthode : SQL Editor sur Render (Recommandé)

1. **Connectez-vous à Render** : https://dashboard.render.com
2. **Allez dans votre base de données PostgreSQL**
3. **Ouvrez l'onglet "SQL Editor"**
4. **Copiez-collez le contenu** du fichier `scripts/CORRIGER_PERMISSIONS_PRODUCTION_POSTGRESQL.sql`
5. **Cliquez sur "Run"** pour exécuter le script
6. **Vérifiez le résultat** : Vous devriez voir des messages de succès

## 📋 Méthode Alternative : Via psql

```bash
# Récupérer la DATABASE_URL depuis Render
# Puis exécuter :
psql $DATABASE_URL -f scripts/CORRIGER_PERMISSIONS_PRODUCTION_POSTGRESQL.sql
```

## ✅ Vérification

Après l'exécution du script, vérifiez que :

### Admin
- ✅ Peut accéder à `/automated-reports/1/edit`
- ✅ Peut créer et modifier des rapports automatiques
- ✅ A les permissions `messaging.read`, `messaging.update`, etc.

### Magasinier
- ✅ Peut accéder à `/stocks/outgoings`
- ✅ Peut créer des sorties (`/stocks/outgoings/new`)
- ✅ A les permissions `outgoings.read`, `outgoings.create`, `outgoings.update`

## 🔄 Redémarrage

Après l'exécution du script, **redémarrez l'application** sur Render :
1. Allez dans votre service web sur Render
2. Cliquez sur "Manual Deploy" → "Clear build cache & deploy"

## 📝 Ce que le Script Fait

### Pour l'Admin
- Ajoute les permissions `messaging` si elles manquent
- Permissions ajoutées : `read`, `update`, `send_sms`, `send_whatsapp`, `send_otp`, `manage_contacts`

### Pour le Magasinier
- Vérifie et complète les permissions `outgoings`
- Permissions garanties : `read`, `create`, `update`

## ⚠️ Note Importante

Le code Python a également été modifié pour garantir l'accès :
- **Admin** : Accès garanti aux rapports automatiques (vérification explicite du rôle)
- **Magasinier** : Accès garanti aux sorties de stock (vérification explicite du rôle)

Ces modifications sont dans les commits récents et seront déployées automatiquement après le push Git.

## 🔍 Vérification SQL

Après l'exécution, vous pouvez vérifier avec :

```sql
-- Vérifier les permissions admin
SELECT code, permissions->'messaging' as messaging_permissions
FROM roles
WHERE code IN ('admin', 'superadmin');

-- Vérifier les permissions magasinier
SELECT code, 
       permissions->'outgoings' as outgoings_permissions,
       permissions->'receptions' as receptions_permissions,
       permissions->'returns' as returns_permissions
FROM roles
WHERE code = 'warehouse';
```

## 📞 Support

Si les problèmes persistent après l'exécution du script :
1. Vérifiez les logs de l'application sur Render
2. Vérifiez que les permissions sont bien mises à jour dans la base de données
3. Redémarrez l'application
4. Videz le cache du navigateur

