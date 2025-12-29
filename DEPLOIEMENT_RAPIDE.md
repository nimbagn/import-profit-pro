# 🚀 Déploiement Rapide - Guide Express

## ⚡ Déploiement en 5 minutes (Render - Recommandé)

### 1. Préparer le projet
```bash
# Tester que tout fonctionne
python3 test_deploiement.py

# S'assurer que tous les fichiers sont commités
git add .
git commit -m "Préparation au déploiement"
git push
```

### 2. Sur Render.com

1. **Créer un compte** : https://render.com (gratuit)

2. **Nouveau Web Service** :
   - Connectez votre repo GitHub
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `gunicorn wsgi:app`
   - Environment : Python 3

3. **Variables d'environnement** (dans Render Dashboard) :
   ```
   SECRET_KEY=<générez avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
   DB_HOST=<votre_host_mysql>
   DB_PORT=3306
   DB_NAME=madargn
   DB_USER=<votre_user>
   DB_PASSWORD=<votre_password>
   FLASK_ENV=production
   FLASK_DEBUG=0
   ```

4. **C'est tout !** Render déploiera automatiquement.

---

## 🔧 Test Local avec Gunicorn

Avant de déployer, testez localement :

```bash
# Installer gunicorn
pip install gunicorn

# Tester
gunicorn --bind 0.0.0.0:5000 wsgi:app

# Ouvrir http://localhost:5000
```

---

## 📋 Checklist Avant Déploiement

- [ ] `python3 test_deploiement.py` passe tous les tests
- [ ] SECRET_KEY unique générée
- [ ] Variables d'environnement configurées
- [ ] Base de données accessible depuis l'hébergeur
- [ ] DEBUG = False en production
- [ ] Tous les fichiers commités et pushés

---

## 🆘 Problèmes Courants

**Erreur : Module not found**
→ Vérifiez que `requirements.txt` contient toutes les dépendances

**Erreur : Cannot connect to database**
→ Vérifiez les variables DB_* et que la base est accessible

**Erreur : SECRET_KEY not set**
→ Ajoutez SECRET_KEY dans les variables d'environnement

---

Pour plus de détails, consultez `GUIDE_DEPLOIEMENT.md`

