# 🔴 CONFIGURATION REDIS POUR LE CACHE (PRODUCTION)

**Date :** 3 Décembre 2025  
**Objectif :** Configurer Redis pour le cache en production

---

## 📋 PRÉREQUIS

### 1. Installation de Redis

#### Sur macOS (Homebrew)
```bash
brew install redis
brew services start redis
```

#### Sur Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### Sur Windows
Télécharger depuis : https://redis.io/download

### 2. Vérification de Redis

```bash
redis-cli ping
# Devrait répondre : PONG
```

---

## ⚙️ CONFIGURATION

### 1. Installation de redis-py

```bash
pip install redis
```

### 2. Configuration dans `.env`

Ajouter les lignes suivantes dans le fichier `.env` :

```env
# Cache Redis
CACHE_TYPE=redis
REDIS_URL=redis://localhost:6379/0
CACHE_TIMEOUT=300
```

### 3. Configuration dans `app.py`

Le code dans `app.py` devrait déjà être compatible :

```python
# Si Redis est configuré
redis_url = os.getenv('REDIS_URL', '')
if redis_url and redis_url != 'memory://' and redis_url.startswith('redis://'):
    cache_config['CACHE_TYPE'] = 'redis'
    cache_config['CACHE_REDIS_URL'] = redis_url
    print(f"✅ Cache Redis configuré: {redis_url}")
```

---

## 🧪 TEST DE LA CONFIGURATION

### 1. Vérifier Redis

```bash
# Vérifier que Redis fonctionne
redis-cli ping

# Voir les clés en cache
redis-cli KEYS "*"

# Voir une clé spécifique
redis-cli GET "flotte_dashboard_2025-12-03"
```

### 2. Tester l'application

1. **Redémarrer l'application** après modification du `.env`
2. **Vérifier les logs** :
   ```bash
   tail -f app.log | grep -i "redis\|cache"
   ```
3. **Devrait afficher** : `✅ Cache Redis configuré: redis://localhost:6379/0`

### 3. Vérifier le cache dans Redis

```bash
# Après avoir accédé au dashboard
redis-cli KEYS "flotte_dashboard_*"

# Voir le contenu d'une clé
redis-cli GET "flotte_dashboard_2025-12-03"
```

---

## 🔧 CONFIGURATION AVANCÉE

### 1. Redis avec authentification

Si Redis nécessite un mot de passe :

```env
REDIS_URL=redis://:password@localhost:6379/0
```

### 2. Redis sur un serveur distant

```env
REDIS_URL=redis://user:password@redis.example.com:6379/0
```

### 3. Redis avec SSL/TLS

```env
REDIS_URL=rediss://user:password@redis.example.com:6380/0
```

### 4. Configuration complète dans `.env`

```env
# Cache Redis
CACHE_TYPE=redis
REDIS_URL=redis://localhost:6379/0
CACHE_TIMEOUT=300
CACHE_KEY_PREFIX=flotte_
CACHE_DEFAULT_TIMEOUT=3600
```

---

## 📊 AVANTAGES DE REDIS

### vs Cache mémoire (simple)

| Caractéristique | Mémoire | Redis |
|----------------|---------|-------|
| **Persistance** | ❌ Perdu au redémarrage | ✅ Persistant |
| **Partage entre processus** | ❌ Non | ✅ Oui |
| **Partage entre serveurs** | ❌ Non | ✅ Oui |
| **Performance** | ⚡ Très rapide | ⚡ Rapide |
| **Scalabilité** | ❌ Limitée | ✅ Excellente |
| **Production** | ❌ Non recommandé | ✅ Recommandé |

---

## 🚀 MIGRATION VERS REDIS

### Étapes

1. **Installer Redis** sur le serveur
2. **Installer redis-py** : `pip install redis`
3. **Modifier `.env`** avec la configuration Redis
4. **Redémarrer l'application**
5. **Vérifier les logs** pour confirmer l'utilisation de Redis
6. **Tester le cache** avec le guide de test

---

## 🔍 MONITORING REDIS

### Commandes utiles

```bash
# Voir toutes les clés
redis-cli KEYS "*"

# Compter les clés
redis-cli DBSIZE

# Voir les informations du serveur
redis-cli INFO

# Voir la mémoire utilisée
redis-cli INFO memory

# Vider le cache (attention !)
redis-cli FLUSHDB
```

### Monitoring en temps réel

```bash
# Surveiller les commandes Redis
redis-cli MONITOR

# Voir les statistiques
redis-cli --stat
```

---

## 🛡️ SÉCURITÉ

### 1. Protection par mot de passe

Dans `redis.conf` :
```
requirepass votre_mot_de_passe_securise
```

Puis dans `.env` :
```env
REDIS_URL=redis://:votre_mot_de_passe_securise@localhost:6379/0
```

### 2. Firewall

Limiter l'accès à Redis uniquement depuis l'application :
```bash
# Autoriser uniquement localhost
sudo ufw allow from 127.0.0.1 to any port 6379
```

### 3. Binding

Dans `redis.conf`, limiter l'écoute :
```
bind 127.0.0.1
```

---

## 🐛 DÉPANNAGE

### Problème 1 : Redis non accessible

**Erreur :** `Connection refused` ou `Cannot connect to Redis`

**Solutions :**
1. Vérifier que Redis est démarré : `redis-cli ping`
2. Vérifier le port : `netstat -an | grep 6379`
3. Vérifier l'URL dans `.env`

### Problème 2 : Authentification échouée

**Erreur :** `NOAUTH Authentication required`

**Solutions :**
1. Vérifier le mot de passe dans `.env`
2. Tester la connexion : `redis-cli -a password ping`

### Problème 3 : Cache ne fonctionne pas avec Redis

**Solutions :**
1. Vérifier les logs : `grep -i "redis\|cache" app.log`
2. Tester Redis directement : `redis-cli SET test "value"` puis `redis-cli GET test`
3. Vérifier que `redis-py` est installé : `pip list | grep redis`

---

## ✅ CHECKLIST DE CONFIGURATION

- [ ] Redis installé et démarré
- [ ] `redis-py` installé (`pip install redis`)
- [ ] Configuration dans `.env` ajoutée
- [ ] Application redémarrée
- [ ] Logs vérifiés (Redis configuré)
- [ ] Cache testé et fonctionnel
- [ ] Sécurité configurée (mot de passe, firewall)

---

## 📝 EXEMPLE DE CONFIGURATION COMPLÈTE

### `.env` (Production)

```env
# Base de données
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=madargn
DB_USER=root
DB_PASSWORD=votre_mot_de_passe

# Cache Redis
CACHE_TYPE=redis
REDIS_URL=redis://:mot_de_passe_redis@127.0.0.1:6379/0
CACHE_TIMEOUT=300

# Sécurité
SECRET_KEY=votre_secret_key_tres_longue_et_securisee
```

---

## 🎯 RECOMMANDATIONS

### Développement
- ✅ Utiliser le cache mémoire (simple) - plus facile
- ✅ Pas besoin de Redis

### Production
- ✅ Utiliser Redis pour la persistance
- ✅ Configurer l'authentification
- ✅ Configurer le firewall
- ✅ Monitorer Redis régulièrement

---

**Configuration Redis prête pour la production ! 🚀**

