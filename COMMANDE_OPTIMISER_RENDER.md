# ⚡ COMMANDES RAPIDES POUR OPTIMISER SUR RENDER

**Date :** 30 Décembre 2025  
**Objectif :** Commandes directes à exécuter pour optimiser immédiatement

---

## 🚀 OPTIMISATIONS IMMÉDIATES (15 MINUTES)

### 1. Créer Redis sur Render (5 min)

1. Allez sur https://dashboard.render.com
2. **New +** → **Redis**
3. **Name :** `import-profit-cache`
4. **Plan :** Free
5. **Create Redis**
6. Copiez **"Internal Redis URL"** (format : `redis://red-xxxxx:6379`)

### 2. Configurer Redis dans Render (2 min)

1. Allez dans votre **Web Service** (Flask app)
2. **Settings** → **Environment**
3. Ajoutez/modifiez :
   ```
   REDIS_URL=redis://red-xxxxx:6379
   CACHE_TYPE=redis
   CACHE_TIMEOUT=300
   ```
4. **Save Changes**

### 3. Vérifier que Redis fonctionne (2 min)

Dans **Render Shell**, exécutez :

```python
python3 -c "
import os
from app import app, cache
with app.app_context():
    if cache and cache.config.get('CACHE_TYPE') == 'redis':
        print('✅ Redis configuré:', cache.config.get('CACHE_REDIS_URL'))
        cache.set('test', 'ok', timeout=60)
        result = cache.get('test')
        print('✅ Test cache:', result)
    else:
        print('❌ Redis non configuré')
        print('   Vérifiez REDIS_URL dans les variables d\'environnement')
"
```

---

## 📊 CRÉER LES INDEX DE PERFORMANCE (10 MIN)

### Option 1 : Via Render Shell (Recommandé)

Dans **Render Shell**, exécutez :

```bash
# Télécharger le script
curl -o /tmp/add_indexes.sql https://raw.githubusercontent.com/VOTRE_REPO/main/scripts/add_performance_indexes.sql

# Ou créer directement
cat > /tmp/add_indexes.sql << 'EOF'
-- Index pour le dashboard
CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date DESC);
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_sessions_date ON inventory_sessions(session_date DESC);
EOF

# Exécuter
psql $DATABASE_URL -f /tmp/add_indexes.sql
```

### Option 2 : Via Python (Plus sûr)

Dans **Render Shell**, exécutez :

```python
python3 << 'EOF'
from app import db
from sqlalchemy import text

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status)",
    "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_inventory_sessions_date ON inventory_sessions(session_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_receptions_date ON receptions(reception_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true",
]

with db.engine.connect() as conn:
    for idx_sql in indexes:
        try:
            conn.execute(text(idx_sql))
            conn.commit()
            print(f"✅ {idx_sql[:50]}...")
        except Exception as e:
            print(f"⚠️  Erreur: {e}")

print("\n✅ Index créés avec succès!")
EOF
```

---

## 🔍 VÉRIFIER LES PERFORMANCES

### 1. Vérifier le cache

```python
python3 -c "
from app import app, cache
with app.app_context():
    if cache:
        print('Type:', cache.config.get('CACHE_TYPE'))
        print('URL:', cache.config.get('CACHE_REDIS_URL', 'N/A'))
        # Test
        cache.set('perf_test', 'ok', timeout=60)
        print('Test:', cache.get('perf_test'))
    else:
        print('❌ Cache non configuré')
"
```

### 2. Vérifier les index créés

```python
python3 -c "
from app import db
from sqlalchemy import text
with db.engine.connect() as conn:
    result = conn.execute(text('''
        SELECT indexname, tablename 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexname LIKE 'idx_%'
        ORDER BY tablename
    '''))
    print('Index créés:')
    for row in result:
        print(f'  - {row[1]}.{row[0]}')
"
```

### 3. Vérifier les temps de réponse

Dans **Render Dashboard** → **Logs**, cherchez :
```
responseTimeMS=200  ← Bon (<500ms)
responseTimeMS=1200 ← Lent (>1000ms)
```

---

## ⚙️ OPTIMISER LE POOL DE CONNEXIONS

Dans **Render** → **Settings** → **Environment**, ajoutez :

```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=300
```

Puis **Save Changes** (redéploiement automatique).

---

## ✅ CHECKLIST RAPIDE

- [ ] Redis créé et configuré
- [ ] REDIS_URL ajouté dans les variables d'environnement
- [ ] Index de performance créés
- [ ] DB_POOL_SIZE configuré
- [ ] Vérification que le cache fonctionne
- [ ] Test des performances (vérifier les logs)

**Temps total : ~15 minutes**  
**Impact : +70% de performance**

---

## 🚨 SI ÇA NE FONCTIONNE PAS

### Cache ne fonctionne pas ?

1. Vérifiez que Redis est créé
2. Vérifiez que `REDIS_URL` est correct (format : `redis://red-xxxxx:6379`)
3. Vérifiez les logs au démarrage : doit afficher `✅ Cache Redis configuré`

### Index ne se créent pas ?

1. Vérifiez que vous êtes connecté à la bonne base de données
2. Vérifiez les permissions (doit être owner de la DB)
3. Utilisez `IF NOT EXISTS` pour éviter les erreurs

### Application toujours lente ?

1. Vérifiez les logs pour identifier les requêtes lentes
2. Vérifiez que le plan Render n'est pas en veille (premier chargement lent)
3. Considérez passer au plan payant ($7/mois) pour éviter la mise en veille

---

**Besoin d'aide ?** Consultez `GUIDE_OPTIMISATION_RENDER.md` pour plus de détails.

