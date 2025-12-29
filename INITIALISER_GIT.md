# 🔧 Initialiser Git pour le Déploiement

Votre projet n'est pas encore un dépôt Git. Suivez ces étapes pour l'initialiser et le connecter à GitHub pour Render.

## 📋 Étapes

### 1. Initialiser Git

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
git init
```

### 2. Ajouter tous les fichiers

```bash
git add .
```

### 3. Faire le premier commit

```bash
git commit -m "Initial commit - Application Flask Import Profit Pro"
```

### 4. Créer un repository sur GitHub

1. Allez sur https://github.com
2. Cliquez sur **"New repository"** (ou le bouton **+** en haut à droite)
3. Nommez votre repository : `mini-flask-import-profitability` (ou autre nom)
4. **Ne cochez PAS** "Initialize with README" (vous avez déjà des fichiers)
5. Cliquez sur **"Create repository"**

### 5. Connecter votre projet local à GitHub

GitHub vous donnera des commandes. Utilisez celles-ci :

```bash
# Remplacer YOUR_USERNAME et YOUR_REPO_NAME par vos valeurs
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

**Exemple :**
```bash
git remote add origin https://github.com/dantawi/mini-flask-import-profitability.git
git branch -M main
git push -u origin main
```

### 6. Vérifier

```bash
git status
git remote -v
```

---

## ✅ Vérification

Une fois fait, vous devriez voir votre code sur GitHub. Ensuite, vous pourrez :

1. Aller sur Render.com
2. Créer un nouveau Web Service
3. Connecter votre repository GitHub
4. Déployer !

---

## 🆘 Problèmes Courants

### "fatal: not a git repository"
→ Vous n'êtes pas dans le bon répertoire. Utilisez `cd` pour aller dans le projet.

### "Permission denied"
→ Vérifiez que vous avez les droits d'écriture dans le répertoire.

### "remote origin already exists"
→ Le repository est déjà connecté. Vous pouvez utiliser :
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

---

## 📝 Fichiers qui seront ignorés (grâce à .gitignore)

- `.env` (variables d'environnement sensibles)
- `__pycache__/`
- `*.log`
- `instance/` (base de données locale)
- `.venv/` (environnement virtuel)

Ces fichiers ne seront **pas** commités, ce qui est correct pour la sécurité.

---

**Une fois Git initialisé et connecté à GitHub, vous pourrez suivre `DEPLOIEMENT_RENDER_RAPIDE.md` !**

