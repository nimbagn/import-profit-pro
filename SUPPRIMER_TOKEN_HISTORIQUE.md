# 🔒 Supprimer le Token de l'Historique Git

## ⚠️ Problème

GitHub détecte encore le token dans l'historique Git (commit `d387965`), même si on l'a supprimé dans le dernier commit.

## ✅ Solution : Réécrire l'Historique

### Option 1 : Supprimer le Fichier de l'Historique (Recommandé)

Le fichier `COMMANDE_CORRECTE.md` contient le token dans l'historique. Supprimons-le complètement :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability

# Supprimer le fichier de l'historique Git
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch COMMANDE_CORRECTE.md" \
  --prune-empty --tag-name-filter cat -- --all

# OU méthode plus simple avec git-filter-repo (si installé)
# git filter-repo --path COMMANDE_CORRECTE.md --invert-paths
```

### Option 2 : Réécrire le Commit Spécifique

Réécrire le commit `d387965` pour supprimer le token :

```bash
# Faire un rebase interactif
git rebase -i d387965^1

# Dans l'éditeur, changez "pick" en "edit" pour le commit d387965
# Puis :
git commit --amend
# Modifiez COMMANDE_CORRECTE.md pour supprimer le token
git add COMMANDE_CORRECTE.md
git commit --amend --no-edit
git rebase --continue
```

### Option 3 : Supprimer le Fichier et Forcer le Push

Solution la plus simple :

```bash
# Supprimer le fichier
rm COMMANDE_CORRECTE.md

# Supprimer de Git
git rm COMMANDE_CORRECTE.md

# Commiter la suppression
git commit -m "Suppression fichier contenant token - sécurité"

# Forcer le push (ATTENTION : réécrit l'historique)
git push origin main --force
```

⚠️ **Attention :** `--force` réécrit l'historique. Utilisez-le seulement si vous êtes sûr.

### Option 4 : Utiliser l'URL GitHub (Plus Simple)

GitHub vous donne une URL pour autoriser le secret :

1. Allez sur : https://github.com/nimbagn/import-profit-pro/security/secret-scanning/unblock-secret/37XAwMkrdztQLmzXzHR04Q6Hrh0
2. Cliquez sur **"Allow secret"** (si vous êtes sûr que le token est révoqué)
3. Puis poussez à nouveau : `git push origin main`

## 🔐 Important : Révoquer le Token

**AVANT TOUT**, révoquez le token qui était dans le code :

1. Allez sur : https://github.com/settings/tokens
2. Trouvez et révoquez le token exposé

## ✅ Solution Recommandée (Simple)

1. **Révoquer le token** : https://github.com/settings/tokens
2. **Utiliser l'URL GitHub** pour autoriser le push une fois
3. **Pousser** : `git push origin main`

OU

1. **Supprimer le fichier** : `git rm COMMANDE_CORRECTE.md`
2. **Commiter** : `git commit -m "Suppression fichier avec token"`
3. **Pousser** : `git push origin main`

---

**La solution la plus simple est d'utiliser l'URL GitHub pour autoriser le secret une fois, puis de supprimer le fichier pour éviter le problème à l'avenir.**

