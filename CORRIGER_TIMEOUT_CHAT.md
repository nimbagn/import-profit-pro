# 🔧 CORRECTION DES TIMEOUTS CHAT ET OPTIMISATION

**Date :** 31 Décembre 2025  
**Problème :** WORKER TIMEOUT et requêtes lentes dans le chat

---

## ❌ PROBLÈMES IDENTIFIÉS

### 1. WORKER TIMEOUT (CRITIQUE)

**Erreur :**
```
[CRITICAL] WORKER TIMEOUT (pid:74)
Error handling request /chat/api/stream/rooms
```

**Cause :**
- Gunicorn a un timeout par défaut de **30 secondes**
- Les connexions SSE restent ouvertes indéfiniment
- Gunicorn tue le worker après 30 secondes

**Solution :** Augmenter le timeout Gunicorn à 120 secondes

### 2. Requêtes lentes

**Problème :**
- `/chat/api/rooms` : **12-21 secondes** (devrait être < 1 seconde)
- `/chat/api/stream/rooms` : **30+ secondes** avant timeout

**Cause :**
- Requêtes N+1 dans le code SSE
- Pas d'optimisation des requêtes dans la boucle

**Solution :** Optimiser les requêtes avec `joinedload` et sous-requêtes

---

## ✅ CORRECTIONS APPLIQUÉES

### 1. Configuration Gunicorn (`gunicorn.conf.py`)

**Créé :** `gunicorn.conf.py`

```python
# Timeout pour les connexions longues (SSE)
timeout = 120  # 120 secondes au lieu de 30
graceful_timeout = 30
```

**Modifié :** `Procfile`

```
web: gunicorn --config gunicorn.conf.py wsgi:app
```

### 2. Optimisation du code SSE (`chat/sse.py`)

**Avant :** Requêtes N+1 dans une boucle
```python
for room_id in room_ids:
    new_messages = ChatMessage.query.filter_by(room_id=room_id)...  # N requêtes
    membership = ChatRoomMember.query.filter_by(room_id=room_id)...  # N requêtes
    unread_count = ChatMessage.query.filter_by(room_id=room_id)...  # N requêtes
```

**Après :** Requêtes optimisées avec sous-requêtes
```python
# Récupérer tous les derniers messages en une seule requête
last_msg_subq = db.session.query(...).subquery()
latest_messages = db.session.query(ChatMessage).join(...).all()

# Récupérer tous les membres en une seule requête
memberships_map = {m.room_id: m for m in memberships}
```

**Impact :** Réduction de N requêtes à 2-3 requêtes totales

---

## 📋 FICHIERS MODIFIÉS

1. ✅ `gunicorn.conf.py` (nouveau) - Configuration Gunicorn
2. ✅ `Procfile` - Utilise la configuration
3. ✅ `chat/sse.py` - Optimisation des requêtes SSE

---

## 🚀 DÉPLOIEMENT

### 1. Commiter les changements

```bash
git add gunicorn.conf.py Procfile chat/sse.py
git commit -m "Fix: Augmenter timeout Gunicorn et optimiser requêtes chat SSE"
git push
```

### 2. Render redéploiera automatiquement

Attendez 1-2 minutes pour le redéploiement.

### 3. Vérifier les logs

Dans **Render Dashboard** → **Logs**, cherchez :

```
✅ Application démarrée avec Gunicorn
✅ Timeout configuré: 120 secondes
```

---

## 🔍 VÉRIFICATION

### 1. Vérifier que le timeout est appliqué

Dans **Render Shell**, exécutez :

```bash
ps aux | grep gunicorn
```

Vous devriez voir les workers avec le nouveau timeout.

### 2. Tester les performances

**Avant :**
- `/chat/api/rooms` : 12-21 secondes
- `/chat/api/stream/rooms` : Timeout après 30 secondes

**Après (attendu) :**
- `/chat/api/rooms` : < 1 seconde
- `/chat/api/stream/rooms` : Pas de timeout (connexion stable)

### 3. Vérifier les logs

Dans **Render Dashboard** → **Logs**, vous ne devriez plus voir :
```
[CRITICAL] WORKER TIMEOUT
```

---

## 📊 RÉSULTATS ATTENDUS

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Timeout SSE** | 30s (crash) | 120s (stable) | ✅ Stable |
| **/chat/api/rooms** | 12-21s | < 1s | **95%** |
| **Requêtes DB SSE** | N+1 (lent) | 2-3 (rapide) | **80%** |
| **Stabilité** | Crashes fréquents | Stable | ✅ |

---

## 🚨 SI LES PROBLÈMES PERSISTENT

### 1. Vérifier la configuration Gunicorn

Dans **Render Shell**, vérifiez :

```bash
cat gunicorn.conf.py
```

### 2. Vérifier les logs Gunicorn

Dans **Render Dashboard** → **Logs**, cherchez les erreurs Gunicorn.

### 3. Augmenter encore le timeout (si nécessaire)

Dans `gunicorn.conf.py`, modifiez :

```python
timeout = 180  # 3 minutes au lieu de 2
```

**⚠️ Attention :** Ne dépassez pas 180 secondes, car Render a aussi des limites.

---

## 💡 OPTIMISATIONS FUTURES

1. **Utiliser Gevent workers** pour mieux gérer les connexions longues
2. **WebSocket** au lieu de SSE (meilleure performance)
3. **Cache Redis** pour les données de chat fréquentes
4. **Pagination** sur les messages anciens

---

## ✅ CHECKLIST

- [ ] Fichiers modifiés committés
- [ ] Changements poussés sur GitHub
- [ ] Render redéployé automatiquement
- [ ] Vérifié les logs (pas de timeout)
- [ ] Testé `/chat/api/rooms` (rapide)
- [ ] Testé `/chat/api/stream/rooms` (stable)

---

**Besoin d'aide ?** Vérifiez les logs Render pour identifier d'autres problèmes de performance.

