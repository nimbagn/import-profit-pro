# 🧪 GUIDE DE TEST DÉTAILLÉ - CORRECTIONS MODULE FLOTTE

**Date :** 3 Décembre 2025  
**Version :** 1.0  
**Objectif :** Tester toutes les corrections effectuées dans le module flotte

---

## 📋 PRÉREQUIS

### 1. Application lancée
- ✅ Serveur Flask démarré sur http://localhost:5002
- ✅ Base de données MySQL connectée
- ✅ Utilisateur administrateur créé

### 2. Données de test nécessaires
- Au moins **2 véhicules** dans la base de données
- Au moins **2 utilisateurs** (conducteurs) dans la base de données
- Au moins **1 assignation** existante pour un véhicule

### 3. Accès requis
- Connexion en tant qu'administrateur ou utilisateur avec permissions `vehicles.read` et `vehicles.update`

---

## 🎯 CORRECTION 1 : VALIDATION DE CHEVAUCHEMENT D'ASSIGNATIONS

### Objectif du test
Vérifier que le système empêche la création d'assignations en double pour le même conducteur sur une période qui chevauche.

### Scénario de test

#### **TEST 1.1 : Assignation normale (succès)**

**Étapes :**
1. Se connecter à l'application : http://localhost:5002/auth/login
2. Naviguer vers : **Référentiels** → **Véhicules**
3. Cliquer sur un véhicule (ou accéder directement à `/vehicles/<id>`)
4. Aller dans l'onglet **"Assignations"**
5. Cliquer sur **"Nouvelle Assignation"**
6. Remplir le formulaire :
   - **Conducteur** : Sélectionner un utilisateur
   - **Date de début** : Date d'aujourd'hui ou future
   - **Raison** : "Test assignation normale"
   - **Notes** : Optionnel
7. Cliquer sur **"Enregistrer"**

**Résultat attendu :**
- ✅ Assignation créée avec succès
- ✅ Message flash vert : "Assignation créée avec succès"
- ✅ Redirection vers la page des assignations
- ✅ Nouvelle assignation visible dans la liste
- ✅ Véhicule mis à jour avec le nouveau conducteur

**Critères de succès :**
- [ ] Assignation créée sans erreur
- [ ] Message de succès affiché
- [ ] Assignation visible dans la liste

---

#### **TEST 1.2 : Chevauchement de dates (échec attendu)**

**Étapes :**
1. Se connecter à l'application
2. Naviguer vers un véhicule qui a déjà une assignation active
3. Aller dans l'onglet **"Assignations"**
4. Noter la date de début de l'assignation existante
5. Cliquer sur **"Nouvelle Assignation"**
6. Remplir le formulaire :
   - **Conducteur** : **MÊME utilisateur** que l'assignation existante
   - **Date de début** : **Date qui chevauche** avec l'assignation existante
     - Exemple : Si assignation existante du 01/12/2025 au 31/12/2025
     - Utiliser une date entre le 01/12 et le 31/12
   - **Raison** : "Test chevauchement"
7. Cliquer sur **"Enregistrer"**

**Résultat attendu :**
- ❌ Assignation **NON créée**
- ❌ Message flash rouge : "Ce conducteur a déjà une assignation active pour cette période"
- ✅ Formulaire reste affiché avec les données saisies
- ✅ Assignation existante non modifiée

**Critères de succès :**
- [ ] Message d'erreur affiché
- [ ] Assignation non créée
- [ ] Assignation existante intacte
- [ ] Formulaire toujours visible

---

#### **TEST 1.3 : Assignation avec dates non chevauchantes (succès)**

**Étapes :**
1. Se connecter à l'application
2. Naviguer vers un véhicule avec une assignation existante
3. Aller dans l'onglet **"Assignations"**
4. Noter la date de fin de l'assignation existante (ou date actuelle si active)
5. Cliquer sur **"Nouvelle Assignation"**
6. Remplir le formulaire :
   - **Conducteur** : Même utilisateur que l'assignation existante
   - **Date de début** : **Date APRÈS** la fin de l'assignation existante
     - Exemple : Si assignation existante jusqu'au 31/12/2025
     - Utiliser une date après le 31/12/2025 (ex: 01/01/2026)
   - **Raison** : "Test assignation séquentielle"
7. Cliquer sur **"Enregistrer"**

**Résultat attendu :**
- ✅ Assignation créée avec succès
- ✅ Message flash vert : "Assignation créée avec succès"
- ✅ Deux assignations visibles (ancienne et nouvelle)
- ✅ Pas de chevauchement

**Critères de succès :**
- [ ] Assignation créée sans erreur
- [ ] Pas de message d'erreur de chevauchement
- [ ] Les deux assignations visibles

---

#### **TEST 1.4 : Assignation pour un autre conducteur (succès)**

**Étapes :**
1. Se connecter à l'application
2. Naviguer vers un véhicule avec une assignation active
3. Aller dans l'onglet **"Assignations"**
4. Cliquer sur **"Nouvelle Assignation"**
5. Remplir le formulaire :
   - **Conducteur** : **AUTRE utilisateur** (différent du conducteur actuel)
   - **Date de début** : Date qui chevauche avec l'assignation existante
   - **Raison** : "Changement de conducteur"
6. Cliquer sur **"Enregistrer"**

**Résultat attendu :**
- ✅ Assignation créée avec succès
- ✅ L'ancienne assignation automatiquement terminée (date de fin = date de début - 1 jour)
- ✅ Nouveau conducteur assigné au véhicule
- ✅ Message flash vert : "Assignation créée avec succès"

**Critères de succès :**
- [ ] Nouvelle assignation créée
- [ ] Ancienne assignation terminée automatiquement
- [ ] Véhicule mis à jour avec le nouveau conducteur

---

### 📊 Résumé des tests - Correction 1

| Test | Scénario | Résultat Attendu | Statut |
|------|----------|------------------|--------|
| 1.1 | Assignation normale | ✅ Succès | ☐ |
| 1.2 | Chevauchement même conducteur | ❌ Erreur | ☐ |
| 1.3 | Dates non chevauchantes | ✅ Succès | ☐ |
| 1.4 | Autre conducteur | ✅ Succès | ☐ |

---

## 🎯 CORRECTION 2 : GESTION D'ERREUR AMÉLIORÉE

### Objectif du test
Vérifier que la gestion d'erreur dans `vehicle_detail()` fonctionne correctement même si certaines tables n'existent pas.

### Scénario de test

#### **TEST 2.1 : Fiche véhicule avec table VehicleCost existante**

**Étapes :**
1. Se connecter à l'application
2. Naviguer vers : **Référentiels** → **Véhicules**
3. Cliquer sur un véhicule pour accéder à sa fiche complète
4. Vérifier que la page se charge correctement
5. Vérifier l'onglet **"Coûts"** (si présent)

**Résultat attendu :**
- ✅ Page chargée sans erreur
- ✅ Tous les onglets visibles
- ✅ Si table VehicleCost existe : coûts affichés
- ✅ Si table VehicleCost n'existe pas : pas d'erreur, valeurs par défaut

**Critères de succès :**
- [ ] Page chargée sans erreur 500
- [ ] Pas d'erreur dans les logs serveur
- [ ] Tous les onglets fonctionnels

---

#### **TEST 2.2 : Vérification des logs serveur**

**Étapes :**
1. Ouvrir un terminal
2. Exécuter : `tail -f app.log`
3. Accéder à une fiche véhicule dans le navigateur
4. Observer les logs

**Résultat attendu :**
- ✅ Pas d'erreur `ImportError` ou `AttributeError` non gérée
- ✅ Si table VehicleCost n'existe pas : message `⚠️ Erreur lors de la récupération des coûts: ...` dans les logs
- ✅ Application continue de fonctionner normalement

**Critères de succès :**
- [ ] Pas d'erreur critique dans les logs
- [ ] Erreurs gérées proprement avec logging
- [ ] Application stable

---

#### **TEST 2.3 : Test avec plusieurs véhicules**

**Étapes :**
1. Se connecter à l'application
2. Accéder à plusieurs fiches véhicules différentes
3. Vérifier que toutes se chargent correctement

**Résultat attendu :**
- ✅ Toutes les fiches se chargent sans erreur
- ✅ Comportement cohérent pour tous les véhicules

**Critères de succès :**
- [ ] Toutes les fiches accessibles
- [ ] Pas d'erreur aléatoire

---

### 📊 Résumé des tests - Correction 2

| Test | Scénario | Résultat Attendu | Statut |
|------|----------|------------------|--------|
| 2.1 | Fiche véhicule chargement | ✅ Succès | ☐ |
| 2.2 | Vérification logs | ✅ Pas d'erreur critique | ☐ |
| 2.3 | Plusieurs véhicules | ✅ Succès | ☐ |

---

## 🎯 CORRECTION 3 : OPTIMISATION REQUÊTES (JOINEDLOAD)

### Objectif du test
Vérifier que les optimisations `joinedload()` réduisent le nombre de requêtes DB et améliorent les performances.

### Scénario de test

#### **TEST 3.1 : Comparaison des requêtes DB (avec SQLALCHEMY_ECHO)**

**Préparation :**
1. Modifier temporairement `config.py` ou `.env` :
   ```python
   SQLALCHEMY_ECHO = True
   ```
2. Redémarrer l'application

**Étapes :**
1. Ouvrir un terminal pour voir les logs
2. Exécuter : `tail -f app.log | grep "SELECT"`
3. Dans le navigateur, accéder à une fiche véhicule avec beaucoup de données :
   - Documents : au moins 5
   - Maintenances : au moins 5
   - Relevés odomètre : au moins 10
   - Mouvements de stock : au moins 5
4. Compter le nombre de requêtes `SELECT` dans les logs

**Résultat attendu :**
- ✅ Nombre de requêtes réduit grâce à `joinedload()`
- ✅ Requêtes groupées (JOIN) au lieu de requêtes séparées
- ✅ Temps de chargement réduit

**Critères de succès :**
- [ ] Moins de requêtes qu'avant l'optimisation
- [ ] Requêtes avec JOIN visibles dans les logs
- [ ] Temps de chargement < 1 seconde

---

#### **TEST 3.2 : Test de performance - Dashboard flotte**

**Étapes :**
1. Ouvrir les outils de développement du navigateur (F12)
2. Aller dans l'onglet **"Network"**
3. Accéder au dashboard flotte : http://localhost:5002/vehicles/dashboard
4. Noter le temps de chargement de la page
5. Vérifier le nombre de requêtes HTTP

**Résultat attendu :**
- ✅ Temps de chargement < 500ms
- ✅ Nombre de requêtes HTTP minimal
- ✅ Page réactive

**Critères de succès :**
- [ ] Temps de chargement acceptable
- [ ] Pas de requêtes HTTP inutiles

---

#### **TEST 3.3 : Test de performance - Fiche véhicule**

**Étapes :**
1. Ouvrir les outils de développement du navigateur (F12)
2. Aller dans l'onglet **"Network"**
3. Accéder à une fiche véhicule complète : `/vehicles/<id>`
4. Noter le temps de chargement
5. Vérifier que tous les onglets se chargent rapidement

**Résultat attendu :**
- ✅ Temps de chargement < 800ms
- ✅ Tous les onglets accessibles rapidement
- ✅ Pas de délai lors du changement d'onglet

**Critères de succès :**
- [ ] Temps de chargement acceptable
- [ ] Navigation fluide entre onglets

---

#### **TEST 3.4 : Test avec plusieurs utilisateurs simultanés**

**Étapes :**
1. Ouvrir plusieurs onglets du navigateur
2. Accéder à différentes fiches véhicules en parallèle
3. Vérifier que toutes se chargent correctement

**Résultat attendu :**
- ✅ Toutes les pages se chargent sans erreur
- ✅ Pas de ralentissement significatif
- ✅ Pas d'erreur de connexion DB

**Critères de succès :**
- [ ] Toutes les pages accessibles
- [ ] Performance stable

---

### 📊 Résumé des tests - Correction 3

| Test | Scénario | Résultat Attendu | Statut |
|------|----------|------------------|--------|
| 3.1 | Comparaison requêtes DB | ✅ Moins de requêtes | ☐ |
| 3.2 | Performance dashboard | ✅ < 500ms | ☐ |
| 3.3 | Performance fiche véhicule | ✅ < 800ms | ☐ |
| 3.4 | Utilisateurs simultanés | ✅ Stable | ☐ |

---

## 🎯 CORRECTION 4 : IMPORT `or_` CORRIGÉ

### Objectif du test
Vérifier que l'import `or_` fonctionne correctement et que le code compile sans erreur.

### Scénario de test

#### **TEST 4.1 : Vérification de l'import**

**Étapes :**
1. Ouvrir un terminal
2. Exécuter :
   ```bash
   python3 -c "from flotte import flotte_bp; from sqlalchemy import or_; print('✅ Import réussi')"
   ```

**Résultat attendu :**
- ✅ Import réussi sans erreur
- ✅ Message "✅ Import réussi" affiché

**Critères de succès :**
- [ ] Pas d'erreur d'import
- [ ] Code exécuté avec succès

---

#### **TEST 4.2 : Test de compilation**

**Étapes :**
1. Ouvrir un terminal
2. Exécuter :
   ```bash
   python3 -m py_compile flotte.py
   ```

**Résultat attendu :**
- ✅ Compilation réussie
- ✅ Aucune erreur de syntaxe

**Critères de succès :**
- [ ] Compilation réussie
- [ ] Pas d'erreur de syntaxe

---

#### **TEST 4.3 : Test fonctionnel - Utilisation de `or_`**

**Étapes :**
1. Se connecter à l'application
2. Tester la fonctionnalité qui utilise `or_` (validation de chevauchement)
3. Vérifier que tout fonctionne correctement

**Résultat attendu :**
- ✅ Fonctionnalité opérationnelle
- ✅ Pas d'erreur liée à `or_`

**Critères de succès :**
- [ ] Fonctionnalité fonctionne
- [ ] Pas d'erreur dans les logs

---

### 📊 Résumé des tests - Correction 4

| Test | Scénario | Résultat Attendu | Statut |
|------|----------|------------------|--------|
| 4.1 | Vérification import | ✅ Succès | ☐ |
| 4.2 | Test compilation | ✅ Succès | ☐ |
| 4.3 | Test fonctionnel | ✅ Succès | ☐ |

---

## 📊 CHECKLIST GLOBALE DES TESTS

### Correction 1 : Validation chevauchement
- [ ] TEST 1.1 : Assignation normale
- [ ] TEST 1.2 : Chevauchement (échec attendu)
- [ ] TEST 1.3 : Dates non chevauchantes
- [ ] TEST 1.4 : Autre conducteur

### Correction 2 : Gestion d'erreur
- [ ] TEST 2.1 : Fiche véhicule chargement
- [ ] TEST 2.2 : Vérification logs
- [ ] TEST 2.3 : Plusieurs véhicules

### Correction 3 : Optimisation requêtes
- [ ] TEST 3.1 : Comparaison requêtes DB
- [ ] TEST 3.2 : Performance dashboard
- [ ] TEST 3.3 : Performance fiche véhicule
- [ ] TEST 3.4 : Utilisateurs simultanés

### Correction 4 : Import `or_`
- [ ] TEST 4.1 : Vérification import
- [ ] TEST 4.2 : Test compilation
- [ ] TEST 4.3 : Test fonctionnel

---

## 🔍 COMMANDES UTILES POUR LES TESTS

### Voir les logs en temps réel
```bash
tail -f app.log
```

### Filtrer les requêtes SQL
```bash
tail -f app.log | grep "SELECT"
```

### Vérifier les erreurs
```bash
tail -f app.log | grep -i "error\|exception"
```

### Tester l'import Python
```bash
python3 -c "from flotte import flotte_bp; print('OK')"
```

### Compiler le module
```bash
python3 -m py_compile flotte.py
```

---

## 📝 RAPPORT DE TEST

### Template de rapport

```
Date du test : ___________
Testeur : ___________

CORRECTION 1 : Validation chevauchement
- TEST 1.1 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 1.2 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 1.3 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 1.4 : ☐ Réussi ☐ Échec - Notes : ___________

CORRECTION 2 : Gestion d'erreur
- TEST 2.1 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 2.2 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 2.3 : ☐ Réussi ☐ Échec - Notes : ___________

CORRECTION 3 : Optimisation requêtes
- TEST 3.1 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 3.2 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 3.3 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 3.4 : ☐ Réussi ☐ Échec - Notes : ___________

CORRECTION 4 : Import or_
- TEST 4.1 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 4.2 : ☐ Réussi ☐ Échec - Notes : ___________
- TEST 4.3 : ☐ Réussi ☐ Échec - Notes : ___________

PROBLÈMES RENCONTRÉS :
_________________________________________________
_________________________________________________

RECOMMANDATIONS :
_________________________________________________
_________________________________________________
```

---

## ✅ CRITÈRES DE VALIDATION GLOBAUX

### Tous les tests doivent passer pour valider les corrections :

1. **Fonctionnalité** : Toutes les fonctionnalités corrigées fonctionnent comme prévu
2. **Performance** : Pas de régression de performance
3. **Stabilité** : Pas d'erreur critique ou de crash
4. **Compatibilité** : Compatible avec les données existantes
5. **Sécurité** : Pas de faille de sécurité introduite

---

## 🚨 EN CAS DE PROBLÈME

### Si un test échoue :

1. **Noter l'erreur exacte** dans les logs
2. **Reproduire le problème** avec les mêmes étapes
3. **Vérifier les données** de test (sont-elles correctes ?)
4. **Consulter les logs serveur** : `tail -f app.log`
5. **Vérifier la console navigateur** (F12 → Console)

### Erreurs courantes :

- **Erreur 500** : Vérifier les logs serveur
- **Erreur 404** : Vérifier que la route existe
- **Erreur de permission** : Vérifier les permissions utilisateur
- **Erreur DB** : Vérifier la connexion MySQL

---

## 📞 SUPPORT

Pour toute question ou problème lors des tests, consulter :
- `ANALYSE_MODULE_FLOTTE.md` - Analyse complète
- `CORRECTIONS_MODULE_FLOTTE.md` - Détails des corrections
- Logs serveur : `app.log`

---

**Bon test ! 🚀**

