# 🔧 Guide d'exécution - Fix Permissions RH Assistant et Magasinier

**Date :** 2025-01-07  
**Script :** `scripts/fix_permissions_rh_warehouse_postgresql.sql`

---

## 📋 Problèmes corrigés

### 1. **RH Assistant** - Suivi du personnel
- ❌ **Problème** : L'assistant RH ne pouvait pas accéder aux statistiques (`/rh/statistiques`)
- ✅ **Solution** : Ajout de la permission `analytics.read` au rôle `rh_assistant`

### 2. **Magasinier** - Suivi des véhicules et odomètre
- ❌ **Problème** : Le magasinier ne pouvait pas ajouter de relevés odomètre
- ✅ **Solution** : Ajout de la permission `vehicles.update` au rôle `warehouse`

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
   - Copiez le contenu de `scripts/fix_permissions_rh_warehouse_postgresql.sql`
   - Collez-le dans l'éditeur SQL
   - Cliquez sur **"Run"** ou **"Execute"**

4. **Vérifiez les résultats**
   - Vous devriez voir des messages `NOTICE` confirmant les mises à jour
   - La requête de vérification affiche les permissions mises à jour

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
   psql $DATABASE_URL -f scripts/fix_permissions_rh_warehouse_postgresql.sql
   
   # Option 2 : Via psql avec variables séparées
   psql -h <host> -U <user> -d <dbname> -f scripts/fix_permissions_rh_warehouse_postgresql.sql
   ```

---

## ✅ Vérification

Après l'exécution, vérifiez que les permissions sont correctes :

```sql
SELECT 
    r.code,
    r.name,
    r.permissions->'analytics' as analytics_perms,
    r.permissions->'vehicles' as vehicles_perms
FROM roles r
WHERE r.code IN ('rh_assistant', 'warehouse')
ORDER BY r.code;
```

### Résultats attendus :

| code | name | analytics_perms | vehicles_perms |
|------|------|-----------------|----------------|
| rh_assistant | RH Assistant | `["read"]` | `null` |
| warehouse | Magasinier | `null` | `["read", "update"]` |

---

## 🔍 Dépannage

### Erreur : "Rôle non trouvé"
- Vérifiez que les rôles `rh_assistant` et `warehouse` existent dans la table `roles`
- Exécutez : `SELECT code, name FROM roles WHERE code IN ('rh_assistant', 'warehouse');`

### Erreur : "Permission déjà présente"
- C'est normal, le script est idempotent (peut être exécuté plusieurs fois)
- Les permissions ne seront pas dupliquées

### Erreur : "Syntax error"
- Vérifiez que vous utilisez PostgreSQL (pas MySQL)
- Le script utilise des blocs `DO $$` spécifiques à PostgreSQL

---

## 📝 Notes importantes

1. **Idempotence** : Le script peut être exécuté plusieurs fois sans problème
2. **Sécurité** : Les permissions existantes ne sont pas supprimées, seulement ajoutées
3. **Compatibilité** : Script conçu pour PostgreSQL (Render utilise PostgreSQL)

---

## 🎯 Résultat attendu

Après l'exécution :

✅ **RH Assistant** peut maintenant :
- Accéder à `/rh/statistiques`
- Voir toutes les statistiques d'utilisation
- Faire le suivi complet du personnel

✅ **Magasinier** peut maintenant :
- Accéder à `/vehicles/<id>/odometer`
- Ajouter des relevés odomètre (`/vehicles/<id>/odometer/new`)
- Faire le suivi complet des véhicules

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs dans Render
2. Vérifiez que les rôles existent dans la base de données
3. Vérifiez que les permissions sont au format JSONB

