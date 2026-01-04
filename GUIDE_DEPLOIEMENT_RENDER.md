# 🚀 Guide de Déploiement sur Render

## 📋 Prérequis

1. Compte Render (gratuit disponible)
2. Repository Git (GitHub, GitLab, etc.)
3. Base de données PostgreSQL sur Render

---

## 🔧 Étape 1 : Préparation du Repository

### 1.1 Vérifier les fichiers nécessaires

Assurez-vous que ces fichiers existent :
- ✅ `requirements.txt` - Dépendances Python
- ✅ `render.yaml` - Configuration Render
- ✅ `wsgi.py` - Point d'entrée WSGI
- ✅ `scripts/migration_postgresql_render_complete.sql` - Script SQL

### 1.2 Pousser le code sur Git

```bash
git add .
git commit -m "feat: Préparation déploiement Render"
git push origin main
```

---

## 🗄️ Étape 2 : Créer la Base de Données PostgreSQL

### 2.1 Dans Render Dashboard

1. Cliquez sur **"New +"** → **"PostgreSQL"**
2. Configurez :
   - **Name** : `import-profit-db`
   - **Database** : `madargn`
   - **User** : `madargn_user`
   - **Plan** : `Free` (ou plan payant selon vos besoins)
3. Cliquez sur **"Create Database"**

### 2.2 Initialiser la Base de Données

1. Dans votre base PostgreSQL, allez dans **"Connect"**
2. Copiez l'**Internal Database URL**
3. Utilisez l'éditeur SQL de Render ou connectez-vous via `psql` :

```bash
# Via psql (si vous avez accès)
# Option 1 : Avec variable d'environnement DATABASE_URL
psql "$DATABASE_URL" -f scripts/migration_postgresql_render_complete.sql

# Option 2 : Avec URL complète (remplacez les valeurs)
psql "postgresql://user:password@host:port/database" -f scripts/migration_postgresql_render_complete.sql

# Option 3 : Avec paramètres séparés
psql -h hostname -U username -d database -f scripts/migration_postgresql_render_complete.sql
```

**OU** via l'interface Render :
1. Allez dans votre base PostgreSQL → **"Connect"** → **"SQL Editor"**
2. Copiez-collez le contenu de `scripts/migration_postgresql_render_complete.sql`
3. Exécutez le script

---

## 🌐 Étape 3 : Créer le Service Web

### 3.1 Créer le Service

1. Dans Render Dashboard, cliquez sur **"New +"** → **"Web Service"**
2. Connectez votre repository Git
3. Configurez :
   - **Name** : `import-profit-pro`
   - **Environment** : `Python 3`
   - **Build Command** : 
     ```bash
     pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
     ```
   - **Start Command** :
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - wsgi:app
     ```

### 3.2 Configurer les Variables d'Environnement

Dans **"Environment"** de votre service, ajoutez :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `FLASK_ENV` | `production` | Environnement Flask |
| `FLASK_DEBUG` | `0` | Désactiver le mode debug |
| `SECRET_KEY` | *(généré automatiquement)* | Clé secrète Flask |
| `DATABASE_URL` | *(automatique si lié)* | URL de connexion PostgreSQL |
| `CACHE_TYPE` | `simple` | Type de cache |
| `URL_SCHEME` | `https` | Schéma d'URL |

**Important** : Si vous utilisez `render.yaml`, `DATABASE_URL` sera automatiquement configuré si vous liez la base de données.

### 3.3 Lier la Base de Données

1. Dans votre service web, allez dans **"Environment"**
2. Cliquez sur **"Link Database"**
3. Sélectionnez votre base PostgreSQL `import-profit-db`
4. Render configurera automatiquement `DATABASE_URL`

---

## 🔐 Étape 4 : Configuration de la Sécurité

### 4.1 Générer SECRET_KEY

Si `SECRET_KEY` n'est pas généré automatiquement :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Ajoutez la valeur dans les variables d'environnement Render.

### 4.2 Vérifier la Configuration

Dans les logs du service, vous devriez voir :
```
✅ Configuration PostgreSQL: dpg-xxxxx.virginia-postgres.render.com/madargn
✅ Connexion à la base de données réussie
✅ Tables créées avec succès
```

---

## 📊 Étape 5 : Vérification Post-Déploiement

### 5.1 Accéder à l'Application

1. Votre application sera disponible sur : `https://import-profit-pro.onrender.com`
2. (ou l'URL personnalisée que vous avez configurée)

### 5.2 Créer l'Utilisateur Admin

1. Accédez à : `https://votre-app.onrender.com/init-db`
2. Cela créera l'utilisateur admin :
   - **Username** : `admin`
   - **Password** : `admin123`
3. ⚠️ **Changez le mot de passe immédiatement après la première connexion !**

### 5.3 Vérifier les Tables

Connectez-vous à votre base PostgreSQL et vérifiez :

```sql
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';
```

Vous devriez voir toutes les tables créées.

---

## 🔄 Étape 6 : Mises à Jour Futures

### 6.1 Déploiement Automatique

Render déploie automatiquement à chaque push sur la branche `main`.

### 6.2 Migrations de Base de Données

Pour ajouter de nouvelles tables ou colonnes :

1. Créez un script SQL dans `scripts/`
2. Exécutez-le via l'éditeur SQL de Render
3. Ou créez une route temporaire dans l'app pour exécuter les migrations

---

## 🐛 Dépannage

### Problème : Erreur de connexion à la base de données

**Solution** :
1. Vérifiez que `DATABASE_URL` est bien configurée
2. Vérifiez que la base de données est liée au service
3. Vérifiez les logs pour voir l'URL utilisée

### Problème : Tables manquantes

**Solution** :
1. Exécutez `scripts/migration_postgresql_render_complete.sql`
2. Vérifiez les logs pour les erreurs SQL

### Problème : Application ne démarre pas

**Solution** :
1. Vérifiez les logs dans Render Dashboard
2. Vérifiez que `wsgi.py` existe et est correct
3. Vérifiez que toutes les dépendances sont dans `requirements.txt`

### Problème : Timeout lors du build

**Solution** :
1. Augmentez le timeout dans `render.yaml`
2. Vérifiez que `requirements.txt` ne contient pas de dépendances inutiles

---

## 📝 Checklist de Déploiement

- [ ] Repository Git configuré et à jour
- [ ] Base PostgreSQL créée sur Render
- [ ] Script SQL exécuté avec succès
- [ ] Service web créé et configuré
- [ ] Variables d'environnement configurées
- [ ] Base de données liée au service
- [ ] Application accessible via l'URL Render
- [ ] Utilisateur admin créé
- [ ] Mot de passe admin changé
- [ ] Tests de fonctionnalités effectués

---

## 🔗 Ressources

- [Documentation Render](https://render.com/docs)
- [Guide PostgreSQL Render](https://render.com/docs/databases)
- [Guide Python Render](https://render.com/docs/python)

---

## ✅ Support

En cas de problème, vérifiez :
1. Les logs du service dans Render Dashboard
2. Les logs de la base de données
3. La configuration des variables d'environnement
4. La connexion entre le service et la base de données

---

**Date de mise à jour** : 4 Janvier 2026
