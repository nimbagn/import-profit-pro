# 🧪 Guide de Test des Améliorations - Module Promotion

## 📋 Vue d'ensemble

Ce guide vous permet de tester manuellement toutes les améliorations implémentées dans le module Promotion.

---

## ✅ Prérequis

1. **Serveur Flask actif** sur `http://localhost:5002`
2. **Utilisateur connecté** avec les permissions `promotion.read` et `promotion.write`
3. **Données de test** : Au moins quelques membres et ventes dans la base de données

---

## 🚀 Tests à Effectuer

### 1. **Test de Performance (Optimisation N+1 Queries)**

#### Objectif
Vérifier que les requêtes SQL sont optimisées et que les pages se chargent rapidement.

#### Étapes
1. Ouvrir les **Outils de Développeur** du navigateur (F12)
2. Aller dans l'onglet **Network** (Réseau)
3. Accéder à `/promotion/members`
4. Observer le nombre de requêtes SQL dans les logs serveur

#### Résultats attendus
- ✅ Moins de 10 requêtes SQL pour charger la page
- ✅ Temps de chargement < 2 secondes
- ✅ Les équipes sont chargées en batch (pas de requêtes individuelles)

#### Vérification dans les logs
```bash
tail -f app.log | grep -i "query\|SELECT"
```

---

### 2. **Test de Pagination**

#### Test sur Members List (`/promotion/members`)

**Étapes :**
1. Accéder à `/promotion/members`
2. Vérifier la présence de la pagination en bas du tableau
3. Cliquer sur "Page 2" → Vérifier que la page change
4. Changer le nombre d'éléments par page (25, 50, 100, 200)
5. Vérifier que les filtres sont conservés lors de la navigation

**Résultats attendus :**
- ✅ Pagination visible avec boutons Précédent/Suivant
- ✅ Numéros de pages cliquables
- ✅ Sélecteur "X/page" fonctionnel
- ✅ Affichage "Affichage de X à Y sur Z membres"
- ✅ Filtres conservés dans l'URL

#### Test sur Sales List (`/promotion/sales`)

**Étapes :**
1. Accéder à `/promotion/sales`
2. Répéter les mêmes tests que pour members_list

**Résultats attendus :**
- ✅ Même comportement que members_list
- ✅ Pagination fonctionne avec les filtres actifs

---

### 3. **Test de Recherche**

#### Test sur Members List

**Étapes :**
1. Accéder à `/promotion/members`
2. Dans le champ "Rechercher", taper un nom de membre
3. Cliquer sur "Filtrer" ou appuyer sur Entrée
4. Vérifier que seuls les membres correspondants s'affichent
5. Tester avec un numéro de téléphone
6. Tester avec une recherche vide (doit afficher tous les membres)

**Résultats attendus :**
- ✅ Recherche insensible à la casse
- ✅ Recherche partielle (LIKE)
- ✅ Recherche par nom ET téléphone
- ✅ Résultats instantanés

#### Test sur Sales List

**Étapes :**
1. Accéder à `/promotion/sales`
2. Dans le champ "Rechercher", taper :
   - Un nom de membre
   - Une référence de vente
3. Vérifier les résultats

**Résultats attendus :**
- ✅ Recherche par nom de membre fonctionne
- ✅ Recherche par référence fonctionne
- ✅ Résultats filtrés correctement

---

### 4. **Test des Filtres Avancés**

#### Test sur Sales List

**Étapes :**
1. Accéder à `/promotion/sales`
2. Cliquer sur le bouton pour replier/déplier les filtres (si disponible)
3. Tester chaque filtre individuellement :
   - **Date début** : Sélectionner une date
   - **Date fin** : Sélectionner une date
   - **Équipe** : Sélectionner une équipe
   - **Membre** : Sélectionner un membre
   - **Gamme** : Sélectionner une gamme
   - **Type** : Sélectionner "Enlèvement" ou "Retour"
4. Tester des filtres combinés :
   - Date + Type
   - Équipe + Membre + Gamme
   - Tous les filtres ensemble
5. Cliquer sur "Réinitialiser" → Vérifier que tous les filtres sont effacés

**Résultats attendus :**
- ✅ Tous les filtres fonctionnent individuellement
- ✅ Les filtres combinés fonctionnent
- ✅ Le bouton "Réinitialiser" efface tous les filtres
- ✅ Les filtres sont conservés dans l'URL
- ✅ Les filtres sont appliqués à la pagination

---

### 5. **Test d'Export Excel**

#### Étapes
1. Accéder à `/promotion/sales`
2. Appliquer des filtres (optionnel) :
   - Date spécifique
   - Type de transaction
   - Membre spécifique
3. Cliquer sur le bouton **"Exporter Excel"** (vert avec icône Excel)
4. Vérifier que le fichier se télécharge
5. Ouvrir le fichier Excel téléchargé

#### Vérifications dans Excel
- ✅ Le fichier s'ouvre sans erreur
- ✅ Toutes les colonnes sont présentes :
  - Date, Référence, Type, Membre, Équipe, Gamme
  - Quantité, Prix Unitaire, Montant Total
  - Commission Unitaire, Commission Totale
- ✅ Les données correspondent aux filtres appliqués
- ✅ Une ligne "TOTAL" est présente à la fin
- ✅ Les colonnes sont bien formatées (largeur adaptée)
- ✅ Le nom du fichier contient un timestamp

#### Test avec différents filtres
1. Exporter sans filtres → Vérifier toutes les ventes
2. Exporter avec filtre date → Vérifier seulement les ventes de cette date
3. Exporter avec filtre membre → Vérifier seulement les ventes de ce membre

**Résultats attendus :**
- ✅ Export fonctionne avec tous les filtres
- ✅ Export fonctionne sans filtres (toutes les ventes)
- ✅ Fichier Excel valide et lisible
- ✅ Temps de génération < 10 secondes pour < 1000 ventes

---

### 6. **Test du Cache**

#### Objectif
Vérifier que le cache réduit les requêtes répétées.

#### Étapes
1. Ouvrir les logs serveur :
   ```bash
   tail -f app.log
   ```
2. Accéder à `/promotion/sales` plusieurs fois rapidement
3. Observer les logs pour voir si la vérification de colonne `transaction_type` n'est faite qu'une fois

#### Résultats attendus
- ✅ La première requête fait la vérification de colonne
- ✅ Les requêtes suivantes utilisent le cache (pas de nouvelle vérification pendant 1 heure)
- ✅ Message dans les logs : "Utilisation du cache" (si implémenté)

#### Vérification manuelle
- Accéder à plusieurs pages promotion rapidement
- Vérifier que les temps de réponse sont rapides (< 1s)
- Vérifier dans les logs qu'il n'y a pas de requêtes INFORMATION_SCHEMA répétées

---

## 📊 Checklist de Test Complète

### Performance
- [ ] Page members_list charge rapidement (< 2s)
- [ ] Page sales_list charge rapidement (< 2s)
- [ ] Pas de requêtes SQL répétées (N+1)
- [ ] Cache fonctionne pour vérifications de colonnes

### Pagination
- [ ] Pagination visible sur members_list
- [ ] Pagination visible sur sales_list
- [ ] Navigation entre pages fonctionne
- [ ] Sélecteur "X/page" fonctionne
- [ ] Filtres conservés lors de la navigation
- [ ] Affichage du nombre total d'éléments correct

### Recherche
- [ ] Recherche fonctionne sur members_list
- [ ] Recherche fonctionne sur sales_list
- [ ] Recherche insensible à la casse
- [ ] Recherche partielle fonctionne
- [ ] Recherche vide affiche tous les résultats

### Filtres Avancés
- [ ] Filtre par date fonctionne
- [ ] Filtre par équipe fonctionne
- [ ] Filtre par membre fonctionne
- [ ] Filtre par gamme fonctionne
- [ ] Filtre par type fonctionne
- [ ] Filtres combinés fonctionnent
- [ ] Bouton "Réinitialiser" fonctionne
- [ ] Filtres conservés dans l'URL

### Export Excel
- [ ] Bouton "Exporter Excel" visible
- [ ] Export fonctionne sans filtres
- [ ] Export fonctionne avec filtres
- [ ] Fichier Excel téléchargé correctement
- [ ] Fichier Excel contient toutes les colonnes
- [ ] Données correctes dans Excel
- [ ] Ligne TOTAL présente
- [ ] Formatage correct

---

## 🐛 Tests de Cas Limites

### Pagination
- [ ] Page 1 avec moins d'éléments que per_page
- [ ] Dernière page avec éléments restants
- [ ] Navigation avec 0 résultat
- [ ] Changement de per_page avec filtres actifs

### Recherche
- [ ] Recherche avec caractères spéciaux
- [ ] Recherche avec très long texte
- [ ] Recherche avec texte inexistant (doit afficher "Aucun résultat")

### Filtres
- [ ] Date début > Date fin (doit gérer l'erreur)
- [ ] Filtres avec valeurs inexistantes
- [ ] Tous les filtres à la fois

### Export
- [ ] Export avec 0 résultat
- [ ] Export avec très grand nombre de ventes (> 10000)
- [ ] Export avec caractères spéciaux dans les noms

---

## 📝 Rapport de Test

Après avoir effectué tous les tests, remplissez ce rapport :

**Date du test :** _______________

**Testeur :** _______________

**Résultats :**
- ✅ Tests réussis : _____ / _____
- ❌ Tests échoués : _____ / _____

**Problèmes rencontrés :**
1. _________________________________
2. _________________________________
3. _________________________________

**Temps de chargement moyen :**
- members_list : _____ secondes
- sales_list : _____ secondes
- Export Excel : _____ secondes

**Commentaires :**
_________________________________
_________________________________
_________________________________

---

## 🔧 Dépannage

### Problème : Pagination ne s'affiche pas
**Solution :** Vérifier que `pagination` est passé au template dans la route

### Problème : Export Excel ne fonctionne pas
**Solution :** 
1. Vérifier que pandas et openpyxl sont installés
2. Vérifier les permissions de l'utilisateur
3. Vérifier les logs pour erreurs

### Problème : Recherche ne fonctionne pas
**Solution :**
1. Vérifier que la recherche est dans l'URL
2. Vérifier les logs pour erreurs SQL
3. Vérifier que les colonnes existent dans la base

### Problème : Filtres ne fonctionnent pas
**Solution :**
1. Vérifier que les paramètres sont dans l'URL
2. Vérifier que les filtres sont appliqués dans la requête SQL
3. Vérifier les logs pour erreurs

---

## ✅ Validation Finale

Une fois tous les tests effectués avec succès :

- [ ] Toutes les fonctionnalités fonctionnent correctement
- [ ] Performance améliorée (temps de chargement < 2s)
- [ ] Pas d'erreurs dans les logs
- [ ] Export Excel fonctionne
- [ ] Pagination fonctionne
- [ ] Recherche fonctionne
- [ ] Filtres fonctionnent

**Signature du testeur :** _______________

**Date de validation :** _______________

