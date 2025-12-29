# 🔐 Solution Définitive - Erreur 403

Le problème : Vous êtes connecté en tant que `dantawi` mais le repository appartient à `nimbagn`.

## 🎯 Solutions

### Solution 1 : Utiliser le Token dans l'URL (Recommandé)

Incluez directement le token dans l'URL pour forcer l'authentification :

```bash
# 1. Créez un Personal Access Token pour le compte nimbagn
#    Allez sur : https://github.com/settings/tokens
#    (Connectez-vous avec le compte nimbagn)
#    Créez un token avec les permissions "repo"

# 2. Remplacez l'URL du remote avec le token
git remote set-url origin https://VOTRE_TOKEN@github.com/nimbagn/import-profit-pro.git

# 3. Poussez (sans demander de mot de passe)
git push -u origin main
```

**Exemple :**
```bash
git remote set-url origin https://ghp_xxxxxxxxxxxxxxxxxxxx@github.com/nimbagn/import-profit-pro.git
git push -u origin main
```

⚠️ **Note de sécurité :** Le token sera visible dans `.git/config`. Utilisez cette méthode uniquement si vous êtes le seul utilisateur de la machine.

---

### Solution 2 : Utiliser SSH (Plus Sécurisé)

Si vous avez configuré une clé SSH pour le compte `nimbagn` :

```bash
# Changer l'URL en SSH
git remote set-url origin git@github.com:nimbagn/import-profit-pro.git

# Pousser
git push -u origin main
```

**Pour configurer SSH :**
1. Générez une clé SSH : `ssh-keygen -t ed25519 -C "votre_email@example.com"`
2. Ajoutez la clé à GitHub : https://github.com/settings/keys
3. Utilisez l'URL SSH ci-dessus

---

### Solution 3 : Se Connecter avec le Bon Compte

Si `dantawi` et `nimbagn` sont deux comptes différents :

#### Option A : Utiliser GitHub CLI

```bash
# Se déconnecter
gh auth logout

# Se reconnecter avec le compte nimbagn
gh auth login

# Puis pousser
git push -u origin main
```

#### Option B : Nettoyer les Credentials macOS

```bash
# Supprimer les credentials stockés
git credential-osxkeychain erase
host=github.com
protocol=https
# Appuyez sur Entrée deux fois

# Puis poussez (vous devrez vous authentifier)
git push -u origin main
```

---

### Solution 4 : Ajouter dantawi comme Collaborateur

Si vous avez accès au compte `nimbagn` :

1. Allez sur : https://github.com/nimbagn/import-profit-pro/settings/access
2. Cliquez sur **"Add people"**
3. Ajoutez `dantawi` comme collaborateur
4. Acceptez l'invitation avec le compte `dantawi`
5. Puis poussez normalement

---

## ✅ Solution Rapide (Recommandée)

**La plus simple :** Utiliser le token dans l'URL

```bash
# 1. Créez un token pour nimbagn : https://github.com/settings/tokens
# 2. Remplacez VOTRE_TOKEN par le token réel
git remote set-url origin https://VOTRE_TOKEN@github.com/nimbagn/import-profit-pro.git

# 3. Poussez
git push -u origin main
```

**Exemple concret :**
Si votre token est `ghp_abc123xyz789`, la commande serait :
```bash
git remote set-url origin https://ghp_abc123xyz789@github.com/nimbagn/import-profit-pro.git
git push -u origin main
```

---

## 🔍 Vérifier la Configuration

```bash
# Voir l'URL actuelle
git remote -v

# Voir les credentials stockés (macOS)
git config --global credential.helper
```

---

## 🆘 Si Rien ne Fonctionne

1. **Vérifiez que le repository existe** : https://github.com/nimbagn/import-profit-pro
2. **Vérifiez que vous avez les droits** sur ce repository
3. **Essayez de créer le repository sous votre compte** `dantawi` si vous n'avez pas accès à `nimbagn`

---

**Une fois le push réussi, vous pourrez déployer sur Render ! 🚀**

