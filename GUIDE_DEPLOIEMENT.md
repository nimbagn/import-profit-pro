# Guide de Déploiement - Import Profit Pro

Ce guide vous explique comment mettre votre application Flask en ligne sur différentes plateformes.

## 📋 Prérequis

- Un compte sur la plateforme de déploiement choisie
- Une base de données MySQL accessible (locale ou cloud)
- Git installé sur votre machine
- Python 3.9+ installé localement

---

## 🚀 Option 1 : Déploiement sur Render (Recommandé - Gratuit)

Render est une plateforme moderne et gratuite pour les applications Flask.

### Étapes :

1. **Créer un compte sur Render** : https://render.com

2. **Créer une base de données MySQL** :
   - Dans le dashboard Render, cliquez sur "New +" → "PostgreSQL" (ou MySQL si disponible)
   - Notez les informations de connexion

3. **Créer un nouveau Web Service** :
   - Cliquez sur "New +" → "Web Service"
   - Connectez votre repository GitHub/GitLab
   - Configurez :
     - **Build Command** : `pip install -r requirements.txt`
     - **Start Command** : `gunicorn wsgi:app`
     - **Environment** : Python 3

4. **Configurer les variables d'environnement** dans Render :
   ```
   FLASK_ENV=production
   SECRET_KEY=votre_secret_key_tres_securise
   DB_HOST=votre_host_mysql
   DB_PORT=3306
   DB_NAME=votre_nom_db
   DB_USER=votre_user
   DB_PASSWORD=votre_password
   REDIS_URL=redis://... (optionnel)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=1
   MAIL_USERNAME=votre_email
   MAIL_PASSWORD=votre_mot_de_passe_app
   ```

5. **Déployer** : Render déploiera automatiquement à chaque push sur votre branche principale.

---

## 🚀 Option 2 : Déploiement sur Railway

Railway offre un déploiement simple avec support MySQL intégré.

### Étapes :

1. **Créer un compte** : https://railway.app

2. **Installer Railway CLI** :
   ```bash
   npm i -g @railway/cli
   railway login
   ```

3. **Initialiser le projet** :
   ```bash
   railway init
   ```

4. **Ajouter MySQL** :
   - Dans le dashboard Railway, ajoutez un service MySQL
   - Railway générera automatiquement `DATABASE_URL`

5. **Configurer les variables d'environnement** :
   ```bash
   railway variables set SECRET_KEY=votre_secret_key
   railway variables set FLASK_ENV=production
   # Les autres variables selon vos besoins
   ```

6. **Déployer** :
   ```bash
   railway up
   ```

---

## 🚀 Option 3 : Déploiement sur Heroku

Heroku est une plateforme classique pour le déploiement d'applications.

### Étapes :

1. **Installer Heroku CLI** : https://devcenter.heroku.com/articles/heroku-cli

2. **Se connecter** :
   ```bash
   heroku login
   ```

3. **Créer l'application** :
   ```bash
   heroku create nom-de-votre-app
   ```

4. **Ajouter une base de données MySQL** :
   - Utilisez un addon comme ClearDB ou JawsDB :
   ```bash
   heroku addons:create cleardb:ignite
   ```
   - Récupérez l'URL de connexion :
   ```bash
   heroku config:get CLEARDB_DATABASE_URL
   ```

5. **Configurer les variables d'environnement** :
   ```bash
   heroku config:set SECRET_KEY=votre_secret_key
   heroku config:set FLASK_ENV=production
   heroku config:set DATABASE_URL=mysql://user:pass@host/db
   ```

6. **Déployer** :
   ```bash
   git push heroku main
   ```

---

## 🚀 Option 4 : Déploiement sur un VPS (DigitalOcean, AWS, etc.)

Pour un contrôle total, vous pouvez déployer sur votre propre serveur.

### Étapes :

1. **Préparer le serveur** :
   ```bash
   # Mettre à jour le système
   sudo apt update && sudo apt upgrade -y
   
   # Installer Python et pip
   sudo apt install python3 python3-pip python3-venv nginx mysql-server -y
   ```

2. **Cloner le projet** :
   ```bash
   git clone votre-repo-url
   cd mini_flask_import_profitability
   ```

3. **Créer un environnement virtuel** :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

4. **Configurer MySQL** :
   ```bash
   sudo mysql_secure_installation
   sudo mysql -u root -p
   ```
   ```sql
   CREATE DATABASE madargn;
   CREATE USER 'votre_user'@'localhost' IDENTIFIED BY 'votre_password';
   GRANT ALL PRIVILEGES ON madargn.* TO 'votre_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

5. **Créer un fichier .env** :
   ```bash
   nano .env
   ```
   Ajoutez toutes les variables d'environnement nécessaires.

6. **Créer un service systemd** :
   ```bash
   sudo nano /etc/systemd/system/flask-app.service
   ```
   ```ini
   [Unit]
   Description=Flask Import Profit Pro
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/chemin/vers/votre/projet
   Environment="PATH=/chemin/vers/votre/projet/venv/bin"
   ExecStart=/chemin/vers/votre/projet/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app

   [Install]
   WantedBy=multi-user.target
   ```

7. **Démarrer le service** :
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start flask-app
   sudo systemctl enable flask-app
   ```

8. **Configurer Nginx** :
   ```bash
   sudo nano /etc/nginx/sites-available/flask-app
   ```
   ```nginx
   server {
       listen 80;
       server_name votre-domaine.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   ```bash
   sudo ln -s /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

9. **Configurer SSL avec Let's Encrypt** :
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d votre-domaine.com
   ```

---

## 📝 Fichiers Nécessaires pour le Déploiement

### 1. Procfile (pour Heroku/Railway)
```
web: gunicorn wsgi:app
```

### 2. wsgi.py (point d'entrée pour gunicorn)
```python
from app import app

if __name__ == "__main__":
    app.run()
```

### 3. runtime.txt (optionnel, pour spécifier la version Python)
```
python-3.11.0
```

### 4. .env.example (template pour les variables d'environnement)
Voir le fichier `.env.example` créé dans le projet.

---

## 🔒 Sécurité en Production

### Variables d'environnement critiques :

1. **SECRET_KEY** : Générer une clé sécurisée :
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **DB_PASSWORD** : Utiliser un mot de passe fort

3. **FLASK_ENV** : Toujours mettre à `production`

4. **DEBUG** : Toujours mettre à `False` en production

### Checklist de sécurité :

- [ ] SECRET_KEY unique et sécurisée
- [ ] DEBUG = False
- [ ] Base de données avec accès restreint
- [ ] HTTPS activé (SSL/TLS)
- [ ] Rate limiting activé
- [ ] Mots de passe forts pour tous les comptes
- [ ] Firewall configuré
- [ ] Backups réguliers de la base de données

---

## 🧪 Tester le Déploiement Localement

Avant de déployer, testez avec gunicorn localement :

```bash
# Installer gunicorn
pip install gunicorn

# Tester
gunicorn --bind 0.0.0.0:5000 wsgi:app

# Avec plusieurs workers (production)
gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app
```

---

## 📊 Monitoring et Logs

### Sur Render/Railway/Heroku :
- Les logs sont disponibles dans le dashboard
- Configurez des alertes pour les erreurs

### Sur VPS :
```bash
# Voir les logs de l'application
sudo journalctl -u flask-app -f

# Voir les logs Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 🔄 Mise à Jour de l'Application

### Sur Render/Railway/Heroku :
- Push automatique : `git push origin main`
- Les plateformes redéploient automatiquement

### Sur VPS :
```bash
cd /chemin/vers/projet
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart flask-app
```

---

## 🆘 Dépannage

### Problème : L'application ne démarre pas
- Vérifiez les logs : `heroku logs --tail` ou dans le dashboard
- Vérifiez que toutes les variables d'environnement sont définies
- Vérifiez la connexion à la base de données

### Problème : Erreur de connexion MySQL
- Vérifiez que la base de données est accessible depuis l'hébergeur
- Vérifiez les credentials dans les variables d'environnement
- Vérifiez les règles de firewall

### Problème : Erreur 500
- Activez temporairement DEBUG=True pour voir les erreurs
- Vérifiez les logs détaillés
- Vérifiez que tous les fichiers sont bien déployés

---

## 📞 Support

Pour toute question ou problème, consultez :
- La documentation de votre plateforme de déploiement
- Les logs de l'application
- Les issues GitHub du projet

---

**Bon déploiement ! 🚀**

