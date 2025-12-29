# 🚀 Commandes Git pour le Déploiement

Copiez-collez ces commandes dans votre terminal, une par une.

## 🔧 Initialisation (à faire une seule fois)

```bash
# 1. Aller dans le répertoire du projet
cd /Users/dantawi/Documents/mini_flask_import_profitability

# 2. Initialiser Git
git init

# 3. Ajouter tous les fichiers
git add .

# 4. Faire le premier commit
git commit -m "Initial commit - Application Flask Import Profit Pro prête pour Render"
```

## 📤 Connecter à GitHub

**Remplacez `VOTRE_USERNAME` et `VOTRE_REPO` par vos valeurs réelles !**

```bash
# 5. Ajouter le remote GitHub (remplacez par votre URL)
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git

# 6. Renommer la branche en 'main'
git branch -M main

# 7. Pousser vers GitHub
git push -u origin main
```

## 🔄 Mises à jour futures

Après avoir fait des modifications :

```bash
# Ajouter les modifications
git add .

# Commiter
git commit -m "Description de vos modifications"

# Pousser vers GitHub
git push
```

---

## 📋 Exemple Complet

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
git init
git add .
git commit -m "Initial commit - Application Flask Import Profit Pro"
git remote add origin https://github.com/dantawi/mini-flask-import-profitability.git
git branch -M main
git push -u origin main
```

---

## ✅ Vérification

```bash
# Vérifier le statut
git status

# Vérifier les remotes
git remote -v

# Voir l'historique
git log --oneline
```

---

**Une fois poussé sur GitHub, allez sur Render.com et connectez votre repository !**

