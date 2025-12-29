# ⚡ Déploiement Rapide sur Render - 10 Minutes

## 🎯 Étapes Rapides

### 1️⃣ Préparer (2 min)

```bash
# Générer une SECRET_KEY
python3 generate_secret_key.py
# ⚠️ COPIEZ LA CLÉ AFFICHÉE !

# Tester que tout fonctionne
python3 test_deploiement.py

# S'assurer que tout est commité
git add .
git commit -m "Prêt pour Render"
git push
```

### 2️⃣ Créer la Base de Données (2 min)

1. Allez sur https://render.com → Créez un compte
2. **New +** → **PostgreSQL** (Render propose PostgreSQL gratuitement)
3. Configurez :
   - Name : `import-profit-db`
   - Database : `madargn` (ou laissez par défaut)
   - Plan : **Free**
4. Cliquez **Create Database**
5. **⚠️ COPIEZ l'Internal Database URL** (format : `postgresql://user:pass@host:port/db`)
   - Render fournit automatiquement cette URL
   - Elle commence par `postgresql://`

### 3️⃣ Créer le Web Service (3 min)

1. **New +** → **Web Service**
2. Connectez votre repo GitHub
3. Configurez :
   - **Name** : `import-profit-pro`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn wsgi:app`
   - **Plan** : Free (pour commencer)

### 4️⃣ Variables d'Environnement (2 min)

Dans la section **Environment Variables**, ajoutez :

```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<collez la clé de l'étape 1>
DATABASE_URL=<collez l'Internal Database URL de l'étape 2>
```

**Note :** L'URL commence par `postgresql://` - c'est normal ! L'application la convertira automatiquement.

### 5️⃣ Déployer (1 min)

1. Cliquez **Create Web Service**
2. Attendez 2-5 minutes
3. Votre app sera sur : `https://import-profit-pro.onrender.com`

---

## ✅ C'est Tout !

Votre application est maintenant en ligne ! 🎉

---

## 🆘 Problèmes ?

- **Build échoue ?** → Vérifiez les logs dans Render
- **Erreur DB ?** → Vérifiez que DATABASE_URL est correcte
- **500 Error ?** → Activez temporairement `FLASK_DEBUG=1` pour voir l'erreur

---

Pour plus de détails, consultez `GUIDE_DEPLOIEMENT_RENDER.md`

