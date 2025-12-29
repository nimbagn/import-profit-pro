# 🧪 TESTS RAPIDES - AMÉLIORATIONS PHASE 1

## ✅ TEST 1 : RATE LIMITING (2 minutes)

1. **Ouvrir** : http://localhost:5002/auth/login
2. **Essayer de se connecter 6 fois rapidement** avec :
   - Username : `admin`
   - Password : `mauvais123`
3. **Résultat attendu** : Après 5 tentatives → "Trop de tentatives de connexion"

---

## ✅ TEST 2 : MOT DE PASSE FORT (2 minutes)

1. **Ouvrir** : http://localhost:5002/auth/register
2. **Essayer de créer un utilisateur** avec :
   - Password : `123` (trop court)
3. **Résultat attendu** : Message d'erreur détaillé
4. **Réessayer** avec : `Test123!@#`
5. **Résultat attendu** : Succès ✅

---

## ✅ TEST 3 : CSRF PROTECTION (1 minute)

1. **Ouvrir** : http://localhost:5002/auth/login
2. **Se connecter** normalement
3. **Vérifier** : Le formulaire contient un champ `<input type="hidden" name="csrf_token">`
4. **Ouvrir** les outils développeur (F12) → Onglet "Network"
5. **Soumettre** un formulaire
6. **Vérifier** : Le header contient `csrf_token`

---

## ✅ TEST 4 : CACHE DASHBOARD (1 minute)

1. **Se connecter** : http://localhost:5002/auth/login
2. **Ouvrir** : http://localhost:5002 (Dashboard)
3. **Noter** le temps de chargement
4. **Recharger** la page (F5)
5. **Résultat attendu** : Chargement plus rapide (données en cache)

---

## 📊 VÉRIFICATION DES LOGS

```bash
tail -f app.log | grep -E "(Rate|Cache|CSRF|✅)"
```

---

## 🎯 RÉSULTATS ATTENDUS

- ✅ Rate limiting : Bloque après 5 tentatives
- ✅ Mots de passe : Validation stricte active
- ✅ CSRF : Token présent dans les formulaires
- ✅ Cache : Dashboard plus rapide au 2ème chargement

