# 🔗 Connecter votre Projet à GitHub

Votre code est déjà commité localement. Maintenant, connectons-le à GitHub pour pouvoir déployer sur Render.

## 📋 Étapes

### 1️⃣ Créer un Repository sur GitHub

1. Allez sur **https://github.com**
2. Cliquez sur le bouton **"+"** en haut à droite
3. Sélectionnez **"New repository"**
4. Configurez :
   - **Repository name** : `mini-flask-import-profitability` (ou votre nom)
   - **Description** : "Application Flask Import Profit Pro"
   - **Visibility** : Public ou Private (selon votre choix)
   - **⚠️ NE COCHEZ PAS** "Add a README file" (vous avez déjà des fichiers)
   - **⚠️ NE COCHEZ PAS** "Add .gitignore" (vous en avez déjà un)
   - **⚠️ NE COCHEZ PAS** "Choose a license"
5. Cliquez sur **"Create repository"**

### 2️⃣ Copier l'URL du Repository

GitHub vous affichera une page avec des instructions. **Copiez l'URL HTTPS** qui ressemble à :
```
https://github.com/VOTRE_USERNAME/mini-flask-import-profitability.git
```

### 3️⃣ Connecter votre Projet Local à GitHub

Exécutez ces commandes dans votre terminal (remplacez `VOTRE_USERNAME` et `VOTRE_REPO` par vos valeurs) :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability

# Ajouter le remote GitHub
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git

# Vérifier que c'est bien configuré
git remote -v

# Pousser votre code vers GitHub
git push -u origin main
```

**Exemple concret :**
```bash
git remote add origin https://github.com/dantawi/mini-flask-import-profitability.git
git remote -v
git push -u origin main
```

### 4️⃣ Vérifier

Allez sur votre repository GitHub. Vous devriez voir tous vos fichiers !

---

## 🆘 Problèmes Courants

### "remote origin already exists"
Si vous avez déjà un remote, supprimez-le d'abord :
```bash
git remote remove origin
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
```

### "Permission denied" ou "Authentication failed"
Vous devrez vous authentifier. Options :
1. **Utiliser GitHub CLI** : `gh auth login`
2. **Utiliser un Personal Access Token** : https://github.com/settings/tokens
3. **Utiliser SSH** : Configurez une clé SSH sur GitHub

### "fatal: not a git repository"
Assurez-vous d'être dans le bon répertoire :
```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
```

---

## ✅ Une fois Connecté

Une fois votre code sur GitHub, vous pourrez :
1. Aller sur **Render.com**
2. Créer un nouveau **Web Service**
3. Connecter votre repository GitHub
4. Déployer ! 🚀

---

**Besoin d'aide ?** Consultez `DEPLOIEMENT_RENDER_RAPIDE.md` une fois GitHub connecté !

