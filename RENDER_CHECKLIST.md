# ✅ Checklist de Déploiement sur Render

## 📋 Avant de Commencer

- [ ] Code testé localement et fonctionnel
- [ ] Tous les fichiers commités et pushés sur GitHub
- [ ] Compte Render créé (https://render.com)

---

## 🔧 Préparation Locale

- [ ] Exécuté `python3 test_deploiement.py` - tous les tests passent
- [ ] Généré une SECRET_KEY avec `python3 generate_secret_key.py`
- [ ] SECRET_KEY copiée (vous en aurez besoin)
- [ ] Fichiers vérifiés :
  - [ ] `wsgi.py` existe
  - [ ] `Procfile` existe
  - [ ] `requirements.txt` contient `gunicorn`
  - [ ] `runtime.txt` existe (optionnel)

---

## 🗄️ Base de Données MySQL

- [ ] Base de données MySQL créée sur Render
- [ ] Informations de connexion notées :
  - [ ] Internal Database URL (ou DB_HOST, DB_PORT, etc.)
  - [ ] Database name
  - [ ] Username
  - [ ] Password

---

## 🚀 Création du Web Service

- [ ] Nouveau Web Service créé sur Render
- [ ] Repository GitHub connecté
- [ ] Configuration :
  - [ ] Name : `import-profit-pro` (ou votre choix)
  - [ ] Region : Même région que la base de données
  - [ ] Branch : `main`
  - [ ] Build Command : `pip install -r requirements.txt`
  - [ ] Start Command : `gunicorn wsgi:app`

---

## 🔐 Variables d'Environnement

Toutes ces variables doivent être configurées dans Render :

### Obligatoires
- [ ] `FLASK_ENV=production`
- [ ] `FLASK_DEBUG=0`
- [ ] `SECRET_KEY=<votre_clé_générée>`

### Base de Données (choisir une option)
- [ ] Option A : `DATABASE_URL=<internal_database_url>`
- [ ] Option B : Variables séparées :
  - [ ] `DB_HOST=<hostname>`
  - [ ] `DB_PORT=3306`
  - [ ] `DB_NAME=madargn`
  - [ ] `DB_USER=<username>`
  - [ ] `DB_PASSWORD=<password>`

### Optionnelles (selon vos besoins)
- [ ] `CACHE_TYPE=simple`
- [ ] `CACHE_TIMEOUT=3600`
- [ ] `MAX_CONTENT_MB=25`
- [ ] `URL_SCHEME=https`
- [ ] Variables email (si vous utilisez Flask-Mail)

---

## ✅ Déploiement

- [ ] Service créé et déploiement lancé
- [ ] Logs surveillés - pas d'erreurs critiques
- [ ] Statut : **Live** ✅
- [ ] URL de l'application notée : `https://votre-app.onrender.com`

---

## 🧪 Tests Post-Déploiement

- [ ] Application accessible via l'URL Render
- [ ] Page d'accueil charge correctement
- [ ] Connexion à la base de données fonctionne
- [ ] Authentification fonctionnelle (login)
- [ ] Fonctionnalités principales testées :
  - [ ] Navigation
  - [ ] Création/édition d'éléments
  - [ ] Affichage des données
  - [ ] Export (si applicable)

---

## 🔒 Sécurité

- [ ] `DEBUG=False` en production
- [ ] `SECRET_KEY` unique et sécurisée
- [ ] Mots de passe de base de données forts
- [ ] Variables sensibles non commitées dans Git
- [ ] HTTPS activé (automatique sur Render)

---

## 📊 Monitoring

- [ ] Logs vérifiés - pas d'erreurs
- [ ] Métriques surveillées (CPU, Memory)
- [ ] Alertes configurées (optionnel)

---

## 🎉 Finalisation

- [ ] Domaine personnalisé configuré (si nécessaire)
- [ ] Documentation mise à jour avec l'URL de production
- [ ] Équipe informée de l'URL de production
- [ ] Backup de la base de données planifié

---

## 📝 Notes Importantes

- ⚠️ Le plan gratuit met l'application en veille après 15 min d'inactivité
- ⚠️ Le premier démarrage après veille peut prendre 30-60 secondes
- ✅ Render active automatiquement HTTPS
- ✅ Auto-deploy activé par défaut (redéploie à chaque push)

---

**🎊 Félicitations ! Votre application est en ligne !**

