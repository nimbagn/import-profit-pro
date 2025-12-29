# 🧪 Guide de Test en Live - Gestion des Stocks

**Date**: 21 Décembre 2025  
**Serveur**: http://localhost:5002

---

## ✅ STATUT DU SERVEUR

Le serveur Flask est **démarré** et écoute sur le port **5002**.

**Vérification**:
- ✅ Processus Python détecté sur le port 5002
- ✅ Serveur en cours d'exécution

---

## 🚀 DÉMARRAGE DES TESTS

### Étape 1 : Accéder à l'application

1. Ouvrez votre navigateur
2. Allez sur : **http://localhost:5002**
3. Vous devriez voir la page d'accueil ou la page de connexion

### Étape 2 : Se connecter

**Identifiants de test** :
- **Username** : `admin`
- **Password** : `admin123`

---

## 📋 CHECKLIST DE TESTS

### ✅ Test 1 : Liste des Mouvements

**URL** : http://localhost:5002/stocks/movements

**À vérifier** :
- [ ] La page se charge sans erreur
- [ ] Les mouvements sont filtrés par région (si utilisateur non-admin)
- [ ] La pagination fonctionne
- [ ] Les filtres (date, type, dépôt, véhicule) fonctionnent
- [ ] Les colonnes sont visibles (pas masquées)

**Corrections testées** :
- ✅ Filtrage par région implémenté
- ✅ Optimisation des requêtes

---

### ✅ Test 2 : Créer un Transfert

**URL** : http://localhost:5002/stocks/movements/new?type=transfer

**À vérifier** :
- [ ] Le formulaire se charge
- [ ] Validation source != destination fonctionne
- [ ] Possibilité d'ajouter plusieurs articles
- [ ] Après création, **2 mouvements sont créés** (OUT et IN)
- [ ] Les références sont au format : `TRANS-YYYYMMDD-XXXX-OUT` et `TRANS-YYYYMMDD-XXXX-IN`

**Corrections testées** :
- ✅ Validation source != destination
- ✅ Création de 2 mouvements (sortie + entrée)
- ✅ Transactions atomiques

**Test à effectuer** :
1. Sélectionner un dépôt source
2. Sélectionner un dépôt destination différent
3. Ajouter 2-3 articles avec quantités
4. Soumettre le formulaire
5. Vérifier dans la liste des mouvements que 2 mouvements sont créés pour chaque article

---

### ✅ Test 3 : Créer une Réception

**URL** : http://localhost:5002/stocks/receptions/new

**À vérifier** :
- [ ] Le formulaire se charge
- [ ] La référence générée utilise UUID (pas de blocage de 1 seconde)
- [ ] Format de référence : `REC-YYYYMMDD-UUID8CHARS`
- [ ] Le stock est incrémenté après création
- [ ] Un mouvement de type 'reception' est créé

**Corrections testées** :
- ✅ Génération de référence avec UUID (pas de time.sleep)
- ✅ Filtrage par région

**Test à effectuer** :
1. Remplir le formulaire (dépôt, fournisseur, BL, date)
2. Ajouter des articles
3. Soumettre
4. Vérifier que la référence est générée instantanément
5. Vérifier que le stock du dépôt est mis à jour

---

### ✅ Test 4 : Créer une Sortie

**URL** : http://localhost:5002/stocks/outgoings/new

**À vérifier** :
- [ ] Le formulaire se charge
- [ ] Après création, le mouvement créé contient `[SORTIE_CLIENT]` dans le reason
- [ ] Le reason contient aussi la référence de la sortie
- [ ] Le stock est décrémenté
- [ ] Un mouvement négatif est créé

**Corrections testées** :
- ✅ Marqueur `[SORTIE_CLIENT]` dans le reason
- ✅ Référence de sortie incluse dans le reason

**Test à effectuer** :
1. Remplir le formulaire (client, dépôt/véhicule)
2. Ajouter des articles
3. Soumettre
4. Vérifier dans les mouvements que le reason contient `[SORTIE_CLIENT]`
5. Vérifier que le stock est décrémenté

---

### ✅ Test 5 : Créer un Retour

**URL** : http://localhost:5002/stocks/returns/new

**À vérifier** :
- [ ] Le formulaire se charge
- [ ] Après création, le mouvement créé contient `[RETOUR_CLIENT]` dans le reason
- [ ] Le reason contient aussi la référence du retour
- [ ] Le stock est incrémenté
- [ ] Un mouvement positif est créé

**Corrections testées** :
- ✅ Marqueur `[RETOUR_CLIENT]` dans le reason
- ✅ Référence de retour incluse dans le reason

**Test à effectuer** :
1. Remplir le formulaire (client, dépôt/véhicule)
2. Ajouter des articles
3. Soumettre
4. Vérifier dans les mouvements que le reason contient `[RETOUR_CLIENT]`
5. Vérifier que le stock est incrémenté

---

### ✅ Test 6 : Récapitulatif du Stock

**URL** : http://localhost:5002/stocks/summary

**À vérifier** :
- [ ] La page se charge sans erreur
- [ ] Les stocks sont calculés correctement
- [ ] Les filtres (période, dépôt, véhicule) fonctionnent
- [ ] Les calculs de balance sont corrects (mouvements négatifs gérés)
- [ ] Pas de double comptage
- [ ] Les données sont filtrées par région

**Corrections testées** :
- ✅ Calcul de stock corrigé (gestion mouvements négatifs)
- ✅ Suppression du double comptage
- ✅ Filtrage par région
- ✅ Optimisation N+1

**Test à effectuer** :
1. Ouvrir le récapitulatif
2. Vérifier que les totaux sont cohérents
3. Filtrer par période (aujourd'hui, semaine, mois)
4. Vérifier que les calculs sont corrects

---

### ✅ Test 7 : Suppression de Mouvement

**URL** : http://localhost:5002/stocks/movements

**À vérifier** :
- [ ] Seuls les admins peuvent voir le bouton de suppression
- [ ] Si on essaie de supprimer un mouvement lié à une réception, erreur affichée
- [ ] Si on essaie de supprimer un mouvement lié à une sortie, erreur affichée
- [ ] Si on essaie de supprimer un mouvement lié à un retour, erreur affichée
- [ ] Les mouvements indépendants peuvent être supprimés

**Corrections testées** :
- ✅ Vérification des dépendances avant suppression
- ✅ Messages d'erreur clairs

**Test à effectuer** :
1. Créer une réception
2. Essayer de supprimer le mouvement associé
3. Vérifier que l'erreur appropriée est affichée
4. Supprimer d'abord la réception
5. Vérifier que le mouvement peut maintenant être supprimé

---

### ✅ Test 8 : Performance et Optimisations

**À vérifier** :
- [ ] Les listes se chargent rapidement (< 2 secondes)
- [ ] Le récapitulatif ne charge pas trop de données
- [ ] Les mouvements récents sont limités à 1000
- [ ] Pas de requêtes SQL excessives (vérifier dans les logs)

**Corrections testées** :
- ✅ Limitation à 1000 mouvements récents
- ✅ Optimisation N+1 (2 requêtes au lieu de N)

**Test à effectuer** :
1. Ouvrir la console développeur (F12)
2. Aller dans l'onglet Network
3. Charger différentes pages de stocks
4. Vérifier le nombre de requêtes et le temps de chargement

---

## 🔍 VÉRIFICATIONS SPÉCIFIQUES DES CORRECTIONS

### Correction #1 : Mouvements de chargement (2 mouvements)

**Test** :
1. Valider une commande commerciale
2. Aller dans le dashboard magasinier
3. Vérifier le récapitulatif de chargement
4. Exécuter le chargement
5. Vérifier dans les mouvements que **2 mouvements sont créés** :
   - Un avec `-OUT` dans la référence (sortie source)
   - Un avec `-IN` dans la référence (entrée destination)

### Correction #2 : Génération UUID

**Test** :
1. Créer plusieurs réceptions rapidement (en succession)
2. Vérifier que les références sont générées instantanément
3. Vérifier le format : `REC-YYYYMMDD-UUID8CHARS`
4. Vérifier qu'il n'y a pas de blocage de 1 seconde

### Correction #3 : Filtrage par région

**Test** :
1. Se connecter avec un utilisateur non-admin (commercial)
2. Vérifier qu'il ne voit que les données de sa région
3. Vérifier les listes (mouvements, réceptions, sorties, retours)
4. Vérifier le récapitulatif

### Correction #4 : Transactions atomiques

**Test** :
1. Créer un transfert avec plusieurs articles
2. Simuler une erreur (ex: stock insuffisant pour un article)
3. Vérifier qu'**aucun** mouvement n'est créé (rollback complet)
4. Corriger l'erreur et réessayer
5. Vérifier que **tous** les mouvements sont créés

---

## 📊 RÉSULTATS ATTENDUS

### ✅ Tous les tests doivent passer

- ✅ Pas d'erreurs dans la console du navigateur
- ✅ Pas d'erreurs dans les logs du serveur
- ✅ Les fonctionnalités fonctionnent comme prévu
- ✅ Les performances sont bonnes
- ✅ Les données sont cohérentes

---

## 🐛 EN CAS DE PROBLÈME

### Le serveur ne démarre pas
```bash
# Vérifier les logs
tail -f flask_output.log

# Redémarrer
pkill -f "python.*app.py"
python3 app.py
```

### Erreurs dans le navigateur
1. Ouvrir la console développeur (F12)
2. Vérifier les erreurs JavaScript
3. Vérifier les erreurs réseau
4. Vérifier les logs du serveur

### Erreurs dans les logs
1. Vérifier la connexion à la base de données
2. Vérifier les permissions des utilisateurs
3. Vérifier que les tables existent

---

## 📝 NOTES

- Tous les tests nécessitent une connexion à la base de données
- Les tests de filtrage par région nécessitent des utilisateurs avec régions assignées
- Les tests de performance nécessitent des données de test

---

**✅ Prêt pour les tests en live !**

Ouvrez http://localhost:5002 dans votre navigateur et commencez les tests.

