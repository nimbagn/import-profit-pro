# 🧪 GUIDE DE TEST - CACHE FLOTTE

**Date :** 3 Décembre 2025  
**Objectif :** Vérifier que le cache fonctionne correctement pour le dashboard flotte

---

## 📋 PRÉREQUIS

### 1. Application lancée
- ✅ Serveur Flask démarré sur http://localhost:5002
- ✅ Flask-Caching installé et activé
- ✅ Cache configuré (mémoire ou Redis)

### 2. Outils nécessaires
- Navigateur web avec outils de développement (F12)
- Terminal pour voir les logs
- Accès administrateur à l'application

---

## 🎯 TEST 1 : VÉRIFICATION DU CACHE (PREMIER ACCÈS)

### Objectif
Vérifier que le cache est bien activé et que les données sont calculées lors du premier accès.

### Étapes

1. **Ouvrir les outils de développement** (F12 dans le navigateur)
2. **Aller dans l'onglet "Network"** (Réseau)
3. **Vider le cache du navigateur** (Ctrl+Shift+R ou Cmd+Shift+R)
4. **Accéder au dashboard flotte** : http://localhost:5002/vehicles/dashboard
5. **Noter le temps de chargement** dans l'onglet Network
6. **Vérifier les logs serveur** :
   ```bash
   tail -f app.log | grep -i "cache\|dashboard"
   ```

### Résultat attendu

- ✅ Page chargée avec succès
- ✅ Temps de chargement : ~500-1200ms (premier calcul)
- ✅ Logs serveur : Calcul des statistiques (pas de cache hit)
- ✅ Données affichées correctement

### Critères de succès

- [ ] Page chargée sans erreur
- [ ] Temps de chargement acceptable (< 2 secondes)
- [ ] Toutes les statistiques affichées
- [ ] Pas d'erreur dans les logs

---

## 🎯 TEST 2 : CACHE HIT (ACCÈS RAPIDE)

### Objectif
Vérifier que le cache fonctionne et que les accès suivants sont plus rapides.

### Étapes

1. **Sans fermer le navigateur**, recharger la page du dashboard
   - Utiliser F5 ou Ctrl+R (pas Ctrl+Shift+R)
2. **Noter le temps de chargement** dans l'onglet Network
3. **Comparer avec le temps du premier accès**
4. **Vérifier les logs serveur** :
   ```bash
   tail -f app.log | grep -i "cache"
   ```

### Résultat attendu

- ✅ Temps de chargement réduit : ~50-200ms (cache hit)
- ✅ Amélioration de 80-90% par rapport au premier accès
- ✅ Logs serveur : Pas de nouvelles requêtes DB (cache utilisé)
- ✅ Données identiques au premier accès

### Critères de succès

- [ ] Temps de chargement < 200ms
- [ ] Amélioration de performance visible
- [ ] Données identiques
- [ ] Pas de nouvelles requêtes DB dans les logs

---

## 🎯 TEST 3 : EXPIRATION DU CACHE (APRÈS 5 MINUTES)

### Objectif
Vérifier que le cache expire correctement après 5 minutes et recalcule les données.

### Étapes

1. **Accéder au dashboard** et noter l'heure
2. **Attendre 5 minutes et 10 secondes** (au-delà de la durée du cache)
3. **Recharger la page** du dashboard
4. **Noter le temps de chargement**
5. **Vérifier les logs serveur**

### Résultat attendu

- ✅ Temps de chargement similaire au premier accès (~500-1200ms)
- ✅ Nouveau calcul des statistiques
- ✅ Cache invalidé automatiquement
- ✅ Données mises à jour si changements dans la DB

### Critères de succès

- [ ] Cache expiré après 5 minutes
- [ ] Nouveau calcul effectué
- [ ] Données à jour

---

## 🎯 TEST 4 : CACHE AVEC PLUSIEURS UTILISATEURS

### Objectif
Vérifier que le cache fonctionne correctement avec plusieurs utilisateurs simultanés.

### Étapes

1. **Ouvrir plusieurs onglets** du navigateur (ou plusieurs navigateurs)
2. **Accéder au dashboard** dans chaque onglet
3. **Noter les temps de chargement** de chaque onglet
4. **Vérifier que tous utilisent le même cache**

### Résultat attendu

- ✅ Premier onglet : Temps normal (calcul)
- ✅ Autres onglets : Temps réduit (cache hit)
- ✅ Tous les onglets affichent les mêmes données
- ✅ Pas de conflit entre utilisateurs

### Critères de succès

- [ ] Cache partagé entre utilisateurs
- [ ] Performance améliorée pour tous
- [ ] Données cohérentes

---

## 🎯 TEST 5 : INVALIDATION MANUELLE DU CACHE

### Objectif
Vérifier que le cache peut être invalidé manuellement si nécessaire.

### Étapes

1. **Accéder au dashboard** (cache hit attendu)
2. **Modifier une donnée** dans la base (ex: créer un nouveau véhicule)
3. **Attendre moins de 5 minutes**
4. **Recharger le dashboard**
5. **Vérifier si les nouvelles données apparaissent**

### Résultat attendu

- ⚠️ Les nouvelles données peuvent ne pas apparaître immédiatement (cache actif)
- ✅ Après expiration du cache (5 min), les nouvelles données apparaissent
- ✅ Comportement normal du cache

### Note
Pour invalider le cache manuellement, il faudrait ajouter une fonction d'invalidation dans le code.

---

## 📊 COMPARAISON DES PERFORMANCES

### Tableau de comparaison

| Test | Scénario | Temps Attendu | Cache |
|------|----------|---------------|-------|
| Test 1 | Premier accès | ~500-1200ms | ❌ Miss |
| Test 2 | Accès immédiat | ~50-200ms | ✅ Hit |
| Test 3 | Après expiration | ~500-1200ms | ❌ Miss |
| Test 4 | Utilisateurs multiples | Variable | ✅ Hit (après premier) |

---

## 🔍 VÉRIFICATION DES LOGS

### Commandes utiles

```bash
# Voir tous les logs
tail -f app.log

# Filtrer les logs de cache
tail -f app.log | grep -i "cache"

# Voir les requêtes DB
tail -f app.log | grep -i "SELECT\|INSERT\|UPDATE"

# Compter les requêtes
tail -f app.log | grep -c "SELECT"
```

### Logs attendus

**Premier accès (cache miss) :**
```
✅ Calcul des statistiques du dashboard
[Plusieurs requêtes SELECT]
```

**Accès suivant (cache hit) :**
```
✅ Données récupérées depuis le cache
[Pas ou très peu de requêtes SELECT]
```

---

## 🧪 TEST AUTOMATISÉ (OPTIONNEL)

### Script Python de test

```python
import requests
import time

url = "http://localhost:5002/vehicles/dashboard"

# Test 1: Premier accès
print("Test 1: Premier accès (cache miss)")
start = time.time()
response = requests.get(url)
first_time = time.time() - start
print(f"Temps: {first_time:.3f}s")
print(f"Status: {response.status_code}")

# Test 2: Accès immédiat (cache hit)
print("\nTest 2: Accès immédiat (cache hit)")
start = time.time()
response = requests.get(url)
second_time = time.time() - start
print(f"Temps: {second_time:.3f}s")
print(f"Status: {response.status_code}")

# Comparaison
improvement = ((first_time - second_time) / first_time) * 100
print(f"\nAmélioration: {improvement:.1f}%")
if improvement > 50:
    print("✅ Cache fonctionne correctement!")
else:
    print("⚠️ Cache peut ne pas fonctionner correctement")
```

---

## ✅ CHECKLIST DE VALIDATION

### Tests fonctionnels

- [ ] Test 1 : Premier accès fonctionne
- [ ] Test 2 : Cache hit fonctionne (performance améliorée)
- [ ] Test 3 : Cache expire après 5 minutes
- [ ] Test 4 : Cache partagé entre utilisateurs
- [ ] Test 5 : Comportement normal avec données modifiées

### Performance

- [ ] Temps de chargement réduit de > 50% avec cache
- [ ] Pas de régression de performance
- [ ] Mémoire utilisée acceptable

### Stabilité

- [ ] Pas d'erreur lors de l'utilisation du cache
- [ ] Application stable avec cache activé
- [ ] Pas de fuite mémoire

---

## 🚨 PROBLÈMES COURANTS

### Problème 1 : Cache ne fonctionne pas

**Symptômes :**
- Temps de chargement identique à chaque accès
- Logs montrent toujours des requêtes DB

**Solutions :**
1. Vérifier que Flask-Caching est installé : `pip list | grep Flask-Caching`
2. Vérifier les logs au démarrage : `grep -i "cache" app.log`
3. Vérifier la configuration dans `app.py`

### Problème 2 : Données obsolètes

**Symptômes :**
- Les nouvelles données n'apparaissent pas immédiatement
- Données affichées ne correspondent pas à la DB

**Solutions :**
1. Attendre l'expiration du cache (5 minutes)
2. Redémarrer l'application pour vider le cache
3. Implémenter une invalidation manuelle du cache

### Problème 3 : Cache trop lent

**Symptômes :**
- Temps de chargement toujours élevé même avec cache

**Solutions :**
1. Vérifier que le cache est bien utilisé (logs)
2. Vérifier la configuration du cache
3. Considérer Redis pour de meilleures performances

---

## 📝 RAPPORT DE TEST

### Template

```
Date du test : ___________
Testeur : ___________

TEST 1 : Premier accès
- Temps de chargement : ___________
- Status : ☐ Réussi ☐ Échec
- Notes : ___________

TEST 2 : Cache hit
- Temps de chargement : ___________
- Amélioration : ___________
- Status : ☐ Réussi ☐ Échec
- Notes : ___________

TEST 3 : Expiration cache
- Temps après expiration : ___________
- Status : ☐ Réussi ☐ Échec
- Notes : ___________

TEST 4 : Utilisateurs multiples
- Status : ☐ Réussi ☐ Échec
- Notes : ___________

PROBLÈMES RENCONTRÉS :
_________________________________________________
_________________________________________________

RECOMMANDATIONS :
_________________________________________________
_________________________________________________
```

---

## ✅ CONCLUSION

Après avoir effectué tous les tests :

1. **Si tous les tests passent** : ✅ Cache fonctionne correctement
2. **Si certains tests échouent** : Consulter la section "Problèmes courants"
3. **Pour améliorer** : Considérer Redis pour la production

---

**Bon test ! 🚀**

