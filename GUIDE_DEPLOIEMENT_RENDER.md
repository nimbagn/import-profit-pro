# 🚀 Guide de Déploiement sur Render.com

Guide complet étape par étape pour déployer votre application Flask sur Render.com.

---

## 📋 Prérequis

- Un compte GitHub/GitLab/Bitbucket avec votre code
- Un compte Render.com (gratuit)
- Une base de données MySQL accessible (Render propose MySQL ou vous pouvez utiliser une base externe)

---

## 🔧 Étape 1 : Préparer le Projet Localement

### 1.1 Vérifier que tout fonctionne

```bash
# Tester que l'application est prête
python3 test_deploiement.py
```

### 1.2 S'assurer que tous les fichiers sont commités

```bash
# Vérifier le statut
git status

# Ajouter tous les fichiers nécessaires
git add .
git commit -m "Préparation au déploiement sur Render"
git push origin main
```

### 1.3 Générer une SECRET_KEY sécurisée

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**⚠️ IMPORTANT :** Copiez cette clé, vous en aurez besoin plus tard !

---

## 🌐 Étape 2 : Créer un Compte sur Render

1. Allez sur https://render.com
2. Cliquez sur **"Get Started for Free"**
3. Créez un compte avec GitHub (recommandé) ou email
4. Vérifiez votre email si nécessaire

---

## 🗄️ Étape 3 : Créer une Base de Données PostgreSQL

**Note importante :** Render propose PostgreSQL gratuitement, pas MySQL. Votre application supporte maintenant les deux !

### Option A : Base de données PostgreSQL sur Render (Recommandé)

1. Dans le dashboard Render, cliquez sur **"New +"**
2. Sélectionnez **"PostgreSQL"**
3. Configurez :
   - **Name** : `import-profit-db` (ou votre nom)
   - **Database** : Laissez par défaut (généralement le même que le nom)
   - **Region** : Choisissez la région la plus proche
   - **Plan** : Free (pour commencer)
4. Cliquez sur **"Create Database"**
5. **⚠️ IMPORTANT :** Notez les informations de connexion qui s'affichent :
   - **Internal Database URL** : `postgresql://user:password@host:port/database`
     - C'est cette URL que vous utiliserez dans `DATABASE_URL`
     - Elle commence par `postgresql://` - c'est normal !
   - **External Hostname** : Pour connexions externes (si nécessaire)
   - **Port** : Généralement 5432 (PostgreSQL)
   - **Database** : Le nom de votre base
   - **User** : Votre utilisateur
   - **Password** : Le mot de passe généré

### Option B : Utiliser une Base de Données MySQL Externe

Si vous préférez utiliser MySQL (externe à Render), vous pouvez :
- Utiliser un service MySQL externe (comme PlanetScale, Aiven, etc.)
- Configurer les variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- L'application utilisera MySQL au lieu de PostgreSQL

---

## 🚀 Étape 4 : Créer le Web Service

1. Dans le dashboard Render, cliquez sur **"New +"**
2. Sélectionnez **"Web Service"**
3. Connectez votre repository :
   - Si vous utilisez GitHub, autorisez Render à accéder à vos repos
   - Sélectionnez votre repository : `mini_flask_import_profitability`
   - Sélectionnez la branche : `main` (ou `master`)

4. Configurez le service :

   **Informations de base :**
   - **Name** : `import-profit-pro` (ou votre nom)
   - **Region** : Choisissez la même région que votre base de données
   - **Branch** : `main`
   - **Root Directory** : Laissez vide (ou `/` si nécessaire)
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn wsgi:app`

   **Plan :**
   - **Free** : Pour commencer (avec limitations)
   - **Starter** : $7/mois (recommandé pour production)

5. Cliquez sur **"Advanced"** pour plus d'options (optionnel)

6. **NE CLIQUEZ PAS ENCORE sur "Create Web Service"** - nous devons d'abord configurer les variables d'environnement !

---

## 🔐 Étape 5 : Configurer les Variables d'Environnement

Avant de créer le service, configurez les variables d'environnement :

### 5.1 Dans la section "Environment Variables", ajoutez :

#### Configuration de base :
```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<collez la clé générée à l'étape 1.3>
```

#### Configuration Base de Données :

**Si vous utilisez PostgreSQL sur Render (recommandé) :**
```
DATABASE_URL=<collez l'Internal Database URL de l'étape 3>
```
L'URL commence par `postgresql://` - l'application la convertira automatiquement.

**OU si vous utilisez MySQL externe :**
```
DB_HOST=<le hostname de votre base MySQL>
DB_PORT=3306
DB_NAME=madargn
DB_USER=<votre utilisateur MySQL>
DB_PASSWORD=<votre mot de passe MySQL>
```

#### Configuration du cache (optionnel) :
```
CACHE_TYPE=simple
CACHE_TIMEOUT=3600
```

#### Configuration Email (si vous utilisez l'envoi d'emails) :
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
MAIL_DEFAULT_SENDER=votre_email@gmail.com
```

#### Autres configurations :
```
MAX_CONTENT_MB=25
URL_SCHEME=https
```

### 5.2 Exemple complet de variables :

```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=abc123xyz789...votre_cle_secrete_ici
DATABASE_URL=postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/madargn
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
CACHE_TYPE=simple
MAX_CONTENT_MB=25
URL_SCHEME=https
```

**Note :** L'URL PostgreSQL commence par `postgresql://` et utilise le port 5432 (pas 3306 comme MySQL).

---

## ✅ Étape 6 : Créer et Déployer

1. Vérifiez que toutes les variables d'environnement sont configurées
2. Cliquez sur **"Create Web Service"**
3. Render va maintenant :
   - Cloner votre repository
   - Installer les dépendances (`pip install -r requirements.txt`)
   - Démarrer l'application avec Gunicorn

4. **Suivez les logs** dans l'onglet "Logs" pour voir le déploiement en temps réel

5. Attendez que le statut passe à **"Live"** (cela peut prendre 2-5 minutes la première fois)

---

## 🌍 Étape 7 : Accéder à Votre Application

Une fois le déploiement terminé :

1. Votre application sera accessible à l'URL : `https://votre-app-name.onrender.com`
2. Cliquez sur l'URL dans le dashboard Render pour ouvrir votre application
3. Testez la connexion et les fonctionnalités

---

## 🔄 Étape 8 : Configuration Post-Déploiement

### 8.1 Vérifier que l'application fonctionne

- Testez la page d'accueil
- Testez la connexion
- Testez les fonctionnalités principales

### 8.2 Configurer un domaine personnalisé (optionnel)

1. Dans les paramètres de votre service, allez dans **"Custom Domains"**
2. Ajoutez votre domaine
3. Suivez les instructions pour configurer le DNS

### 8.3 Activer le SSL automatique

Render active automatiquement HTTPS pour toutes les applications. Pas besoin de configuration supplémentaire !

---

## 🔧 Configuration Avancée

### Auto-Deploy

Par défaut, Render redéploie automatiquement à chaque push sur la branche principale. Vous pouvez :
- Désactiver l'auto-deploy dans les paramètres
- Configurer des branches spécifiques
- Activer les déploiements manuels uniquement

### Health Checks

Render vérifie automatiquement que votre application répond. Si l'application ne répond pas, Render la redémarre automatiquement.

### Logs

- **Logs en temps réel** : Disponibles dans l'onglet "Logs" du dashboard
- **Logs historiques** : Conservés pendant 30 jours (plan gratuit)

### Variables d'environnement sensibles

Pour les valeurs sensibles (mots de passe, clés API), utilisez les **"Secret Files"** de Render au lieu des variables d'environnement.

---

## 🆘 Dépannage

### Problème : Le build échoue

**Solution :**
- Vérifiez les logs de build dans Render
- Assurez-vous que `requirements.txt` contient toutes les dépendances
- Vérifiez que la version Python est compatible (voir `runtime.txt`)

### Problème : L'application ne démarre pas

**Solution :**
- Vérifiez les logs de démarrage
- Vérifiez que `wsgi.py` existe et est correct
- Vérifiez que la commande de démarrage est : `gunicorn wsgi:app`
- Vérifiez que toutes les variables d'environnement sont définies

### Problème : Erreur de connexion à la base de données

**Solution :**
- Vérifiez que `DATABASE_URL` ou les variables `DB_*` sont correctes
- Si vous utilisez PostgreSQL sur Render, utilisez l'**Internal Database URL** (pas l'externe)
- L'URL doit commencer par `postgresql://` pour PostgreSQL
- Vérifiez que la base de données est bien créée et active
- Vérifiez que le mot de passe ne contient pas de caractères spéciaux non encodés
- Assurez-vous que `psycopg2-binary` est dans `requirements.txt` (déjà ajouté)

### Problème : Erreur 500 Internal Server Error

**Solution :**
- Activez temporairement `FLASK_DEBUG=1` pour voir les erreurs détaillées
- Vérifiez les logs dans Render
- Vérifiez que `SECRET_KEY` est défini
- Vérifiez que tous les fichiers nécessaires sont présents

### Problème : L'application se met en veille (plan gratuit)

**Solution :**
- Le plan gratuit met les applications en veille après 15 minutes d'inactivité
- Le premier démarrage après veille peut prendre 30-60 secondes
- Pour éviter cela, passez à un plan payant ou utilisez un service de "ping" pour maintenir l'application active

---

## 📊 Monitoring

### Métriques disponibles

Render fournit des métriques de base :
- CPU usage
- Memory usage
- Request count
- Response time

### Alertes

Configurez des alertes dans les paramètres pour être notifié en cas de problème.

---

## 🔄 Mise à Jour de l'Application

### Déploiement automatique

1. Faites vos modifications localement
2. Testez localement
3. Committez et pushez :
   ```bash
   git add .
   git commit -m "Description des modifications"
   git push origin main
   ```
4. Render détectera automatiquement le changement et redéploiera

### Déploiement manuel

1. Dans le dashboard Render, allez dans votre service
2. Cliquez sur **"Manual Deploy"**
3. Sélectionnez la branche et le commit
4. Cliquez sur **"Deploy"**

---

## 💰 Plans et Tarification

### Plan Free (Gratuit)
- ✅ Applications web illimitées
- ✅ Base de données MySQL gratuite
- ⚠️ Mise en veille après 15 min d'inactivité
- ⚠️ 512 MB RAM
- ⚠️ Logs conservés 30 jours

### Plan Starter ($7/mois)
- ✅ Pas de mise en veille
- ✅ 512 MB RAM
- ✅ Support prioritaire
- ✅ Logs conservés 90 jours

### Plan Standard ($25/mois)
- ✅ 2 GB RAM
- ✅ Scaling automatique
- ✅ Logs conservés 1 an

---

## ✅ Checklist Finale

Avant de considérer le déploiement terminé :

- [ ] Application accessible via l'URL Render
- [ ] Connexion à la base de données fonctionnelle
- [ ] Authentification fonctionnelle
- [ ] Toutes les fonctionnalités principales testées
- [ ] Variables d'environnement sécurisées
- [ ] DEBUG désactivé en production
- [ ] SECRET_KEY unique et sécurisée
- [ ] Logs vérifiés (pas d'erreurs critiques)
- [ ] Domaine personnalisé configuré (si nécessaire)

---

## 📞 Support

- **Documentation Render** : https://render.com/docs
- **Support Render** : support@render.com
- **Status Page** : https://status.render.com

---

**🎉 Félicitations ! Votre application est maintenant en ligne sur Render !**

