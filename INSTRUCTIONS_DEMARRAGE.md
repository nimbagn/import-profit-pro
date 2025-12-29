# 🚀 Instructions de Démarrage du Serveur

**Date**: 21 Décembre 2025

---

## ⚠️ PROBLÈMES DÉTECTÉS

### 1. Processus existants sur le port 5002
Il y a encore des processus Python qui utilisent le port 5002 (PIDs: 34371, 35822)

### 2. Permission de lecture du fichier .env
Le serveur rencontre une erreur de permission pour lire le fichier `.env`

---

## ✅ SOLUTION RECOMMANDÉE

### Étape 1 : Arrêter tous les processus Flask

**Dans un terminal**, exécutez :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability

# Arrêter tous les processus Python Flask
pkill -f "python.*app.py"

# Arrêter les processus sur le port 5002
lsof -ti:5002 | xargs kill -9

# Vérifier que le port est libre
lsof -ti:5002 || echo "✅ Port libre"
```

### Étape 2 : Vérifier les permissions du fichier .env

```bash
# Vérifier si le fichier .env existe
ls -la .env

# Si nécessaire, ajuster les permissions
chmod 644 .env
```

### Étape 3 : Démarrer le serveur proprement

**Option A : Utiliser le script de démarrage**
```bash
./start_server.sh
```

**Option B : Démarrage manuel**
```bash
python3 app.py
```

---

## 🔍 VÉRIFICATION

Une fois le serveur démarré, vous devriez voir :

```
🚀 IMPORT PROFIT PRO - VERSION NETTOYÉE ET MODERNE
============================================================
✅ Projet nettoyé et optimisé
✅ Base de données connectée
✅ Interface ultra-moderne
✅ API REST intégrée
============================================================
🌐 Serveur démarré sur http://localhost:5002
```

---

## 🧪 TESTS EN LIVE

Une fois le serveur démarré :

1. **Ouvrir le navigateur** : http://localhost:5002
2. **Se connecter** : 
   - Username: `admin`
   - Password: `admin123`
3. **Tester les fonctionnalités** selon `GUIDE_TEST_LIVE.md`

---

## 📋 ROUTES À TESTER

- http://localhost:5002/stocks/movements
- http://localhost:5002/stocks/receptions
- http://localhost:5002/stocks/outgoings
- http://localhost:5002/stocks/returns
- http://localhost:5002/stocks/summary

---

## 💡 NOTES

- Le serveur utilise le **fallback SQLite** si MySQL n'est pas disponible
- Toutes les fonctionnalités fonctionnent avec SQLite pour les tests
- Les logs sont affichés dans la console

---

**✅ Suivez ces instructions pour démarrer le serveur proprement !**

