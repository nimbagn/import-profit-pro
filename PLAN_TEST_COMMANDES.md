# 📋 Plan de Test en Live - Système de Commandes Commerciales

## 🎯 Objectif
Tester en conditions réelles le système de commandes commerciales avec validation hiérarchique et génération de bons de sortie.

---

## 📅 Informations de Test
- **Date de test** : _______________
- **Testeur Commercial** : _______________
- **Testeur Hiérarchie** : _______________
- **Testeur Magasinier** : _______________
- **Environnement** : Production / Développement

---

## ✅ Prérequis
- [ ] Base de données initialisée avec les tables de commandes
- [ ] Au moins 1 commercial créé et connecté
- [ ] Au moins 1 superviseur/admin créé et connecté
- [ ] Au moins 1 magasinier créé et connecté
- [ ] Au moins 5 articles de stock créés
- [ ] Au moins 1 dépôt avec stock disponible

---

## 🧪 TESTS - CRÉATION DE COMMANDE (Commercial)

### Test 1.1 : Accès à la page de création
- [ ] **Action** : Se connecter en tant que commercial → Cliquer sur "Nouvelle Commande"
- [ ] **Résultat attendu** : Page `/orders/new` s'affiche avec le formulaire
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.2 : Ajout d'un premier client
- [ ] **Action** : Cliquer sur "Ajouter Client" → Remplir :
  - Nom : "Amadou Diallo"
  - Téléphone : "612345678"
  - Adresse : "Conakry, Hamdallaye"
  - Type de paiement : "Comptant"
  - Commentaires : "Client fidèle, paiement immédiat"
- [ ] **Résultat attendu** : Colonne client apparaît dans le tableau
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.3 : Ajout d'articles pour le premier client
- [ ] **Action** : 
  - Rechercher "Riz" → Ajouter
  - Dans la colonne Client 1, saisir :
    - Quantité Riz : 10
    - Prix unitaire : 5000 GNF
  - Rechercher "Javel" → Ajouter
  - Quantité Javel : 5
  - Prix unitaire : 3000 GNF
- [ ] **Résultat attendu** : Articles ajoutés dans le tableau pour Client 1
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.4 : Ajout d'un deuxième client avec crédit
- [ ] **Action** : Cliquer sur "Ajouter Client" → Remplir :
  - Nom : "Mamadou Camara"
  - Téléphone : "622345678"
  - Type de paiement : "Crédit"
  - Échéance : Date dans 30 jours
  - Commentaires : "Paiement à crédit, échéance dans 30 jours"
- [ ] **Résultat attendu** : 
  - Colonne Client 2 apparaît
  - Champ "Échéance" visible et obligatoire
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.5 : Ajout d'articles pour le deuxième client
- [ ] **Action** : 
  - Pour Client 2, ajouter :
    - Riz : 5 unités à 5000 GNF
    - Javel : 10 unités à 3000 GNF
- [ ] **Résultat attendu** : Articles ajoutés pour Client 2
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.6 : Ajout d'un troisième client
- [ ] **Action** : Ajouter Client 3 "Fatou Bah" avec plusieurs articles
- [ ] **Résultat attendu** : Client 3 ajouté avec succès
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.7 : Validation du formulaire
- [ ] **Action** : Cliquer sur "Enregistrer et Soumettre à Validation"
- [ ] **Résultat attendu** : 
  - Message de succès : "Commande créée avec succès et soumise à validation"
  - Redirection vers la page de détail de la commande
  - Statut : "En attente de validation"
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 1.8 : Vérification des données sauvegardées
- [ ] **Action** : Vérifier la page de détail de la commande
- [ ] **Résultat attendu** : 
  - Tous les clients affichés
  - Tous les articles pour chaque client
  - Type de paiement affiché (badge Comptant/Crédit)
  - Échéance affichée si crédit
  - Commentaires et notes affichés
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🧪 TESTS - VALIDATION HIÉRARCHIQUE

### Test 2.1 : Accès à la liste des commandes (Hiérarchie)
- [ ] **Action** : Se connecter en tant que superviseur/admin → Aller sur `/orders`
- [ ] **Résultat attendu** : Liste de TOUTES les commandes (pas seulement celles du superviseur)
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 2.2 : Voir les détails d'une commande en attente
- [ ] **Action** : Cliquer sur la commande créée précédemment
- [ ] **Résultat attendu** : 
  - Détails complets affichés
  - Section "Validation de la Commande" visible
  - Boutons "Valider" et "Rejeter" disponibles
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 2.3 : Validation d'une commande
- [ ] **Action** : Cliquer sur "Valider la Commande"
- [ ] **Résultat attendu** : 
  - Message : "Commande validée avec succès"
  - Statut passe à "Validée"
  - Date et nom du validateur affichés
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 2.4 : Rejet d'une commande (test avec une autre commande)
- [ ] **Action** : 
  - Créer une nouvelle commande (commercial)
  - Se connecter en hiérarchie
  - Cliquer sur "Rejeter"
  - Saisir la raison : "Stock insuffisant"
- [ ] **Résultat attendu** : 
  - Message : "Commande rejetée"
  - Statut passe à "Rejetée"
  - Raison du rejet affichée
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🧪 TESTS - GÉNÉRATION DE BONS DE SORTIE (Magasinier)

### Test 3.1 : Accès aux commandes validées (Magasinier)
- [ ] **Action** : Se connecter en tant que magasinier → Aller sur `/orders` → Filtrer par "Validée"
- [ ] **Résultat attendu** : Liste des commandes validées affichées
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 3.2 : Voir les détails d'une commande validée
- [ ] **Action** : Cliquer sur une commande validée
- [ ] **Résultat attendu** : 
  - Section "Générer les Bons de Sortie" visible
  - Formulaire avec sélection dépôt/véhicule
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 3.3 : Génération des bons de sortie
- [ ] **Action** : 
  - Sélectionner un dépôt source avec stock suffisant
  - Cliquer sur "Générer les Bons de Sortie"
- [ ] **Résultat attendu** : 
  - Message : "X bon(s) de sortie créé(s) avec succès"
  - Un bon de sortie créé pour CHAQUE client
  - Stock décrémenté du dépôt
  - Commande passe au statut "Complétée"
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 3.4 : Vérification des bons de sortie créés
- [ ] **Action** : Aller sur `/stocks/outgoings` et vérifier les bons créés
- [ ] **Résultat attendu** : 
  - Autant de bons de sortie que de clients dans la commande
  - Chaque bon référence la commande originale
  - Articles et quantités corrects
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 3.5 : Test avec stock insuffisant
- [ ] **Action** : 
  - Créer une commande avec quantités supérieures au stock disponible
  - Valider la commande
  - Essayer de générer les bons de sortie
- [ ] **Résultat attendu** : 
  - Message d'erreur : "Stock insuffisant pour [article]"
  - Aucun bon de sortie créé
  - Stock non modifié
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🧪 TESTS - ISOLATION DES SESSIONS

### Test 4.1 : Commercial voit uniquement ses commandes
- [ ] **Action** : 
  - Se connecter en tant que Commercial A
  - Créer une commande
  - Se déconnecter
  - Se connecter en tant que Commercial B
  - Aller sur `/orders`
- [ ] **Résultat attendu** : Commercial B ne voit PAS la commande de Commercial A
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 4.2 : Tentative d'accès non autorisé
- [ ] **Action** : 
  - Commercial B essaie d'accéder directement à `/orders/<id>` d'une commande de Commercial A
- [ ] **Résultat attendu** : 
  - Message d'erreur : "Vous n'avez pas accès à cette commande"
  - Redirection vers la liste
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🧪 TESTS - COMMENTAIRES ET PAIEMENTS

### Test 5.1 : Saisie de commentaires pour un client
- [ ] **Action** : 
  - Créer une commande
  - Pour Client 1, remplir :
    - Commentaires : "Échéance de paiement : 30 jours. Client fiable."
    - Notes : "Livraison urgente demandée"
- [ ] **Résultat attendu** : Commentaires et notes sauvegardés et affichés
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 5.2 : Affichage du type de paiement
- [ ] **Action** : Vérifier l'affichage dans la page de détail
- [ ] **Résultat attendu** : 
  - Badge "Comptant" (vert) ou "Crédit" (orange) affiché
  - Échéance affichée si crédit
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 5.3 : Champ échéance conditionnel
- [ ] **Action** : 
  - Sélectionner "Comptant" → Vérifier que le champ échéance disparaît
  - Sélectionner "Crédit" → Vérifier que le champ échéance apparaît et devient obligatoire
- [ ] **Résultat attendu** : Comportement correct selon le type de paiement
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🧪 TESTS - FILTRES ET RECHERCHE

### Test 6.1 : Filtre par statut
- [ ] **Action** : Filtrer par "En attente", "Validée", "Rejetée", "Complétée"
- [ ] **Résultat attendu** : Liste filtrée correctement
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 6.2 : Recherche par référence
- [ ] **Action** : Rechercher une référence de commande
- [ ] **Résultat attendu** : Commande trouvée et affichée
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

### Test 6.3 : Filtre par commercial (hiérarchie)
- [ ] **Action** : Filtrer par un commercial spécifique
- [ ] **Résultat attendu** : Seules les commandes de ce commercial affichées
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🧪 TESTS - PAGINATION

### Test 7.1 : Pagination avec plusieurs commandes
- [ ] **Action** : Créer plus de 20 commandes → Vérifier la pagination
- [ ] **Résultat attendu** : Pagination fonctionnelle avec navigation
- [ ] **Résultat obtenu** : ☐ OK ☐ KO
- [ ] **Commentaires** : 

---

## 🐛 BUGS DÉCOUVERTS

| # | Description | Gravité | Statut | Commentaires |
|---|-------------|---------|--------|--------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## ✅ VALIDATION FINALE

- [ ] Tous les tests passent
- [ ] Aucun bug critique
- [ ] Performance acceptable
- [ ] Interface utilisateur intuitive
- [ ] Documentation à jour

---

## 📝 NOTES ET OBSERVATIONS

### Points positifs :
- 

### Points à améliorer :
- 

### Suggestions :
- 

---

## ✍️ SIGNATURES

- **Testeur Commercial** : _______________ Date : _______
- **Testeur Hiérarchie** : _______________ Date : _______
- **Testeur Magasinier** : _______________ Date : _______
- **Responsable Validation** : _______________ Date : _______

