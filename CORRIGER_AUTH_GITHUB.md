# 🔐 Corriger l'Authentification GitHub

## ❌ Erreur

```
remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed
```

## 🔍 Cause

Le token dans l'URL du remote a expiré ou été révoqué.

## ✅ Solutions

### Solution 1 : Utiliser un Nouveau Token (Recommandé)

#### Étape 1 : Créer un Nouveau Token

1. Allez sur : https://github.com/settings/tokens
2. Cliquez **"Generate new token"** → **"Generate new token (classic)"**
3. Configurez :
   - **Note** : `Render Deployment`
   - **Expiration** : 90 jours (ou plus)
   - **Scopes** : Cochez **"repo"**
4. Cliquez **"Generate token"**
5. **COPIEZ LE TOKEN** (vous ne le reverrez plus !)

#### Étape 2 : Mettre à Jour le Remote

```bash
# Remplacez VOTRE_NOUVEAU_TOKEN par le token copié
git remote set-url origin https://VOTRE_NOUVEAU_TOKEN@github.com/nimbagn/import-profit-pro.git

# Vérifier
git remote -v

# Pousser
git push origin main
```

**Exemple :**
```bash
git remote set-url origin https://ghp_abc123xyz789@github.com/nimbagn/import-profit-pro.git
git push origin main
```

---

### Solution 2 : Utiliser SSH (Plus Sécurisé)

Si vous avez une clé SSH configurée :

```bash
# Changer l'URL en SSH
git remote set-url origin git@github.com:nimbagn/import-profit-pro.git

# Pousser
git push origin main
```

**Pour configurer SSH :**
1. Générez une clé : `ssh-keygen -t ed25519 -C "votre_email@example.com"`
2. Ajoutez la clé à GitHub : https://github.com/settings/keys
3. Utilisez l'URL SSH ci-dessus

---

### Solution 3 : Utiliser GitHub CLI

```bash
# Installer GitHub CLI (si pas déjà fait)
brew install gh

# Se connecter
gh auth login

# Pousser
git push origin main
```

---

## 🎯 Solution Rapide Recommandée

1. **Créer un nouveau token** : https://github.com/settings/tokens
2. **Mettre à jour le remote** :
   ```bash
   git remote set-url origin https://VOTRE_NOUVEAU_TOKEN@github.com/nimbagn/import-profit-pro.git
   ```
3. **Pousser** :
   ```bash
   git push origin main
   ```

---

## ⚠️ Note de Sécurité

- Ne commitez JAMAIS le token dans le code
- Révoquez les anciens tokens non utilisés
- Utilisez SSH pour plus de sécurité à long terme

---

**Créez un nouveau token et mettez à jour le remote !**

