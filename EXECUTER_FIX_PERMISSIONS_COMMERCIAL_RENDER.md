# 🔧 Guide d'exécution - Fix Permissions Commercial Orders

**Date :** 2025-01-07  
**Script :** `scripts/fix_commercial_orders_permissions_postgresql.sql`

---

## 📋 Problème identifié

Le commercial ne voit plus le bouton **"Nouvelle Commande"** sur la page `/orders/`.

**Cause probable :** Les permissions `orders.create` ne sont pas correctement synchronisées dans la base de données PostgreSQL sur Render.

---

## 🚀 Méthode 1 : SQL Editor (Recommandé)

### Étapes :

1. **Connectez-vous à Render**
   - Allez sur https://dashboard.render.com
   - Sélectionnez votre service web

2. **Ouvrez le SQL Editor**
   - Dans le menu de gauche, cliquez sur **"PostgreSQL"** ou **"Database"**
   - Cliquez sur **"SQL Editor"** ou **"Connect"**

3. **Exécutez le script**
   - Copiez le contenu de `scripts/fix_commercial_orders_permissions_postgresql.sql`
   - Collez-le dans l'éditeur SQL
   - Cliquez sur **"Run"** ou **"Execute"**

4. **Vérifiez les résultats**
   - Vous devriez voir des messages `NOTICE` confirmant les mises à jour
   - La requête de vérification finale affiche les permissions avec des ✅ ou ❌

---

## 🖥️ Méthode 2 : Ligne de commande (psql)

### Étapes :

1. **Connectez-vous au shell Render**
   ```bash
   # Via le dashboard Render, ouvrez le shell de votre service web
   ```

2. **Récupérez la DATABASE_URL**
   ```bash
   echo $DATABASE_URL
   # Notez l'URL complète (format: postgresql://user:password@host:port/dbname)
   ```

3. **Exécutez le script**
   ```bash
   # Option 1 : Via psql avec l'URL complète
   psql $DATABASE_URL -f scripts/fix_commercial_orders_permissions_postgresql.sql
   
   # Option 2 : Via psql avec variables séparées
   psql -h <host> -U <user> -d <dbname> -f scripts/fix_commercial_orders_permissions_postgresql.sql
   ```

---

## ✅ Vérification

Après l'exécution, vérifiez que les permissions sont correctes :

```sql
SELECT 
    r.code,
    r.name,
    r.permissions->'orders' as orders_permissions
FROM roles r
WHERE r.code = 'commercial';
```

### Résultat attendu :

| code | name | orders_permissions |
|------|------|-------------------|
| commercial | Commercial | `["read", "create", "update"]` |

---

## 🔍 Dépannage

### Erreur : "Rôle commercial non trouvé"
- Vérifiez que le rôle `commercial` existe dans la table `roles`
- Exécutez : `SELECT code, name FROM roles WHERE code = 'commercial';`

### Le bouton ne s'affiche toujours pas
1. **Vérifiez que l'utilisateur a bien le rôle commercial :**
   ```sql
   SELECT u.id, u.username, u.full_name, r.code, r.name
   FROM users u
   JOIN roles r ON u.role_id = r.id
   WHERE u.username = '<nom_utilisateur>';
   ```

2. **Vérifiez les permissions du rôle :**
   ```sql
   SELECT permissions->'orders' as orders_perms
   FROM roles
   WHERE code = 'commercial';
   ```

3. **Déconnectez et reconnectez-vous** pour que les permissions soient rechargées

4. **Videz le cache du navigateur** (Ctrl+Shift+R ou Cmd+Shift+R)

---

## 📝 Notes importantes

1. **Idempotence** : Le script peut être exécuté plusieurs fois sans problème
2. **Sécurité** : Les permissions existantes ne sont pas supprimées, seulement ajoutées
3. **Compatibilité** : Script conçu pour PostgreSQL (Render utilise PostgreSQL)

---

## 🎯 Résultat attendu

Après l'exécution :

✅ **Commercial** peut maintenant :
- Voir le bouton **"Nouvelle Commande"** sur `/orders/`
- Créer de nouvelles commandes (`/orders/new`)
- Modifier ses commandes (`/orders/<id>/edit`)
- Voir uniquement ses propres commandes

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs dans Render
2. Vérifiez que le rôle existe dans la base de données
3. Vérifiez que les permissions sont au format JSONB
4. Déconnectez et reconnectez-vous après la mise à jour

