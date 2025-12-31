# 🔴 CRÉER LE SERVICE REDIS SUR RENDER

**Date :** 30 Décembre 2025  
**Objectif :** Créer un service Redis gratuit sur Render pour améliorer les performances

---

## 📋 ÉTAPES DÉTAILLÉES

### Étape 1 : Accéder au Dashboard Render

1. Allez sur **https://dashboard.render.com**
2. Connectez-vous avec votre compte
3. Vous devriez voir la page d'accueil avec vos services existants

---

### Étape 2 : Créer un nouveau service Redis

1. **Cliquez sur le bouton "New +"** (en haut à droite ou dans le menu)
   - Vous verrez un menu déroulant avec plusieurs options

2. **Sélectionnez "Redis"** dans la liste
   - Options possibles : Web Service, Background Worker, PostgreSQL, Redis, etc.
   - Choisissez **"Redis"**

---

### Étape 3 : Configurer le service Redis

Vous verrez un formulaire de configuration :

#### Champs à remplir :

1. **Name** (Nom du service)
   - Entrez : `import-profit-cache`
   - Ou un autre nom de votre choix (ex: `cache-redis`, `redis-cache`)

2. **Region** (Région)
   - Choisissez la **même région** que votre application Flask
   - Exemple : `Frankfurt (EU)`, `Oregon (US West)`, etc.
   - ⚠️ Important : Même région = meilleure performance

3. **Plan** (Plan tarifaire)
   - Sélectionnez **"Free"** (gratuit)
   - ✅ Le plan gratuit offre 25MB de mémoire (suffisant pour le cache)
   - ⚠️ Limite : 25MB, mais c'est largement suffisant pour le cache

4. **Redis Version** (Version)
   - Laissez la version par défaut (généralement la plus récente)
   - Exemple : `7.2` ou `7.0`

#### Résumé de la configuration :

```
Name: import-profit-cache
Region: [Même région que votre app Flask]
Plan: Free
Redis Version: [Par défaut]
```

---

### Étape 4 : Créer le service

1. **Cliquez sur le bouton "Create Redis"** (ou "Create")
2. Render va créer le service Redis
3. ⏱️ Attendez 1-2 minutes que le service soit créé

---

### Étape 5 : Récupérer l'URL Redis

Une fois le service créé :

1. **Cliquez sur votre service Redis** dans la liste
2. Vous verrez la page de détails du service Redis

3. **Cherchez la section "Connection"** ou "Connection Info"
   - Elle contient les informations de connexion

4. **Copiez "Internal Redis URL"**
   - Format : `redis://red-xxxxxxxxxxxxx:6379`
   - ⚠️ **IMPORTANT** : Utilisez **"Internal Redis URL"** (pas External)
   - L'URL interne est pour la communication entre vos services Render
   - L'URL externe est pour les connexions depuis l'extérieur de Render

#### Exemple d'URL Redis :

```
redis://red-c1234567890abcdefghij:6379
```

---

### Étape 6 : Configurer dans votre application Flask

1. **Allez dans votre service Web** (votre application Flask)
2. **Settings** → **Environment** (ou **Environment Variables**)

3. **Ajoutez/modifiez les variables suivantes :**

   | Variable | Valeur |
   |----------|--------|
   | `REDIS_URL` | `redis://red-xxxxxxxxxxxxx:6379` (l'URL que vous avez copiée) |
   | `CACHE_TYPE` | `redis` |
   | `CACHE_TIMEOUT` | `300` |

4. **Supprimez** l'ancienne variable `CACHE_TYPE = simple` si elle existe

5. **Cliquez sur "Save Changes"**
   - Render va redéployer automatiquement votre application

---

### Étape 7 : Vérifier que Redis fonctionne

Après le redéploiement (1-2 minutes), vérifiez dans **Render Shell** :

```python
python3 -c "
from app import app, cache
with app.app_context():
    if cache:
        print('Type cache:', cache.config.get('CACHE_TYPE'))
        if cache.config.get('CACHE_TYPE') == 'redis':
            print('✅ Redis configuré:', cache.config.get('CACHE_REDIS_URL'))
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

#### Résultat attendu :

```
Type cache: redis
✅ Redis configuré: redis://red-xxxxxxxxxxxxx:6379
✅ Test cache: ok
```

---

## 🚨 PROBLÈMES COURANTS

### 1. "Je ne vois pas l'option Redis"

**Solution :**
- Vérifiez que vous êtes sur la page principale du dashboard
- Le bouton "New +" devrait être visible en haut à droite
- Si vous ne voyez pas "Redis", essayez de rafraîchir la page (F5)

### 2. "Je ne trouve pas Internal Redis URL"

**Solution :**
- Dans la page de détails du service Redis
- Cherchez la section "Connection" ou "Connection Info"
- Il y a généralement deux URLs :
  - **Internal Redis URL** ← Utilisez celle-ci
  - External Redis URL (ignorez celle-ci)

### 3. "Le service Redis ne démarre pas"

**Solution :**
- Attendez 2-3 minutes
- Vérifiez les logs du service Redis
- Si erreur, supprimez et recréez le service

### 4. "Redis fonctionne mais le cache ne fonctionne pas"

**Solution :**
- Vérifiez que `REDIS_URL` est correct (copié-collé exactement)
- Vérifiez que `CACHE_TYPE=redis` est défini
- Vérifiez les logs de votre application Flask au démarrage
- Doit afficher : `✅ Cache Redis configuré: redis://...`

---

## 📊 VÉRIFICATION DANS LES LOGS

Dans **Render Dashboard** → **Votre Web Service** → **Logs**, cherchez au démarrage :

```
✅ Cache Redis configuré: redis://red-xxxxxxxxxxxxx:6379
```

Si vous voyez :
```
✅ Cache simple (mémoire) configuré
```

→ Redis n'est pas correctement configuré. Vérifiez `REDIS_URL`.

---

## 💰 COÛT

- **Plan Free** : Gratuit
- **Limite** : 25MB de mémoire (suffisant pour le cache)
- **Pas de limite de temps** (contrairement aux Web Services gratuits)

---

## ✅ CHECKLIST

- [ ] Service Redis créé sur Render
- [ ] Même région que l'application Flask
- [ ] Plan Free sélectionné
- [ ] Internal Redis URL copiée
- [ ] `REDIS_URL` configuré dans les variables d'environnement
- [ ] `CACHE_TYPE=redis` configuré
- [ ] `CACHE_TIMEOUT=300` configuré
- [ ] Ancienne variable `CACHE_TYPE=simple` supprimée
- [ ] Changements sauvegardés
- [ ] Application redéployée
- [ ] Vérification dans les logs : `✅ Cache Redis configuré`
- [ ] Test du cache fonctionne

---

## 🎯 RÉSULTAT ATTENDU

Après avoir créé Redis et configuré l'application :

1. **Performance améliorée** : Le cache fonctionne entre les redémarrages
2. **Logs** : `✅ Cache Redis configuré: redis://...`
3. **Test** : Le cache fonctionne correctement

**Impact estimé : +60% de performance sur les pages avec cache**

---

## 📝 NOTES IMPORTANTES

- ⚠️ **Internal Redis URL** : Utilisez toujours l'URL interne pour la communication entre services Render
- ⚠️ **Même région** : Créez Redis dans la même région que votre app pour meilleure performance
- ⚠️ **Plan Free** : 25MB suffit largement pour le cache (généralement < 5MB utilisés)
- ✅ **Pas de mise en veille** : Redis ne se met pas en veille (contrairement aux Web Services gratuits)

---

**Besoin d'aide ?** Si vous ne trouvez toujours pas l'option Redis, vérifiez que vous êtes bien connecté à votre compte Render et que vous avez les permissions nécessaires.

