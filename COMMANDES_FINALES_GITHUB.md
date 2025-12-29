# 🚀 Commandes Finales pour Connecter à GitHub

Votre repository GitHub : **https://github.com/nimbagn/import-profit-pro.git**

Repository : `nimbagn/import-profit-pro`

## 📋 Commandes à Exécuter

Copiez-collez ces commandes **une par une** dans votre terminal :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability

# Supprimer l'ancien remote incorrect
git remote remove origin

# Ajouter le bon remote avec votre vraie URL
git remote add origin https://github.com/nimbagn/import-profit-pro.git

# Vérifier que c'est correct
git remote -v

# Pousser votre code vers GitHub
git push -u origin main
```

## 🔐 Authentification

Si GitHub demande une authentification, vous avez deux options :

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

Après le push, allez sur : https://github.com/nimbagn/import-profit-pro

Vous devriez voir tous vos fichiers !

---

## 🎉 Prochaines Étapes

Une fois le code sur GitHub, vous pourrez :
1. Aller sur **Render.com**
2. Créer un nouveau **Web Service**
3. Connecter votre repository : `nimbagn/import-profit-pro`
4. Déployer ! 🚀

**Note :** Le nom du repository est `import-profit-pro` (sans le .git dans le nom)

Consultez **`DEPLOIEMENT_RENDER_RAPIDE.md`** pour la suite !

