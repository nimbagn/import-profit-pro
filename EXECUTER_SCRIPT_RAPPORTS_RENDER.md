# 📋 Guide d'Exécution du Script SQL sur Render

## 🎯 Objectif

Créer la table `scheduled_reports` dans votre base de données PostgreSQL sur Render pour activer le système de rapports automatiques.

## 📝 Méthode 1 : SQL Editor (Recommandé)

### Étapes :

1. **Connectez-vous à votre dashboard Render**
   - Allez sur https://dashboard.render.com
   - Sélectionnez votre service de base de données PostgreSQL

2. **Ouvrez le SQL Editor**
   - Cliquez sur l'onglet **"SQL Editor"** dans le menu de votre base de données
   - Ou utilisez le lien direct : `https://dashboard.render.com/web/[votre-db-id]/sql`

3. **Copiez et collez le script**
   - Ouvrez le fichier `scripts/add_scheduled_reports_table_postgresql_render.sql`
   - Copiez tout le contenu
   - Collez-le dans l'éditeur SQL de Render

4. **Exécutez le script**
   - Cliquez sur **"Run"** ou **"Execute"**
   - Attendez la confirmation de succès

5. **Vérifiez le résultat**
   - Vous devriez voir des messages `✅` indiquant que la table a été créée
   - La dernière requête `SELECT` affichera la structure de la table

## 📝 Méthode 2 : Via psql (Ligne de commande)

### Prérequis :
- Avoir `psql` installé localement
- Avoir l'URL de connexion de votre base de données Render

### Étapes :

1. **Récupérez votre DATABASE_URL depuis Render**
   - Dans votre dashboard Render → Base de données PostgreSQL
   - Copiez la **"Internal Database URL"** ou **"External Database URL"**

2. **Exécutez le script**
```bash
# Depuis votre machine locale
psql "votre_database_url_ici" -f scripts/add_scheduled_reports_table_postgresql_render.sql
```

**Exemple :**
```bash
psql "postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com/dbname" -f scripts/add_scheduled_reports_table_postgresql_render.sql
```

## 📝 Méthode 3 : Via Render Shell (SSH)

Si vous avez accès au shell Render :

1. **Connectez-vous au shell de votre service web**
   - Dashboard Render → Votre service web → Shell

2. **Exécutez psql**
```bash
# Récupérer la DATABASE_URL depuis les variables d'environnement
export DATABASE_URL=$(echo $DATABASE_URL)

# Exécuter le script
psql $DATABASE_URL -f scripts/add_scheduled_reports_table_postgresql_render.sql
```

## ✅ Vérification

Après l'exécution, vérifiez que la table existe :

```sql
-- Vérifier que la table existe
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'scheduled_reports'
);

-- Voir la structure
\d scheduled_reports

-- Compter les rapports (devrait être 0 au début)
SELECT COUNT(*) FROM scheduled_reports;
```

## 🔍 Résolution de Problèmes

### Erreur : "type already exists"
✅ **Normal** : Le script est idempotent, cette erreur est gérée automatiquement.

### Erreur : "relation does not exist" (pour depots ou users)
⚠️ **Solution** : Exécutez d'abord le script de migration complet (`migration_postgresql_render_complete.sql`) pour créer toutes les tables de base.

### Erreur : "permission denied"
⚠️ **Solution** : Vérifiez que vous utilisez le bon utilisateur avec les permissions nécessaires.

## 📊 Après l'Installation

Une fois la table créée :

1. **Redémarrez votre service web** sur Render pour que l'application charge les rapports actifs
2. **Accédez à l'interface** : `/automated-reports/` dans votre application
3. **Créez votre premier rapport automatique** !

## 🎯 Prochaines Étapes

Consultez le guide complet : `GUIDE_RAPPORTS_AUTOMATIQUES.md` pour apprendre à utiliser le système de rapports automatiques.

