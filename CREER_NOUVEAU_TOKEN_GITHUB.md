# 🔐 Créer un Nouveau Token GitHub

## 📍 Où Créer le Token

Le token GitHub n'est **PAS stocké** dans les fichiers du projet (sécurité). Vous devez le créer sur GitHub.

## ✅ Étapes pour Créer un Nouveau Token

### Étape 1 : Aller sur GitHub Settings

1. Allez sur : **https://github.com/settings/tokens**
2. Ou :
   - Cliquez sur votre **avatar** (en haut à droite)
   - Cliquez sur **"Settings"**
   - Dans le menu de gauche, cliquez sur **"Developer settings"**
   - Cliquez sur **"Personal access tokens"** → **"Tokens (classic)"**

### Étape 2 : Générer un Nouveau Token

1. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
2. Configurez le token :
   - **Note** : `Render Deployment` (ou un nom descriptif)
   - **Expiration** : 
     - 90 jours (recommandé)
     - Ou "No expiration" (si vous voulez qu'il ne expire jamais)
   - **Scopes** : Cochez **"repo"** (donne accès complet aux repositories)
3. Cliquez sur **"Generate token"** (en bas de la page)

### Étape 3 : Copier le Token

⚠️ **IMPORTANT** : Le token s'affiche **UNE SEULE FOIS** !

1. **COPIEZ LE TOKEN IMMÉDIATEMENT** (il commence par `ghp_`)
2. Le token ressemble à : `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. **Ne fermez pas la page** avant de l'avoir copié !

## 🔧 Utiliser le Token

### Option 1 : Dans l'URL du Remote (Rapide)

```bash
# Remplacez VOTRE_NOUVEAU_TOKEN par le token que vous venez de copier
git remote set-url origin https://VOTRE_TOKEN@github.com/nimbagn/import-profit-pro.git

# Vérifier
git remote -v

# Pousser
git push origin main
```

**Exemple concret :**
```bash
git remote set-url origin https://ghp_abc123xyz789@github.com/nimbagn/import-profit-pro.git
git push origin main
```

### Option 2 : Via Git Credential Helper (Plus Sécurisé)

```bash
# Configurer le credential helper
git config --global credential.helper osxkeychain

# Lors du push, Git vous demandera le token
git push origin main
# Username: nimbagn
# Password: [collez votre token ici]
```

### Option 3 : Via GitHub CLI (Recommandé)

```bash
# Installer GitHub CLI (si pas déjà fait)
brew install gh

# Se connecter
gh auth login

# Pousser
git push origin main
```

## 📋 Vérifier le Token Actuel

Pour voir quel token est configuré (sans le voir en clair) :

```bash
# Voir l'URL du remote
git remote -v

# Si vous voyez ghp_xxxxx dans l'URL, c'est le token actuel
```

## 🔍 Où Trouver vos Tokens Existants

1. Allez sur : **https://github.com/settings/tokens**
2. Vous verrez la liste de **tous vos tokens**
3. Chaque token a :
   - Un **nom** (Note)
   - Une **date d'expiration**
   - Un bouton pour **révoquer** le token

## ⚠️ Sécurité

- ❌ **NE COMMITEZ JAMAIS** le token dans le code
- ❌ **NE PARTAGEZ PAS** le token publiquement
- ✅ **RÉVOQUEZ** les anciens tokens non utilisés
- ✅ **UTILISEZ SSH** pour plus de sécurité à long terme

## 🆘 Si le Token Expire

Si vous obtenez une erreur "Invalid username or token" :

1. **Vérifiez** si le token a expiré sur : https://github.com/settings/tokens
2. **Créez un nouveau token** (étapes ci-dessus)
3. **Mettez à jour** le remote avec le nouveau token

## 📝 Résumé Rapide

1. **Créer** : https://github.com/settings/tokens → "Generate new token (classic)"
2. **Configurer** : Note + Expiration + Scope "repo"
3. **Copier** : Le token (commence par `ghp_`)
4. **Utiliser** : `git remote set-url origin https://TOKEN@github.com/nimbagn/import-profit-pro.git`
5. **Pousser** : `git push origin main`

---

**Créez votre nouveau token sur GitHub maintenant !**

