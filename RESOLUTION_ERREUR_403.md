# 🔐 Résolution Erreur 403 - Permission Denied

Vous avez une erreur **403 Permission denied** car vous essayez de pousser vers le repository `nimbagn/import-profit-pro` mais vous êtes connecté en tant que `dantawi`.

## 🔍 Solutions

### Option 1 : Utiliser un Personal Access Token (Recommandé)

C'est la solution la plus simple. GitHub ne permet plus d'utiliser votre mot de passe, il faut un token.

#### Étape 1 : Créer un Token

1. Allez sur : **https://github.com/settings/tokens**
2. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
3. Configurez :
   - **Note** : `Render Deployment` (ou autre nom)
   - **Expiration** : Choisissez une durée (90 jours recommandé)
   - **Scopes** : Cochez **"repo"** (accès complet aux repositories)
4. Cliquez sur **"Generate token"** en bas
5. **⚠️ IMPORTANT : COPIEZ LE TOKEN IMMÉDIATEMENT** (vous ne le reverrez plus !)
   - Il ressemble à : `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### Étape 2 : Utiliser le Token

Quand Git demande votre mot de passe, utilisez le **token** (pas votre mot de passe GitHub) :

```bash
git push -u origin main
# Username: nimbagn (ou votre username GitHub)
# Password: <collez le token ici>
```

#### Étape 3 : Stocker le Token (Optionnel)

Pour ne pas avoir à le retaper à chaque fois :

```bash
# macOS Keychain (recommandé)
git config --global credential.helper osxkeychain

# Puis poussez
git push -u origin main
```

---

### Option 2 : Utiliser GitHub CLI

Plus simple et plus sécurisé :

```bash
# Installer GitHub CLI (si pas déjà fait)
brew install gh

# Se connecter avec le bon compte
gh auth login

# Choisir :
# - GitHub.com
# - HTTPS
# - Login with a web browser
# - Autoriser l'accès

# Puis pousser
git push -u origin main
```

---

### Option 3 : Vérifier le Compte GitHub

Assurez-vous que :
- Vous avez accès au repository `nimbagn/import-profit-pro`
- Le repository n'est pas privé ou vous êtes collaborateur
- Vous utilisez le bon compte GitHub

---

### Option 4 : Changer l'URL pour utiliser SSH

Si vous avez configuré une clé SSH sur GitHub :

```bash
# Changer l'URL en SSH
git remote set-url origin git@github.com:nimbagn/import-profit-pro.git

# Pousser
git push -u origin main
```

---

## ✅ Solution Rapide (Recommandée)

1. Créez un **Personal Access Token** : https://github.com/settings/tokens
2. Cochez **"repo"**
3. Copiez le token
4. Exécutez :
   ```bash
   git push -u origin main
   ```
5. Quand demandé :
   - **Username** : `nimbagn` (ou votre username)
   - **Password** : `<collez le token>`

---

## 🆘 Si ça ne fonctionne toujours pas

Vérifiez que :
- Le repository existe bien : https://github.com/nimbagn/import-profit-pro
- Vous avez les droits d'écriture sur ce repository
- Le repository n'est pas en mode "archived"

---

**Une fois le push réussi, vous pourrez déployer sur Render ! 🚀**

