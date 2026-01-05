# Guide : Créer la table api_configs sur Render

## 🎯 Objectif

Créer la table `api_configs` dans la base de données PostgreSQL sur Render pour permettre la configuration de l'API Message Pro depuis l'interface web.

## 📋 Méthode 1 : SQL Editor (Recommandé)

1. **Connectez-vous à Render** : https://dashboard.render.com
2. **Allez dans votre base de données PostgreSQL**
3. **Ouvrez l'onglet "SQL Editor"**
4. **Copiez-collez le contenu** du fichier `scripts/create_api_configs_table_postgresql.sql`
5. **Cliquez sur "Run"** pour exécuter le script
6. **Vérifiez le résultat** : Vous devriez voir des messages de succès

## 📋 Méthode 2 : Via psql (Ligne de commande)

Si vous avez accès au shell de Render ou à votre machine locale avec `psql` :

```bash
# Récupérer la DATABASE_URL depuis Render
# Puis exécuter :
psql $DATABASE_URL -f scripts/create_api_configs_table_postgresql.sql
```

Ou directement :

```bash
psql "postgresql://user:password@host:port/database" -f scripts/create_api_configs_table_postgresql.sql
```

## ✅ Vérification

Après l'exécution du script, vous pouvez vérifier que la table a été créée :

```sql
SELECT * FROM api_configs;
```

## 🔄 Utilisation

Une fois la table créée, vous pouvez :

1. **Accéder à la configuration** : `/messaging/config`
2. **Entrer votre clé API** Message Pro
3. **Tester la connexion** automatiquement
4. **Enregistrer la clé** dans la base de données

## 📝 Note

- La clé API est stockée en clair dans la base de données (pour simplicité)
- Pour une sécurité renforcée, vous pouvez chiffrer la clé avant de l'enregistrer
- La clé peut également être configurée via la variable d'environnement `MESSAGEPRO_API_SECRET`
- Si les deux sont configurées, la clé de la base de données a la priorité

## ⚠️ Important

Après l'exécution du script, **redémarrez l'application** sur Render pour que les changements prennent effet :
1. Allez dans votre service web sur Render
2. Cliquez sur "Manual Deploy" → "Clear build cache & deploy"

