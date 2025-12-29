# Guide d'Exécution des Tests - Système de Commandes Commerciales

Ce guide détaille étape par étape comment exécuter chaque test du plan de test en live.

## Préparation de l'environnement

### 1. Vérifier les prérequis

```bash
# 1. Vérifier que la base de données est à jour
mysql -u root -p madargn < scripts/create_commercial_orders_tables.sql
mysql -u root -p madargn < scripts/add_payment_fields_to_orders.sql

# 2. Vérifier que l'application démarre sans erreur
python3 app.py

# 3. Vérifier les utilisateurs de test
# - Au moins 1 commercial (role: commercial)
# - Au moins 1 superviseur/admin (role: supervisor ou admin)
# - Au moins 1 magasinier (role: warehouse)
```

### 2. Données de test nécessaires

- **Articles** : Au moins 5 articles actifs dans le système
- **Dépôt** : Au moins 1 dépôt avec stock disponible pour les articles
- **Utilisateurs** :
  - Commercial A (ex: username: `commercial1`)
  - Commercial B (ex: username: `commercial2`)
  - Superviseur (ex: username: `supervisor1`)
  - Magasinier (ex: username: `warehouse1`)

---

## Phase 1 : Tests de Création de Commande

### Test 1.1 : Création avec client au comptant

**Objectif** : Vérifier qu'un commercial peut créer une commande avec un client au comptant et des commentaires.

**Étapes détaillées** :

1. **Se connecter en tant que commercial**
   - URL : `http://localhost:5002/auth/login`
   - Username : `commercial1`
   - Password : (mot de passe du commercial)

2. **Accéder à la création de commande**
   - Cliquer sur "Nouvelle Commande" ou aller sur `/orders/new`
   - Vérifier que le formulaire s'affiche correctement

3. **Ajouter un client**
   - Cliquer sur le bouton "Ajouter Client"
   - Remplir les champs :
     - **Nom** : `Amadou Diallo`
     - **Téléphone** : `612345678`
     - **Adresse** : `Conakry, Hamdallaye`
     - **Type de paiement** : Sélectionner `Comptant`
     - **Commentaires** : `Paiement immédiat, client fidèle`
     - **Notes** : `Livraison urgente demandée`
   - Vérifier que le champ "Échéance" n'est PAS visible (car comptant)

4. **Ajouter des articles**
   - Dans le champ de recherche, taper "Riz" ou le nom d'un article
   - Cliquer sur l'article dans les résultats
   - Dans la colonne "Client 1", remplir :
     - Quantité : `10`
     - Prix unitaire : `5000`
   - Répéter pour un deuxième article (ex: "Javel")
     - Quantité : `5`
     - Prix unitaire : `3000`

5. **Enregistrer la commande**
   - Cliquer sur "Enregistrer et Soumettre à Validation"
   - Vérifier le message de succès

6. **Vérifier les résultats**
   - Redirection vers la page de détail de la commande
   - Vérifier que :
     - Statut = "En attente de validation"
     - Badge "Comptant" (vert) est affiché
     - Commentaires sont visibles dans la section dédiée
     - Notes sont affichées
     - Articles et quantités sont corrects

**Résultat attendu** : ✅ Commande créée avec toutes les informations sauvegardées

---

### Test 1.2 : Création avec client en crédit

**Objectif** : Vérifier qu'un commercial peut créer une commande avec un client en crédit, une échéance et des commentaires.

**Étapes détaillées** :

1. **Créer une nouvelle commande** (`/orders/new`)

2. **Ajouter un client en crédit**
   - Cliquer sur "Ajouter Client"
   - Remplir :
     - **Nom** : `Mamadou Camara`
     - **Téléphone** : `622345678`
     - **Type de paiement** : Sélectionner `Crédit`
   - **Vérifier immédiatement** : Le champ "Échéance" doit apparaître et être obligatoire
   - Remplir :
     - **Échéance** : Date dans 30 jours (ex: `2024-02-15`)
     - **Commentaires** : `Échéance de paiement : 30 jours. Client fiable. Conditions : Paiement en 2 fois accepté.`
     - **Notes** : `Vérifier solvabilité avant livraison`

3. **Ajouter des articles**
   - Ajouter au moins 2 articles différents avec quantités et prix

4. **Enregistrer et vérifier**
   - Enregistrer la commande
   - Vérifier dans les détails :
     - Badge "Crédit" (orange) affiché
     - Échéance affichée avec icône calendrier
     - Commentaires avec mention de l'échéance visibles

**Résultat attendu** : ✅ Commande avec crédit et échéance correctement sauvegardée

---

### Test 1.3 : Commande multi-clients avec types de paiement mixtes

**Objectif** : Vérifier qu'une commande peut contenir plusieurs clients avec des types de paiement différents.

**Étapes détaillées** :

1. **Créer une nouvelle commande**

2. **Ajouter Client 1 (Comptant)**
   - Nom : `Fatou Bah`
   - Type : `Comptant`
   - Commentaires : `Paiement comptant, remise de 5% appliquée`
   - Articles : Riz (10), Javel (5)

3. **Ajouter Client 2 (Crédit)**
   - Nom : `Ibrahima Diallo`
   - Type : `Crédit`
   - Échéance : Date dans 45 jours
   - Commentaires : `Crédit 45 jours. Garantie demandée.`
   - Articles : Riz (20), Sucre (15)

4. **Ajouter Client 3 (Comptant)**
   - Nom : `Aissatou Camara`
   - Type : `Comptant`
   - Commentaires : `Paiement immédiat`
   - Notes : `Client nouveau, vérifier identité`
   - Articles : Javel (10), Sucre (8)

5. **Vérifier le tableau paysage**
   - Tous les clients doivent être visibles horizontalement
   - Chaque colonne client doit contenir ses propres champs de saisie
   - Les articles doivent pouvoir être ajoutés pour chaque client

6. **Enregistrer et vérifier**
   - Enregistrer la commande
   - Vérifier que tous les clients sont sauvegardés
   - Vérifier que chaque client a son type de paiement correct
   - Vérifier que les commentaires sont distincts par client

**Résultat attendu** : ✅ Commande multi-clients avec types de paiement mixtes correctement sauvegardée

---

## Phase 2 : Tests de Validation Hiérarchique

### Test 2.1 : Validation d'une commande avec commentaires

**Prérequis** : Avoir créé au moins une commande en attente (Test 1.1, 1.2 ou 1.3)

**Étapes détaillées** :

1. **Se connecter en tant que superviseur/admin**
   - URL : `http://localhost:5002/auth/login`
   - Username : `supervisor1`

2. **Accéder à la liste des commandes**
   - Aller sur `/orders`
   - **Vérifier** : Toutes les commandes sont visibles (pas seulement celles du superviseur)

3. **Ouvrir une commande en attente**
   - Cliquer sur une commande avec statut "En attente"
   - Vérifier l'affichage complet :
     - Informations du commercial
     - Tous les clients avec leurs articles
     - **Commentaires par client** (section mise en évidence)
     - **Types de paiement** (badges Comptant/Crédit)
     - **Échéances** si crédit (avec icône calendrier)

4. **Valider la commande**
   - Cliquer sur "Valider la Commande"
   - Vérifier le message de succès
   - Vérifier que :
     - Statut passe à "Validée"
     - Validateur et date de validation affichés
     - Toutes les informations (commentaires, paiements) sont préservées

**Résultat attendu** : ✅ Commande validée avec toutes les informations préservées

---

### Test 2.2 : Rejet avec raison

**Étapes détaillées** :

1. **Créer une commande de test** (en tant que commercial)
   - Créer une commande simple avec 1 client

2. **Se connecter en tant que superviseur**

3. **Rejeter la commande**
   - Ouvrir la commande en attente
   - Dans le champ "Raison du rejet", saisir : `Stock insuffisant pour certains articles`
   - Cliquer sur "Rejeter"

4. **Vérifier les résultats**
   - Statut passe à "Rejetée"
   - Raison du rejet affichée dans une section mise en évidence
   - Badge "Rejetée" (rouge) affiché

5. **Vérifier que le commercial peut voir la raison**
   - Se reconnecter en tant que commercial
   - Ouvrir la commande rejetée
   - Vérifier que la raison du rejet est visible

**Résultat attendu** : ✅ Commande rejetée avec raison visible par tous

---

## Phase 3 : Tests de Génération de Bons de Sortie

### Test 3.1 : Génération depuis commande validée

**Prérequis** : Avoir une commande validée avec plusieurs clients (après Test 2.1)

**Étapes détaillées** :

1. **Se connecter en tant que magasinier**
   - Username : `warehouse1`

2. **Accéder aux commandes validées**
   - Aller sur `/orders`
   - Filtrer par statut : "Validée"
   - Vérifier que les commandes validées s'affichent

3. **Ouvrir une commande validée**
   - Cliquer sur une commande validée
   - Vérifier l'affichage :
     - Section "Générer les Bons de Sortie" visible
     - Commentaires et informations de paiement affichés
     - Liste des clients et articles

4. **Vérifier le stock disponible**
   - Noter les quantités nécessaires pour chaque article
   - Vérifier que le dépôt sélectionné a suffisamment de stock

5. **Générer les bons de sortie**
   - Sélectionner un dépôt source (avec stock suffisant)
   - Cliquer sur "Générer les Bons de Sortie pour tous les Clients"
   - Vérifier le message de succès

6. **Vérifier les résultats**
   - Message : "X bon(s) de sortie créé(s) avec succès"
   - Commande passe au statut "Complétée"
   - Stock du dépôt décrémenté

**Résultat attendu** : ✅ Bons de sortie générés (un par client) avec stock décrémenté

---

### Test 3.2 : Vérification des bons créés

**Étapes détaillées** :

1. **Accéder à la liste des sorties**
   - Aller sur `/stocks/outgoings`
   - Filtrer par date du jour si nécessaire

2. **Vérifier les bons créés**
   - Compter le nombre de bons créés
   - **Vérifier** : Nombre de bons = nombre de clients dans la commande

3. **Ouvrir chaque bon de sortie**
   - Vérifier que chaque bon contient :
     - Les articles du client correspondant
     - Les quantités correctes
     - Le nom du client
     - La référence de la commande originale (dans les notes)

4. **Vérifier les informations de paiement**
   - Vérifier que les informations de paiement sont préservées
   - Vérifier que les commentaires sont accessibles

**Résultat attendu** : ✅ Tous les bons créés correctement avec informations complètes

---

### Test 3.3 : Test avec stock insuffisant

**Objectif** : Vérifier que le système empêche la génération si le stock est insuffisant.

**Étapes détaillées** :

1. **Créer une commande avec quantités importantes**
   - Créer une commande avec des quantités supérieures au stock disponible
   - Valider la commande

2. **Essayer de générer les bons**
   - Se connecter en tant que magasinier
   - Ouvrir la commande validée
   - Sélectionner un dépôt avec stock insuffisant
   - Cliquer sur "Générer les Bons de Sortie"

3. **Vérifier le comportement**
   - Message d'erreur : "Stock insuffisant pour [article] (client: [nom])"
   - Aucun bon de sortie créé
   - Stock non modifié
   - Commande reste au statut "Validée"

**Résultat attendu** : ✅ Erreur affichée, aucun bon créé, stock préservé

---

## Phase 4 : Tests d'Affichage et de Consultation

### Test 4.1 : Affichage des commentaires dans les détails

**Étapes détaillées** :

1. **Ouvrir une commande avec commentaires**
   - Se connecter (n'importe quel rôle)
   - Ouvrir une commande qui contient des commentaires

2. **Vérifier l'affichage des commentaires**
   - Section "Commentaires" :
     - Fond bleu clair (rgba(0, 56, 101, 0.05))
     - Bordure gauche bleue (3px)
     - Icône commentaire
     - Texte formaté correctement (retours à la ligne préservés)

3. **Vérifier l'affichage des notes**
   - Section "Notes" :
     - Fond gris clair
     - Icône note
     - Texte formaté

4. **Vérifier les badges de paiement**
   - Badge "Comptant" : Vert (#10b981)
   - Badge "Crédit" : Orange (#f59e0b)
   - Icônes appropriées (money-bill-wave / credit-card)

5. **Vérifier l'affichage de l'échéance**
   - Si crédit : Échéance affichée avec icône calendrier
   - Format : "Échéance: DD/MM/YYYY"

**Résultat attendu** : ✅ Tous les éléments affichés correctement et de manière lisible

---

### Test 4.2 : Filtrage et recherche

**Étapes détaillées** :

1. **Tester le filtre par statut**
   - Aller sur `/orders`
   - Sélectionner "En attente" → Vérifier que seules les commandes en attente s'affichent
   - Sélectionner "Validée" → Vérifier que seules les commandes validées s'affichent
   - Répéter pour tous les statuts

2. **Tester la recherche par référence**
   - Saisir une référence de commande dans le champ recherche
   - Vérifier que la commande correspondante s'affiche

3. **Tester le filtre par commercial** (hiérarchie uniquement)
   - Se connecter en tant que superviseur
   - Sélectionner un commercial dans le filtre
   - Vérifier que seules les commandes de ce commercial s'affichent

4. **Tester la combinaison de filtres**
   - Combiner statut + recherche
   - Vérifier que les résultats sont corrects

**Résultat attendu** : ✅ Tous les filtres fonctionnent correctement

---

## Phase 5 : Tests d'Isolation des Sessions

### Test 5.1 : Commercial voit uniquement ses commandes

**Étapes détaillées** :

1. **Commercial A crée une commande**
   - Se connecter en tant que `commercial1`
   - Créer une commande avec au moins 1 client
   - Noter la référence de la commande

2. **Commercial B se connecte**
   - Se déconnecter
   - Se connecter en tant que `commercial2`
   - Aller sur `/orders`

3. **Vérifier l'isolation**
   - **Vérifier** : La commande de Commercial A n'apparaît PAS dans la liste
   - **Vérifier** : Titre affiché = "Mes Commandes" (pas "Commandes Commerciales")
   - **Vérifier** : Message informatif "Vous voyez uniquement vos commandes dans cette session"

4. **Commercial B crée sa propre commande**
   - Créer une commande
   - Vérifier qu'elle apparaît dans sa liste

**Résultat attendu** : ✅ Isolation complète des sessions commerciales

---

### Test 5.2 : Tentative d'accès non autorisé

**Étapes détaillées** :

1. **Commercial A crée une commande**
   - Noter l'ID de la commande (ex: `/orders/5`)

2. **Commercial B essaie d'y accéder**
   - Se connecter en tant que `commercial2`
   - Essayer d'accéder directement à `/orders/5` (remplacer 5 par l'ID réel)

3. **Vérifier la protection**
   - Message d'erreur : "Vous n'avez pas accès à cette commande. Vous ne pouvez voir que vos propres commandes dans votre session."
   - Redirection vers `/orders`
   - Aucune information sur la commande n'est révélée

**Résultat attendu** : ✅ Accès non autorisé bloqué avec message clair

---

## Checklist de Validation Finale

### Fonctionnalités critiques
- [ ] Création commande multi-clients fonctionne
- [ ] Types de paiement (Comptant/Crédit) sauvegardés et affichés
- [ ] Champ échéance conditionnel (visible uniquement si crédit)
- [ ] Commentaires sauvegardés par client et affichés correctement
- [ ] Validation hiérarchique fonctionne
- [ ] Génération bons de sortie crée un bon par client
- [ ] Isolation des sessions commerciales respectée

### Affichage et UX
- [ ] Badges paiement visibles et colorés correctement
- [ ] Échéances affichées si crédit avec format correct
- [ ] Commentaires mis en évidence visuellement
- [ ] Tableau paysage lisible avec plusieurs clients (5-10)
- [ ] Formulaire responsive sur mobile/tablette

### Intégrité des données
- [ ] Toutes les données sauvegardées en base de données
- [ ] Relations entre tables correctes (order → clients → items)
- [ ] Stock décrémenté après génération bons
- [ ] Historique complet traçable (qui a créé, validé, généré)

### Performance
- [ ] Temps de chargement acceptable (< 2 secondes)
- [ ] Pagination fonctionne avec beaucoup de commandes
- [ ] Recherche rapide même avec beaucoup de données

---

## Rapport de Test

Après avoir exécuté tous les tests, remplir ce rapport :

**Date de test** : _______________

**Testeur(s)** :
- Commercial : _______________
- Hiérarchie : _______________
- Magasinier : _______________

**Résultats globaux** :
- Tests réussis : ___ / ___
- Tests échoués : ___ / ___
- Bugs critiques : ___
- Bugs mineurs : ___

**Bugs découverts** :

| # | Description | Gravité | Statut | Commentaires |
|---|-------------|---------|--------|--------------|
| 1 | | | | |
| 2 | | | | |

**Points positifs** :


**Points à améliorer** :


**Recommandations** :


**Validation finale** : ☐ Approuvé ☐ À revoir

**Signature** : _______________ Date : _______

