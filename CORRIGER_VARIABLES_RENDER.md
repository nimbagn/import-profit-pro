# 🔧 CORRECTION DES VARIABLES D'ENVIRONNEMENT SUR RENDER

**Date :** 30 Décembre 2025  
**Problème :** Doublons et valeurs incorrectes dans les variables d'environnement

---

## ❌ PROBLÈMES IDENTIFIÉS

### 1. Doublons détectés

- **CACHE_TYPE** : Apparaît 2 fois
  - ❌ Ancienne : `simple` (à supprimer)
  - ✅ Nouvelle : `redis` (à garder)

- **DB_POOL_SIZE** : Apparaît 2 fois
  - ❌ Ancienne : `5` (à supprimer)
  - ✅ Nouvelle : `10` (à garder)

- **DB_MAX_OVERFLOW** : Apparaît 2 fois
  - ❌ Ancienne : valeur masquée (à supprimer)
  - ✅ Nouvelle : `5` (à garder)

### 2. REDIS_URL avec placeholder

- **REDIS_URL** : `redis://red-xxxxx:6379`
  - ⚠️ C'est un placeholder, pas une vraie URL
  - ✅ À remplacer par la vraie URL Redis de votre service

---

## ✅ SOLUTION : NETTOYER LES VARIABLES

### Étape 1 : Supprimer les doublons

Dans **Render Dashboard** → **Votre Web Service** → **Settings** → **Environment** :

1. **Supprimez** les anciennes valeurs :
   - ❌ `CACHE_TYPE` = `simple` (gardez seulement `redis`)
   - ❌ `DB_POOL_SIZE` = `5` (gardez seulement `10`)
   - ❌ `DB_MAX_OVERFLOW` = ancienne valeur (gardez seulement `5`)

2. **Vérifiez** que vous avez une seule entrée pour chaque variable

### Étape 2 : Récupérer la vraie URL Redis

1. Allez sur **Render Dashboard**
2. Cliquez sur votre service **Redis** (celui que vous avez créé)
3. Dans la section **"Connection"**, copiez **"Internal Redis URL"**
   - Format attendu : `redis://red-xxxxxxxxxxxxx:6379`
   - ⚠️ Utilisez **"Internal Redis URL"** (pas External), car c'est pour la communication interne

4. Si vous n'avez pas encore créé Redis :
   - **New +** → **Redis**
   - **Name :** `import-profit-cache`
   - **Plan :** Free
   - **Create Redis**
   - Copiez l'**Internal Redis URL**

### Étape 3 : Mettre à jour REDIS_URL

Dans **Environment Variables**, modifiez :

- **REDIS_URL** : Remplacez `redis://red-xxxxx:6379` par la vraie URL
  - Exemple : `redis://red-c1234567890abcdef:6379`

### Étape 4 : Vérifier toutes les variables

Voici la liste complète des variables à avoir (sans doublons) :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `CACHE_TYPE` | `redis` | Type de cache (Redis) |
| `REDIS_URL` | `redis://red-xxxxx:6379` | URL Redis (remplacer par la vraie) |
| `CACHE_TIMEOUT` | `300` | Timeout du cache en secondes |
| `DB_POOL_SIZE` | `10` | Taille du pool de connexions |
| `DB_MAX_OVERFLOW` | `5` | Connexions supplémentaires |
| `DB_POOL_RECYCLE` | `300` | Recyclage des connexions (secondes) |
| `DATABASE_URL` | `postgresql://...` | URL de la base de données (générée automatiquement) |
| `SECRET_KEY` | `...` | Clé secrète (masquée) |
| `FLASK_ENV` | `production` | Environnement Flask |
| `FLASK_DEBUG` | `0` | Mode debug (0 = désactivé) |
| `URL_SCHEME` | `https` | Schéma d'URL |
| `MAX_CONTENT_MB` | `25` | Taille max des uploads |

---

## 🔍 VÉRIFICATION

### Après avoir nettoyé, vérifiez dans Render Shell :

```python
python3 -c "
import os
print('=== Variables d\'environnement ===')
print('CACHE_TYPE:', os.getenv('CACHE_TYPE'))
print('REDIS_URL:', os.getenv('REDIS_URL', 'NON DÉFINI'))
print('CACHE_TIMEOUT:', os.getenv('CACHE_TIMEOUT'))
print('DB_POOL_SIZE:', os.getenv('DB_POOL_SIZE'))
print('DB_MAX_OVERFLOW:', os.getenv('DB_MAX_OVERFLOW'))
print('DB_POOL_RECYCLE:', os.getenv('DB_POOL_RECYCLE'))
print()
print('=== Vérification Redis ===')
from app import app, cache
with app.app_context():
    if cache:
        print('Type cache:', cache.config.get('CACHE_TYPE'))
        if cache.config.get('CACHE_TYPE') == 'redis':
            print('✅ Redis configuré:', cache.config.get('CACHE_REDIS_URL', 'N/A'))
            # Test
            cache.set('test', 'ok', timeout=60)
            result = cache.get('test')
            print('✅ Test cache:', result)
        else:
            print('⚠️  Cache simple (pas Redis)')
    else:
        print('❌ Cache non configuré')
"
```

### Résultat attendu :

```
=== Variables d'environnement ===
CACHE_TYPE: redis
REDIS_URL: redis://red-xxxxxxxxxxxxx:6379
CACHE_TIMEOUT: 300
DB_POOL_SIZE: 10
DB_MAX_OVERFLOW: 5
DB_POOL_RECYCLE: 300

=== Vérification Redis ===
Type cache: redis
✅ Redis configuré: redis://red-xxxxxxxxxxxxx:6379
✅ Test cache: ok
```

---

## 📋 CHECKLIST FINALE

- [ ] Supprimé les doublons (`CACHE_TYPE`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`)
- [ ] Remplacé `REDIS_URL` par la vraie URL Redis
- [ ] Vérifié qu'il n'y a qu'une seule entrée par variable
- [ ] Sauvegardé les changements (Render redéploiera automatiquement)
- [ ] Vérifié dans les logs que Redis fonctionne : `✅ Cache Redis configuré`
- [ ] Testé le cache avec la commande de vérification ci-dessus

---

## 🚨 SI REDIS NE FONCTIONNE TOUJOURS PAS

### Vérifier que Redis est créé :

1. Allez sur **Render Dashboard**
2. Vérifiez que vous avez un service **Redis** actif
3. Si non, créez-le (voir étape 2 ci-dessus)

### Vérifier l'URL Redis :

- ✅ **Bonne URL** : `redis://red-xxxxxxxxxxxxx:6379` (avec des caractères alphanumériques)
- ❌ **Mauvaise URL** : `redis://red-xxxxx:6379` (placeholder)

### Vérifier les logs au démarrage :

Dans **Render Dashboard** → **Logs**, cherchez au démarrage :

```
✅ Cache Redis configuré: redis://red-xxxxxxxxxxxxx:6379
```

Si vous voyez :
```
✅ Cache simple (mémoire) configuré
```

→ Redis n'est pas correctement configuré. Vérifiez `REDIS_URL`.

---

## 💡 CONSEIL

Après avoir nettoyé les variables, **attendez le redéploiement automatique** (1-2 minutes), puis vérifiez les logs pour confirmer que Redis est bien configuré.

**Besoin d'aide ?** Consultez `GUIDE_OPTIMISATION_RENDER.md` pour plus de détails.

