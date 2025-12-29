# 🧪 GUIDE DE TEST - AMÉLIORATIONS PHASE 1

**Date :** 3 Décembre 2025  
**Objectif :** Tester toutes les améliorations de sécurité et performance

---

## 📋 CHECKLIST DE TEST

- [ ] Test 1 : Rate Limiting sur Login
- [ ] Test 2 : Validation Mots de Passe Forts
- [ ] Test 3 : Protection CSRF
- [ ] Test 4 : Cache Dashboard
- [ ] Test 5 : Secret Key depuis .env
- [ ] Test 6 : Performance (N+1 queries optimisées)

---

## 🔐 TEST 1 : RATE LIMITING SUR LOGIN

### Objectif
Vérifier que le rate limiting bloque les tentatives excessives de connexion.

### Étapes

1. **Ouvrir la page de login**
   ```
   http://localhost:5002/auth/login
   ```

2. **Tester avec un mauvais mot de passe**
   - Username : `admin` (ou n'importe quel utilisateur)
   - Password : `mauvais_mot_de_passe`
   - Cliquer sur "Se connecter"
   - Répéter cette action **6 fois rapidement** (dans les 30 secondes)

3. **Résultat attendu**
   - ✅ Les 5 premières tentatives affichent : "Nom d'utilisateur ou mot de passe incorrect"
   - ✅ La 6ème tentative affiche : **"Trop de tentatives de connexion. Réessayez dans une minute."**
   - ✅ Le message d'erreur est différent des messages précédents

4. **Vérification dans les logs**
   ```bash
   tail -f app.log | grep -i "rate limit"
   ```

### ✅ Critère de réussite
- Le rate limiting bloque après 5 tentatives/minute
- Message d'erreur spécifique affiché

---

## 🔒 TEST 2 : VALIDATION MOTS DE PASSE FORTS

### Objectif
Vérifier que seuls les mots de passe forts sont acceptés lors de la création d'utilisateur.

### Prérequis
- Être connecté en tant qu'administrateur
- Accéder à `/auth/register`

### Étapes

1. **Ouvrir la page de création d'utilisateur**
   ```
   http://localhost:5002/auth/register
   ```

2. **Tester avec un mot de passe faible**
   - Username : `test_user`
   - Email : `test@example.com`
   - Password : `123` (trop court)
   - Remplir les autres champs obligatoires
   - Cliquer sur "Créer l'Utilisateur"

3. **Résultat attendu**
   - ✅ Message d'erreur : "Le mot de passe doit contenir : au moins 8 caractères, au moins une majuscule, au moins une minuscule, au moins un chiffre, au moins un caractère spécial"

4. **Tester avec un mot de passe conforme**
   - Password : `Test123!@#`
   - Cliquer sur "Créer l'Utilisateur"

5. **Résultat attendu**
   - ✅ Utilisateur créé avec succès
   - ✅ Redirection vers la liste des utilisateurs

### ✅ Critère de réussite
- Les mots de passe faibles sont rejetés
- Les mots de passe forts sont acceptés
- Message d'erreur clair et détaillé

---

## 🛡️ TEST 3 : PROTECTION CSRF

### Objectif
Vérifier que les formulaires sont protégés contre les attaques CSRF.

### Étapes

1. **Vérifier le token CSRF dans le formulaire de login**
   - Ouvrir http://localhost:5002/auth/login
   - Clic droit → "Afficher le code source de la page"
   - Rechercher : `csrf_token` ou `csrf-token`

2. **Résultat attendu**
   - ✅ Un champ caché `<input type="hidden" name="csrf_token" value="...">` est présent
   - ✅ Ou une meta tag `<meta name="csrf-token" content="...">`

3. **Tester la soumission sans token**
   - Ouvrir la console du navigateur (F12)
   - Exécuter :
   ```javascript
   fetch('/auth/login', {
     method: 'POST',
     headers: {'Content-Type': 'application/x-www-form-urlencoded'},
     body: 'username=admin&password=test'
   }).then(r => r.text()).then(console.log)
   ```

4. **Résultat attendu**
   - ✅ Erreur 400 Bad Request
   - ✅ Message CSRF error (si Flask-WTF configuré correctement)

### ✅ Critère de réussite
- Token CSRF présent dans les formulaires
- Soumission sans token rejetée

---

## ⚡ TEST 4 : CACHE DASHBOARD

### Objectif
Vérifier que le cache améliore les performances du dashboard.

### Étapes

1. **Premier chargement (sans cache)**
   - Ouvrir http://localhost:5002
   - Ouvrir les outils développeur (F12) → Onglet "Network"
   - Noter le temps de chargement de la page
   - Noter le nombre de requêtes

2. **Recharger la page immédiatement**
   - Appuyer sur F5 plusieurs fois rapidement
   - Observer les temps de chargement

3. **Résultat attendu**
   - ✅ Les rechargements suivants sont **plus rapides**
   - ✅ Moins de requêtes vers la base de données (statistiques en cache)

4. **Vérification dans les logs**
   ```bash
   tail -f app.log | grep -i "cache"
   ```

5. **Tester l'expiration du cache (5 minutes)**
   - Attendre 5 minutes
   - Recharger la page
   - Le cache devrait être expiré et recalculé

### ✅ Critère de réussite
- Temps de chargement réduit après le premier chargement
- Cache fonctionnel (vérifiable dans les logs)

---

## 🔑 TEST 5 : SECRET KEY DEPUIS .ENV

### Objectif
Vérifier que la secret key est chargée depuis les variables d'environnement.

### Étapes

1. **Vérifier le fichier .env**
   ```bash
   cat .env | grep SECRET_KEY
   ```

2. **Résultat attendu**
   - ✅ Fichier `.env` existe
   - ✅ `SECRET_KEY` est défini avec une valeur longue et aléatoire

3. **Vérifier dans les logs au démarrage**
   ```bash
   grep -i "secret" app.log
   ```

4. **Résultat attendu**
   - ✅ Pas de message "Secret key générée automatiquement"
   - ✅ Ou message indiquant que la secret key vient de .env

5. **Tester la session**
   - Se connecter
   - Vérifier que la session persiste après redémarrage du navigateur (si "Se souvenir de moi" coché)

### ✅ Critère de réussite
- Secret key chargée depuis .env
- Sessions fonctionnelles

---

## 🚀 TEST 6 : PERFORMANCE (N+1 QUERIES)

### Objectif
Vérifier que les optimisations N+1 queries fonctionnent.

### Étapes

1. **Tester la page de stocks**
   - Ouvrir http://localhost:5002/stocks/depot/1 (ou un ID existant)
   - Ouvrir les outils développeur → Onglet "Network"
   - Observer le nombre de requêtes

2. **Résultat attendu**
   - ✅ Moins de requêtes qu'avant (optimisation avec `joinedload`)
   - ✅ Page charge rapidement

3. **Tester la page de flotte**
   - Ouvrir http://localhost:5002/vehicles/dashboard
   - Observer les performances

4. **Résultat attendu**
   - ✅ Chargement rapide
   - ✅ Moins de requêtes grâce aux optimisations

### ✅ Critère de réussite
- Performances améliorées
- Moins de requêtes DB

---

## 📊 RÉSUMÉ DES TESTS

### Tests de Sécurité
- ✅ Rate Limiting : Bloque les attaques brute force
- ✅ Validation Mots de Passe : Force des mots de passe forts
- ✅ Protection CSRF : Protège contre les attaques CSRF
- ✅ Secret Key : Externalisée depuis .env

### Tests de Performance
- ✅ Cache Dashboard : Réduit les requêtes DB
- ✅ Optimisation N+1 : Améliore les performances

---

## 🐛 PROBLÈMES RENCONTRÉS ?

### Rate Limiting ne fonctionne pas
- Vérifier que Flask-Limiter est installé : `pip list | grep Flask-Limiter`
- Vérifier les logs : `tail -f app.log | grep -i "rate"`

### Cache ne fonctionne pas
- Vérifier que Flask-Caching est installé : `pip list | grep Flask-Caching`
- Vérifier la configuration dans `.env` : `CACHE_TYPE=simple`

### CSRF ne fonctionne pas
- Vérifier que Flask-WTF est installé : `pip list | grep Flask-WTF`
- Vérifier que le token est présent dans les formulaires

---

## ✅ VALIDATION FINALE

Une fois tous les tests passés :

- [ ] Tous les tests de sécurité passent
- [ ] Tous les tests de performance passent
- [ ] Aucune erreur dans les logs
- [ ] Application fonctionne normalement

**Phase 1 validée ! ✅**

---

## 🎯 PROCHAINES ÉTAPES

Après validation de la Phase 1 :
1. Créer les index de base de données
2. Passer à la Phase 2 (Tests & Qualité)
3. Implémenter les tests unitaires
4. Améliorer le logging structuré

