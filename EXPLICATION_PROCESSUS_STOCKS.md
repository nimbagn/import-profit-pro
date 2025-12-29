# 📦 Explication du Processus de Gestion des Stocks

## Vue d'ensemble

Le système de gestion des stocks gère le suivi des articles dans différents emplacements (dépôts et véhicules) à travers 4 processus principaux :

1. **Mouvements** : Transferts et ajustements de stock
2. **Réceptions** : Entrées de marchandises depuis des fournisseurs
3. **Sorties** : Ventes ou distributions aux clients
4. **Retours** : Retour de marchandises des clients

---

## 🔄 1. MOUVEMENTS DE STOCK

### Définition
Les mouvements représentent **tous les changements de quantité** d'un article dans le système, qu'ils soient positifs (entrées) ou négatifs (sorties).

### Types de mouvements

#### A. Transfert (`transfer`)
**Objectif** : Déplacer des articles entre emplacements

⚠️ **IMPORTANT** : Les transferts sont des **déplacements** de stock, ils **N'AUGMENTENT JAMAIS** le stock global. Le stock est simplement déplacé d'un emplacement à un autre.

**Exemples** :
- Transfert d'un dépôt vers un autre dépôt
- Transfert d'un dépôt vers un véhicule
- Transfert d'un véhicule vers un dépôt
- Transfert d'un véhicule vers un autre véhicule

**Processus** :
1. **Source** (from_depot_id ou from_vehicle_id) : L'emplacement qui perd le stock
   - La quantité est **déduite** du stock source (négative)
   - Stock source : `quantity -= X`
2. **Destination** (to_depot_id ou to_vehicle_id) : L'emplacement qui reçoit le stock
   - La quantité est **ajoutée** au stock destination (positive)
   - Stock destination : `quantity += X`

**Impact sur le stock global** :
```
Stock global AVANT transfert : 100 unités (Dépôt A: 100)
Stock global APRÈS transfert : 100 unités (Dépôt A: 50, Dépôt B: 50)
→ Le stock global reste identique : -50 + 50 = 0 (pas de changement)
```

**Exemple concret** :
```
Transfert de 50 unités de "Riz" :
- Depuis : Dépôt Central (quantité -50)
- Vers : Véhicule V-001 (quantité +50)
- Stock global : Inchangé (50 - 50 + 50 = 50)
```

**Implémentation technique** :
Le système crée **deux mouvements** pour chaque transfert :
- **Mouvement SORTIE** : quantité **NÉGATIVE** depuis la source
- **Mouvement ENTRÉE** : quantité **POSITIVE** vers la destination

Ces deux mouvements s'annulent au niveau du stock global, garantissant qu'aucun stock n'est créé ou détruit lors d'un transfert.

#### B. Réception (`reception`)
**Objectif** : Enregistrer l'arrivée de marchandises depuis un fournisseur

**Processus** :
1. Les articles arrivent d'un **fournisseur externe**
2. Ils sont stockés dans un **dépôt** (to_depot_id)
3. La quantité est **ajoutée** au stock du dépôt (positive)
4. Informations enregistrées :
   - Nom du fournisseur
   - Numéro de BL (Bon de Livraison)
   - Date de réception
   - Quantités et prix unitaires

**Exemple concret** :
```
Réception de 200 unités de "Riz" :
- Fournisseur : Import Company
- BL : BL-2024-001
- Dépôt : Dépôt Central
- Stock du dépôt : +200 unités
```

#### C. Ajustement (`adjustment`)
**Objectif** : Corriger les écarts d'inventaire ou les erreurs de comptage

**Processus** :
1. Permet d'ajuster manuellement les quantités
2. Peut être **positif** (ajout) ou **négatif** (soustrait)
3. Utilisé pour :
   - Corriger les erreurs de saisie
   - Ajuster après inventaire
   - Gérer les pertes/casses

**Exemple concret** :
```
Ajustement de -5 unités de "Riz" :
- Raison : "Casse lors du transport"
- Stock du dépôt : -5 unités
```

#### D. Inventaire (`inventory`)
**Objectif** : Enregistrer les résultats d'un inventaire physique

**Processus** :
1. Comptage physique des articles
2. Comparaison avec le stock système
3. Génération d'un mouvement pour ajuster la différence

**Exemple concret** :
```
Inventaire : Stock système = 100, Stock physique = 95
- Mouvement : -5 unités (ajustement)
```

---

## 📥 2. RÉCEPTIONS

### Définition
Les réceptions sont des **documents d'entrée** qui enregistrent l'arrivée de marchandises depuis des fournisseurs.

### Processus complet

#### Étape 1 : Création de la réception
1. Créer une nouvelle réception avec :
   - **Dépôt** de destination
   - **Fournisseur** (nom)
   - **Numéro de BL** (Bon de Livraison)
   - **Date de réception**
   - **Notes** (optionnel)

#### Étape 2 : Ajout des articles
Pour chaque article reçu :
- Sélectionner l'**article** (SKU)
- Indiquer la **quantité** reçue
- Indiquer le **prix unitaire** (GNF)
- Le système calcule automatiquement le **montant total**

#### Étape 3 : Validation
1. La réception passe au statut `completed`
2. **Mouvements de stock automatiques** :
   - Création d'un mouvement de type `reception`
   - Ajout de la quantité au stock du dépôt
   - Enregistrement du fournisseur et du BL

#### Exemple complet
```
Réception REC-20240115-001 :
├── Dépôt : Dépôt Central
├── Fournisseur : Import Company
├── BL : BL-2024-001
├── Date : 15/01/2024
└── Articles :
    ├── Riz (SKU: RIZ-001) : 200 unités × 5000 GNF = 1,000,000 GNF
    └── Sucre (SKU: SUC-001) : 100 unités × 3000 GNF = 300,000 GNF

Résultat :
- Stock Dépôt Central : Riz +200, Sucre +100
- Mouvement créé automatiquement
```

---

## 📤 3. SORTIES

### Définition
Les sorties sont des **documents de sortie** qui enregistrent la vente ou la distribution d'articles aux clients.

### Processus complet

#### Étape 1 : Création de la sortie
1. Créer une nouvelle sortie avec :
   - **Client** (nom et téléphone)
   - **Source** : Dépôt OU Véhicule
   - **Commercial** (optionnel)
   - **Date de sortie**
   - **Notes** (optionnel)

#### Étape 2 : Ajout des articles
Pour chaque article vendu :
- Sélectionner l'**article** (SKU)
- Indiquer la **quantité** vendue
- Indiquer le **prix unitaire** de vente (GNF)
- Le système calcule automatiquement le **montant total**

#### Étape 3 : Validation
1. **Vérification du stock disponible** :
   - Le système vérifie que le stock est suffisant
   - Si stock insuffisant → Erreur, sortie non créée

2. La sortie passe au statut `completed`

3. **Mouvements de stock automatiques** :
   - Création d'un mouvement de type `transfer`
   - **Soustraction** de la quantité du stock source (négatif)
   - Enregistrement du client et de la raison

#### Exemple complet
```
Sortie OUT-20240115-001 :
├── Client : Mamadou Diallo (+224 612 34 56 78)
├── Source : Véhicule V-001
├── Commercial : Amadou Bah
├── Date : 15/01/2024
└── Articles :
    ├── Riz (SKU: RIZ-001) : 10 unités × 6000 GNF = 60,000 GNF
    └── Sucre (SKU: SUC-001) : 5 unités × 3500 GNF = 17,500 GNF

Vérification :
- Stock Véhicule V-001 : Riz = 50 unités ✅ (suffisant)
- Stock Véhicule V-001 : Sucre = 20 unités ✅ (suffisant)

Résultat :
- Stock Véhicule V-001 : Riz -10, Sucre -5
- Mouvement créé automatiquement (quantité négative)
- Montant total : 77,500 GNF
```

---

## 🔙 4. RETOURS

### Définition
Les retours sont des **documents de retour** qui enregistrent le retour de marchandises par les clients.

### Processus complet

#### Étape 1 : Création du retour
1. Créer un nouveau retour avec :
   - **Client** (nom et téléphone)
   - **Destination** : Dépôt OU Véhicule (où remettre le stock)
   - **Commercial** (optionnel)
   - **Raison du retour** (obligatoire)
   - **Date de retour**
   - **Notes** (optionnel)

#### Étape 2 : Ajout des articles retournés
Pour chaque article retourné :
- Sélectionner l'**article** (SKU)
- Indiquer la **quantité** retournée
- Le système vérifie la qualité (articles endommagés peuvent être gérés différemment)

#### Étape 3 : Validation
1. Le retour passe au statut `completed`

2. **Mouvements de stock automatiques** :
   - Création d'un mouvement de type `transfer`
   - **Ajout** de la quantité au stock de destination (positif)
   - Enregistrement du client et de la raison

#### Exemple complet
```
Retour RET-20240115-001 :
├── Client : Mamadou Diallo (+224 612 34 56 78)
├── Destination : Dépôt Central
├── Commercial : Amadou Bah
├── Raison : "Article défectueux"
├── Date : 15/01/2024
└── Articles :
    └── Riz (SKU: RIZ-001) : 2 unités retournées

Résultat :
- Stock Dépôt Central : Riz +2
- Mouvement créé automatiquement (quantité positive)
- Raison enregistrée pour traçabilité
```

---

## 🔗 Relations entre les processus

### Flux complet typique

```
1. RÉCEPTION (Augmente le stock global)
   └── Fournisseur → Dépôt Central
       Stock global : +200 unités
       Dépôt Central : +200

2. MOUVEMENT (Transfert - N'impacte PAS le stock global)
   └── Dépôt Central → Véhicule V-001
       Stock global : 0 (inchangé)
       Dépôt Central : -50
       Véhicule V-001 : +50
       → Total : -50 + 50 = 0 ✅

3. SORTIE (Diminue le stock global)
   └── Véhicule V-001 → Client
       Stock global : -10 unités
       Véhicule V-001 : -10

4. RETOUR (Augmente le stock global)
   └── Client → Dépôt Central
       Stock global : +2 unités
       Dépôt Central : +2
```

### Règles importantes sur le stock global

| Type d'opération | Impact sur stock global | Explication |
|------------------|------------------------|-------------|
| **Réception** | ✅ **+X** (augmente) | Stock entre dans le système depuis un fournisseur externe |
| **Transfert** | ⚠️ **0** (inchangé) | Stock déplacé entre emplacements internes |
| **Sortie** | ✅ **-X** (diminue) | Stock sort du système vers un client |
| **Retour** | ✅ **+X** (augmente) | Stock revient dans le système depuis un client |
| **Ajustement** | ✅ **±X** (peut augmenter ou diminuer) | Correction manuelle du stock |
| **Inventaire** | ✅ **±X** (peut augmenter ou diminuer) | Ajustement après comptage physique |

### Traçabilité

Chaque opération crée un **mouvement de stock** qui permet de :
- ✅ Suivre l'historique complet d'un article
- ✅ Connaître l'origine et la destination
- ✅ Identifier les responsables (utilisateurs)
- ✅ Vérifier les quantités à tout moment

---

## 📊 États et statuts

### Statuts des documents

#### Réceptions, Sorties, Retours
- **`draft`** : Brouillon (non validé, pas d'impact sur le stock)
- **`completed`** : Complété (validé, impact sur le stock enregistré)
- **`cancelled`** : Annulé (si applicable)

### Important
⚠️ **Seuls les documents au statut `completed` impactent le stock réel.**

---

## 💡 Bonnes pratiques

### 1. Ordre des opérations
- Toujours créer une **réception** avant de faire des sorties
- Vérifier le stock disponible avant une sortie
- Enregistrer les retours rapidement pour maintenir la traçabilité

### 2. Traçabilité
- Toujours remplir les champs obligatoires (fournisseur, BL, client, raison)
- Ajouter des notes pour clarifier les situations particulières
- Utiliser les ajustements avec précaution (documenter la raison)

### 3. Gestion des erreurs
- Si erreur de saisie : utiliser un **ajustement** pour corriger
- Si problème de qualité : enregistrer un **retour** avec la raison
- Toujours vérifier le stock avant validation

---

## 🎯 Résumé visuel

```
┌─────────────────────────────────────────────────────────────┐
│                    GESTION DES STOCKS                        │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  FOURNISSEUR │
    └──────┬───────┘
           │
           │ RÉCEPTION
           ▼
    ┌──────────────┐
    │   DÉPÔT      │◄──┐
    └──────┬───────┘   │
           │           │ MOUVEMENT
           │           │ (Transfert)
           │ SORTIE    │
           ▼           │
    ┌──────────────┐  │
    │   VÉHICULE   │──┘
    └──────┬───────┘
           │
           │ SORTIE
           ▼
    ┌──────────────┐
    │    CLIENT    │
    └──────┬───────┘
           │
           │ RETOUR
           ▼
    ┌──────────────┐
    │   DÉPÔT      │
    └──────────────┘

Tous ces processus créent des MOUVEMENTS pour la traçabilité.
```

---

## 📝 Notes techniques

### Stock réel vs Stock système
- Le **stock système** est calculé à partir de tous les mouvements
- Le **stock réel** est le stock physique compté
- Les **ajustements** permettent de synchroniser les deux

### Calcul du stock actuel

#### Pour un emplacement spécifique (dépôt ou véhicule)
```
Stock emplacement = Stock initial
                  + Toutes les réceptions vers cet emplacement
                  + Tous les retours vers cet emplacement
                  + Tous les transferts entrants (vers cet emplacement)
                  - Toutes les sorties depuis cet emplacement
                  - Tous les transferts sortants (depuis cet emplacement)
                  ± Tous les ajustements sur cet emplacement
```

#### Pour le stock global (tous emplacements confondus)
```
Stock global = Stock initial
             + Toutes les réceptions (tous emplacements)
             + Tous les retours (tous emplacements)
             - Toutes les sorties (tous emplacements)
             ± Tous les ajustements (tous emplacements)
             
⚠️ IMPORTANT : Les transferts ne sont PAS inclus dans le calcul du stock global
car ils se compensent (entrée + sortie = 0).
```

**Exemple de calcul** :
```
Stock initial global : 1000 unités

Réceptions : +500 unités
Sorties : -200 unités
Retours : +50 unités
Transferts : Dépôt A → Dépôt B (100 unités)
            → Impact global : 0 (car -100 + 100 = 0)
Ajustements : -10 unités

Stock global final = 1000 + 500 - 200 + 50 + 0 - 10 = 1340 unités
```

---

## ❓ Questions fréquentes

**Q : Que se passe-t-il si je crée une sortie avec un stock insuffisant ?**
R : Le système bloque la création et affiche une erreur. Vous devez d'abord approvisionner le stock.

**Q : Puis-je annuler une réception déjà validée ?**
R : Oui, en créant un ajustement négatif ou une sortie pour corriger.

**Q : Les mouvements sont-ils automatiques ?**
R : Oui, dès qu'une réception, sortie ou retour est validée (`completed`), les mouvements sont créés automatiquement.

**Q : Comment suivre l'historique d'un article ?**
R : Consultez la liste des mouvements filtrée par article pour voir tout l'historique.

**Q : Les transferts augmentent-ils le stock global ?**
R : **NON**. Les transferts sont des déplacements entre emplacements internes. Ils créent deux mouvements (un négatif à la source, un positif à la destination) qui s'annulent au niveau du stock global. Le stock global ne change jamais lors d'un transfert.

**Q : Comment calculer le stock global réel ?**
R : Additionnez toutes les réceptions et retours, soustrayez toutes les sorties, et ajoutez/soustrayez les ajustements. **N'incluez pas les transferts** car ils se compensent automatiquement.

---

## 🔍 Pour aller plus loin

- Consultez la documentation des modèles dans `models.py`
- Explorez les routes dans `stocks.py` pour comprendre l'implémentation
- Utilisez les exports Excel pour analyser les données

