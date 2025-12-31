# 🚀 GUIDE D'OPTIMISATION POUR RENDER

**Date :** 30 Décembre 2025  
**Objectif :** Optimiser les performances de l'application sur Render

---

## 🔍 DIAGNOSTIC DES CAUSES DE LENTEUR

### Causes principales identifiées :

1. **Plan gratuit Render** : Mise en veille après 15 min d'inactivité (premier chargement lent)
2. **Cache en mémoire** : Utilise "simple" au lieu de Redis (perdu au redémarrage)
3. **Pas de compression Gzip** : Fichiers statiques non compressés
4. **Pool de connexions DB** : Configuration par défaut peut être optimisée
5. **Requêtes N+1** : Certaines requêtes non optimisées
6. **Pas de pagination** : Chargement de toutes les données à la fois

---

## ⚡ OPTIMISATIONS IMMÉDIATES (À APPLIQUER MAINTENANT)

### 1. Activer Redis pour le Cache (PRIORITÉ HAUTE)

**Problème :** Le cache "simple" est perdu à chaque redémarrage sur Render.

**Solution :** Utiliser Redis (gratuit sur Render jusqu'à 25MB).

#### Étape 1 : Créer un service Redis sur Render

1. Allez sur https://dashboard.render.com
2. Cliquez sur **"New +"** → **"Redis"**
3. Configurez :
   - **Name :** `import-profit-cache` (ou autre nom)
   - **Plan :** Free (25MB suffit pour le cache)
   - **Region :** Même région que votre app
4. Cliquez sur **"Create Redis"**

#### Étape 2 : Récupérer l'URL Redis

1. Dans votre service Redis, copiez **"Internal Redis URL"**
2. Format : `redis://red-xxxxx:6379`

#### Étape 3 : Configurer dans Render

1. Allez dans votre service Web (Flask app)
2. **Settings** → **Environment**
3. Ajoutez/modifiez :
   ```
   REDIS_URL=redis://red-xxxxx:6379
   CACHE_TYPE=redis
   CACHE_TIMEOUT=300
   ```
4. **Save Changes**

#### Étape 4 : Redéployer

Render redéploiera automatiquement. Vérifiez les logs :
```
✅ Cache Redis configuré: redis://red-xxxxx:6379
```

**Impact estimé :** +60% de performance sur les pages avec cache

---

### 2. Activer la Compression Gzip (PRIORITÉ HAUTE)

**Problème :** Les fichiers CSS/JS sont envoyés sans compression.

**Solution :** Installer Flask-Compress.

#### Étape 1 : Ajouter à requirements.txt

```bash
Flask-Compress>=1.14
```

#### Étape 2 : Modifier app.py

Ajoutez après l'initialisation de Flask :

```python
# Compression Gzip
try:
    from flask_compress import Compress
    Compress(app)
    print("✅ Compression Gzip activée")
except ImportError:
    print("⚠️  Flask-Compress non installé. Compression désactivée.")
```

**Impact estimé :** -70% de taille des fichiers statiques

---

### 3. Optimiser le Pool de Connexions DB

**Problème :** Configuration par défaut peut être améliorée pour Render.

**Solution :** Ajuster les variables d'environnement dans Render.

#### Dans Render → Settings → Environment, ajoutez :

```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=300
```

**Explication :**
- `DB_POOL_SIZE=10` : 10 connexions permanentes (au lieu de 5)
- `DB_MAX_OVERFLOW=5` : 5 connexions supplémentaires si besoin
- `DB_POOL_RECYCLE=300` : Recycler les connexions après 5 min (évite les timeouts)

**Impact estimé :** Meilleure gestion des connexions simultanées

---

### 4. Optimiser le Cache du Dashboard

**Problème :** Le dashboard fait beaucoup de requêtes à chaque chargement.

**Solution :** Le cache est déjà implémenté, mais vérifiez qu'il fonctionne.

#### Vérification dans les logs Render :

Cherchez dans les logs :
```
✅ Cache Redis configuré: redis://...
```

Si vous voyez :
```
✅ Cache simple (mémoire) configuré
```

→ **Redis n'est pas configuré !** Suivez l'étape 1 ci-dessus.

#### Augmenter le timeout du cache dashboard

Dans `app.py`, ligne ~793, le cache est à 300 secondes (5 min). Vous pouvez augmenter :

```python
# Mettre en cache les statistiques (cache 10 minutes)
if app.cache:
    app.cache.set(cache_key, stats, timeout=600)  # 10 minutes au lieu de 5
```

**Impact estimé :** Réduction de 90% des requêtes DB sur le dashboard

---

## 🔧 OPTIMISATIONS AVANCÉES

### 5. Ajouter des Index de Base de Données

**Problème :** Certaines requêtes sont lentes sans index.

**Solution :** Créer des index sur les colonnes fréquemment utilisées.

#### Créer un script SQL :

```sql
-- scripts/add_performance_indexes.sql

-- Index pour le dashboard
CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_simulations_completed ON simulations(is_completed);
CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date DESC);
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- Index pour les filtres par région
CREATE INDEX IF NOT EXISTS idx_depots_region ON depots(region_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_region ON vehicles(region_id);
```

#### Exécuter sur Render :

1. **Render Shell** → Connectez-vous
2. Exécutez :
```bash
psql $DATABASE_URL -f scripts/add_performance_indexes.sql
```

**Impact estimé :** +30% de vitesse sur les requêtes filtrées

---

### 6. Pagination sur les Listes

**Problème :** Chargement de toutes les données à la fois.

**Solution :** Implémenter la pagination (déjà fait pour certains modules).

Vérifiez que la pagination est activée sur :
- ✅ Dashboard (limite à 10 simulations récentes)
- ⚠️ Listes d'articles, stocks, commandes (à vérifier)

---

### 7. Lazy Loading des Images

**Problème :** Toutes les images se chargent immédiatement.

**Solution :** Ajouter `loading="lazy"` aux images.

Dans vos templates, remplacez :
```html
<img src="...">
```

Par :
```html
<img src="..." loading="lazy">
```

**Impact estimé :** Chargement initial plus rapide

---

## 📊 MONITORING DES PERFORMANCES

### Vérifier les performances dans Render

1. **Logs** → Cherchez les temps de réponse :
   ```
   responseTimeMS=1200  ← Trop lent (>1000ms)
   responseTimeMS=200   ← Acceptable (<500ms)
   ```

2. **Metrics** → Surveillez :
   - **CPU Usage** : Doit être < 50% en moyenne
   - **Memory Usage** : Doit être < 80%
   - **Response Time** : Doit être < 500ms

### Commandes de diagnostic

Dans **Render Shell**, exécutez :

```python
# Vérifier le cache
python3 -c "
from app import app, cache
with app.app_context():
    if cache:
        print('✅ Cache configuré:', cache.config)
        # Tester le cache
        cache.set('test', 'value', timeout=60)
        print('✅ Cache fonctionne:', cache.get('test'))
    else:
        print('❌ Cache non configuré')
"

# Vérifier les connexions DB
python3 -c "
from app import db
from sqlalchemy import text
with db.engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM users'))
    print('✅ Connexion DB OK:', result.scalar())
"
```

---

## 🎯 CHECKLIST D'OPTIMISATION

### À faire immédiatement :

- [ ] **1. Créer Redis sur Render** (5 min)
- [ ] **2. Configurer REDIS_URL dans Render** (2 min)
- [ ] **3. Ajouter Flask-Compress** (5 min)
- [ ] **4. Optimiser DB_POOL_SIZE** (2 min)
- [ ] **5. Vérifier que le cache fonctionne** (2 min)

**Temps total : ~15 minutes**  
**Impact estimé : +70% de performance**

### À faire cette semaine :

- [ ] **6. Créer les index de performance** (10 min)
- [ ] **7. Vérifier la pagination partout** (30 min)
- [ ] **8. Ajouter lazy loading aux images** (15 min)

**Temps total : ~1 heure**  
**Impact estimé : +20% de performance supplémentaire**

---

## 🚨 PROBLÈMES COURANTS SUR RENDER

### 1. "Application en veille" (premier chargement lent)

**Cause :** Plan gratuit → Mise en veille après 15 min d'inactivité.

**Solutions :**
- **Option 1 :** Utiliser un service de "ping" gratuit (UptimeRobot, etc.) pour maintenir l'app éveillée
- **Option 2 :** Passer au plan payant ($7/mois) pour éviter la mise en veille

### 2. "Timeout sur les requêtes DB"

**Cause :** Connexions DB qui expirent.

**Solution :** Configurer `DB_POOL_RECYCLE=300` (voir étape 3)

### 3. "Cache ne fonctionne pas"

**Cause :** Redis non configuré ou URL incorrecte.

**Solution :** Vérifier `REDIS_URL` dans les variables d'environnement Render

---

## 📈 RÉSULTATS ATTENDUS

### Avant optimisation :
- **Temps de chargement dashboard :** ~2-3 secondes
- **Temps de réponse API :** ~800-1200ms
- **Taille des fichiers statiques :** ~500KB non compressés

### Après optimisation :
- **Temps de chargement dashboard :** ~0.5-1 seconde (avec cache)
- **Temps de réponse API :** ~200-400ms
- **Taille des fichiers statiques :** ~150KB compressés

**Amélioration globale : +70% de performance**

---

## 🔗 RESSOURCES

- [Documentation Render - Performance](https://render.com/docs/performance)
- [Documentation Flask-Caching](https://flask-caching.readthedocs.io/)
- [Documentation Flask-Compress](https://github.com/colour-science/flask-compress)

---

## ✅ PROCHAINES ÉTAPES

1. **Appliquez les optimisations immédiates** (étapes 1-4)
2. **Testez les performances** (vérifiez les logs Render)
3. **Appliquez les optimisations avancées** si nécessaire
4. **Surveillez les métriques** dans Render Dashboard

**Besoin d'aide ?** Vérifiez les logs Render pour identifier les goulots d'étranglement spécifiques.

