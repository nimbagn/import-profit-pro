# 🚀 Démarrage du Serveur Flask

**Date**: 21 Décembre 2025

---

## ✅ SERVEUR REDÉMARRÉ

Le serveur Flask a été redémarré avec les actions suivantes :

1. ✅ Arrêt de tous les processus Flask existants
2. ✅ Libération du port 5002
3. ✅ Démarrage du serveur en arrière-plan
4. ✅ PID sauvegardé dans `flask_server.pid`

---

## 📊 STATUT

### Processus
- **PID**: Vérifier dans `flask_server.pid`
- **Port**: 5002
- **Logs**: `flask_output.log`

### Vérification
Pour vérifier que le serveur fonctionne :

```bash
# Vérifier le processus
cat flask_server.pid
ps -p $(cat flask_server.pid)

# Vérifier le port
lsof -ti:5002

# Voir les logs en temps réel
tail -f flask_output.log
```

---

## 🌐 ACCÈS À L'APPLICATION

### URL
**http://localhost:5002**

### Identifiants de test
- **Username**: `admin`
- **Password**: `admin123`

---

## 🧪 TESTS EN LIVE

Le serveur est maintenant **prêt pour les tests** !

### Routes principales à tester :
1. **Liste des mouvements** : http://localhost:5002/stocks/movements
2. **Créer un transfert** : http://localhost:5002/stocks/movements/new?type=transfer
3. **Liste des réceptions** : http://localhost:5002/stocks/receptions
4. **Créer une réception** : http://localhost:5002/stocks/receptions/new
5. **Récapitulatif** : http://localhost:5002/stocks/summary

### Guide complet
Suivez le guide détaillé dans `GUIDE_TEST_LIVE.md` pour tester toutes les fonctionnalités.

---

## 🔍 VÉRIFICATIONS À EFFECTUER

### Test 1 : Créer un transfert
- Vérifier que **2 mouvements** sont créés (OUT et IN)
- Vérifier les références : `TRANS-YYYYMMDD-XXXX-OUT` et `TRANS-YYYYMMDD-XXXX-IN`

### Test 2 : Créer une réception
- Vérifier que la référence utilise **UUID** (pas de blocage)
- Format : `REC-YYYYMMDD-UUID8CHARS`

### Test 3 : Créer une sortie
- Vérifier que le reason contient `[SORTIE_CLIENT]`
- Vérifier que la référence de sortie est incluse

### Test 4 : Créer un retour
- Vérifier que le reason contient `[RETOUR_CLIENT]`
- Vérifier que la référence de retour est incluse

### Test 5 : Récapitulatif
- Vérifier que les calculs sont corrects
- Vérifier le filtrage par région

---

## 🛑 ARRÊTER LE SERVEUR

Pour arrêter le serveur :

```bash
# Méthode 1 : Utiliser le PID
kill $(cat flask_server.pid)

# Méthode 2 : Arrêter tous les processus Flask
pkill -f "python.*app.py"

# Méthode 3 : Libérer le port
lsof -ti:5002 | xargs kill -9
```

---

## 📝 NOTES

- Le serveur utilise le **fallback SQLite** si MySQL n'est pas disponible
- Toutes les fonctionnalités fonctionnent avec SQLite pour les tests
- Les logs sont disponibles dans `flask_output.log`

---

**✅ Le serveur est redémarré et prêt pour les tests en live !**

Ouvrez **http://localhost:5002** dans votre navigateur et commencez les tests.

