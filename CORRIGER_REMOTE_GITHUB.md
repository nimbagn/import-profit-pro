# 🔧 Corriger la Configuration GitHub

Vous avez utilisé l'URL d'exemple. Voici comment la corriger avec votre vraie URL GitHub.

## 🔍 Étape 1 : Trouver votre URL GitHub

1. Allez sur **https://github.com**
2. Créez un nouveau repository (si pas encore fait) :
   - Cliquez sur **"+"** → **"New repository"**
   - Nommez-le : `mini-flask-import-profitability` (ou votre choix)
   - **Ne cochez pas** "Add a README"
   - Cliquez **"Create repository"**
3. **Copiez l'URL HTTPS** qui ressemble à :
   ```
   https://github.com/VOTRE_VRAI_USERNAME/VOTRE_VRAI_REPO.git
   ```

## 🔧 Étape 2 : Corriger le Remote

Exécutez ces commandes dans votre terminal (remplacez par votre vraie URL) :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability

# Supprimer l'ancien remote incorrect
git remote remove origin

# Ajouter le bon remote avec votre vraie URL
git remote add origin https://github.com/VOTRE_VRAI_USERNAME/VOTRE_VRAI_REPO.git

# Vérifier que c'est correct
git remote -v
```

**Exemple concret :**
Si votre username est `dantawi` et votre repo `mini-flask-import-profitability` :
```bash
git remote remove origin
git remote add origin https://github.com/dantawi/mini-flask-import-profitability.git
git remote -v
```

## 📤 Étape 3 : Pousser vers GitHub

```bash
git push -u origin main
```

## 🔐 Si vous avez besoin d'authentification

### Option 1 : Personal Access Token (Recommandé)

1. Allez sur : https://github.com/settings/tokens
2. Cliquez **"Generate new token"** → **"Generate new token (classic)"**
3. Donnez-lui un nom : `Render Deployment`
4. Cochez **"repo"** (accès complet aux repositories)
5. Cliquez **"Generate token"**
6. **COPIEZ LE TOKEN** (vous ne le reverrez plus !)
7. Quand Git demande le mot de passe, utilisez le **token** (pas votre mot de passe GitHub)

### Option 2 : GitHub CLI

```bash
# Installer GitHub CLI (si pas déjà fait)
brew install gh

# Se connecter
gh auth login

# Puis pousser
git push -u origin main
```

## ✅ Vérification

Après le push, allez sur votre repository GitHub. Vous devriez voir tous vos fichiers !

---

## 🆘 Problèmes

### "remote origin already exists"
→ Utilisez d'abord `git remote remove origin`

### "Repository not found"
→ Vérifiez que :
- Le repository existe bien sur GitHub
- L'URL est correcte (username et nom du repo)
- Vous avez les droits d'accès au repository

### "Permission denied"
→ Utilisez un Personal Access Token (voir Option 1 ci-dessus)

---

**Une fois connecté, vous pourrez déployer sur Render ! 🚀**

