# 🏗️ Architecture de la Prise de Commandes Commerciales

## 📋 Vue d'ensemble

Le système de commandes commerciales permet à un commercial de créer **UNE SEULE commande** qui contient **PLUSIEURS CLIENTS**, et chaque client peut commander **PLUSIEURS ARTICLES** avec des quantités différentes.

---

## 🎯 Architecture du Tableau (Vue Paysage)

### Structure visuelle :

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMMANDE COMMERCIALE                                │
├──────────────┬──────────────┬──────────────┬──────────────┬───────────────┤
│   ARTICLES   │   CLIENT 1   │   CLIENT 2   │   CLIENT 3   │   CLIENT 10   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Nom / SKU    │ [Infos]      │ [Infos]      │ [Infos]      │ [Infos]       │
│              │ Nom, Tél...  │ Nom, Tél...  │ Nom, Tél...  │ Nom, Tél...   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Article A    │ [Qté: 10]    │ [Qté: 5]     │ [Qté: 20]    │ [Qté: 0]      │
│              │ Prix: 170000 │ Prix: 170000 │ Prix: 165000 │               │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Article B    │ [Qté: 0]     │ [Qté: 15]    │ [Qté: 8]     │ [Qté: 12]     │
│              │              │ Prix: 200000 │ Prix: 200000 │ Prix: 195000   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Article C    │ [Qté: 30]    │ [Qté: 0]     │ [Qté: 0]     │ [Qté: 25]     │
│              │ Prix: 50000  │              │              │ Prix: 50000    │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ ...          │ ...          │ ...          │ ...          │ ...           │
│ Article J    │ [Qté: 5]     │ [Qté: 10]    │ [Qté: 15]    │ [Qté: 20]      │
│              │ Prix: 300000 │ Prix: 300000 │ Prix: 295000 │ Prix: 300000   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│              │ Total Client │ Total Client │ Total Client │ Total Client   │
│              │ 1: 1,700,000 │ 2: 3,000,000 │ 3: 3,300,000 │ 10: 5,900,000  │
└──────────────┴──────────────┴──────────────┴──────────────┴───────────────┘
```

---

## 🔄 Workflow Complet : 10 Clients × 10 Articles

### Étape 1 : Ajouter les Clients

1. Cliquer sur **"Ajouter un Client"** → Une colonne est créée
2. Répéter 10 fois → 10 colonnes de clients
3. Remplir les informations de chaque client :
   - Nom du client (obligatoire)
   - Téléphone
   - Adresse
   - Type de paiement (Comptant/Crédit)
   - Commentaires

### Étape 2 : Ajouter les Articles

1. Utiliser la barre de recherche pour trouver un article
2. Cliquer sur l'article → Une **ligne** est ajoutée au tableau
3. Répéter 10 fois → 10 lignes d'articles

### Étape 3 : Remplir les Quantités

Pour chaque intersection **Article × Client** :
- Si le client commande cet article → Entrer la quantité
- Si le client ne commande pas cet article → Laisser vide ou 0

**Exemple concret :**
- **Client 1** commande : Article A (10), Article C (30), Article J (5)
- **Client 2** commande : Article A (5), Article B (15), Article J (10)
- **Client 3** commande : Article A (20), Article B (8), Article J (15)
- ...
- **Client 10** commande : Article B (12), Article C (25), Article J (20)

---

## 💾 Structure des Données en Base

### Modèle de données :

```
CommercialOrder (1 commande)
├── ID: 1
├── Référence: CMD-20251215-0001
├── Commercial: commercial_test
├── Date: 2025-12-15
└── Status: pending_validation
    │
    ├── CommercialOrderClient (Client 1)
    │   ├── ID: 1
    │   ├── Nom: "Amadou"
    │   ├── Téléphone: "123456789"
    │   ├── Type paiement: "cash"
    │   └── Articles:
    │       ├── CommercialOrderItem (ID: 1)
    │       │   ├── Article: "Madar Poudre" (ID: 5)
    │       │   ├── Quantité: 10
    │       │   └── Prix unitaire: 170000 GNF
    │       ├── CommercialOrderItem (ID: 2)
    │       │   ├── Article: "Javel 1L" (ID: 8)
    │       │   ├── Quantité: 30
    │       │   └── Prix unitaire: 50000 GNF
    │       └── CommercialOrderItem (ID: 3)
    │           ├── Article: "Riz 25kg" (ID: 12)
    │           ├── Quantité: 5
    │           └── Prix unitaire: 300000 GNF
    │
    ├── CommercialOrderClient (Client 2)
    │   ├── ID: 2
    │   ├── Nom: "Fatoumata"
    │   └── Articles:
    │       ├── CommercialOrderItem (ID: 4)
    │       │   ├── Article: "Madar Poudre" (ID: 5)
    │       │   ├── Quantité: 5
    │       │   └── Prix unitaire: 170000 GNF
    │       └── CommercialOrderItem (ID: 5)
    │           ├── Article: "Riz 25kg" (ID: 12)
    │           ├── Quantité: 15
    │           └── Prix unitaire: 200000 GNF
    │
    └── ... (Clients 3 à 10)
```

---

## 🔧 Traitement Backend (orders.py)

### Code de traitement :

```python
# 1. Créer la commande principale
order = CommercialOrder(
    reference=generate_order_reference(),
    commercial_id=current_user.id,
    order_date=order_date,
    notes=notes,
    status='draft'
)
db.session.add(order)
db.session.flush()

# 2. Traiter chaque client (boucle i)
i = 0
while True:
    client_name = request.form.get(f'client_{i}_name', '').strip()
    if not client_name:
        break  # Plus de clients
    
    # Créer le client
    order_client = CommercialOrderClient(
        order_id=order.id,
        client_name=client_name,
        client_phone=request.form.get(f'client_{i}_phone'),
        payment_type=request.form.get(f'client_{i}_payment_type', 'cash'),
        ...
    )
    db.session.add(order_client)
    db.session.flush()
    
    # 3. Traiter chaque article de ce client (boucle j)
    j = 0
    while True:
        item_id = request.form.get(f'client_{i}_item_{j}_id', type=int)
        if not item_id:
            break  # Plus d'articles pour ce client
        
        quantity = request.form.get(f'client_{i}_item_{j}_qty', type=Decimal)
        unit_price = request.form.get(f'client_{i}_item_{j}_price', type=Decimal)
        
        if quantity and quantity > 0:
            # Créer l'article de commande pour ce client
            order_item = CommercialOrderItem(
                order_client_id=order_client.id,
                stock_item_id=item_id,
                quantity=quantity,
                unit_price_gnf=unit_price
            )
            db.session.add(order_item)
        
        j += 1  # Article suivant
    
    i += 1  # Client suivant

# 4. Sauvegarder
db.session.commit()
```

---

## 📊 Format des Données Soumises (POST)

### Structure des champs du formulaire :

```
# Informations générales
order_date: 2025-12-15
notes: "Notes générales sur la commande"

# Client 0
client_0_name: "Amadou"
client_0_phone: "123456789"
client_0_address: "Conakry"
client_0_payment_type: "cash"
client_0_comments: "Paiement comptant"
client_0_notes: "Client fidèle"

# Articles du Client 0
client_0_item_0_id: 5        # ID de l'article "Madar Poudre"
client_0_item_0_qty: 10      # Quantité commandée
client_0_item_0_price: 170000 # Prix unitaire

client_0_item_1_id: 8        # ID de l'article "Javel 1L"
client_0_item_1_qty: 30
client_0_item_1_price: 50000

client_0_item_2_id: 12       # ID de l'article "Riz 25kg"
client_0_item_2_qty: 5
client_0_item_2_price: 300000

# Client 1
client_1_name: "Fatoumata"
client_1_phone: "987654321"
client_1_payment_type: "credit"
client_1_payment_due_date: "2026-01-15"

# Articles du Client 1
client_1_item_0_id: 5        # Même article "Madar Poudre"
client_1_item_0_qty: 5       # Mais quantité différente
client_1_item_0_price: 170000

client_1_item_1_id: 12       # Article "Riz 25kg"
client_1_item_1_qty: 15
client_1_item_1_price: 200000

# ... (Clients 2 à 9)
```

---

## 🎨 Interface Utilisateur

### Vue Tableau Paysage :

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [Rechercher un article...]  [Ajouter un Client]                         │
├──────────────┬──────────────┬──────────────┬──────────────┬───────────────┤
│   ARTICLES   │   CLIENT 1   │   CLIENT 2   │   CLIENT 3   │   CLIENT 10   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Nom / SKU    │ [Nom*]       │ [Nom*]       │ [Nom*]       │ [Nom*]        │
│              │ [Téléphone]  │ [Téléphone]  │ [Téléphone]  │ [Téléphone]   │
│              │ [Adresse]    │ [Adresse]    │ [Adresse]    │ [Adresse]     │
│              │ [Paiement]   │ [Paiement]   │ [Paiement]   │ [Paiement]    │
│              │ [Commentaires]│ [Commentaires]│ [Commentaires]│ [Commentaires]│
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Madar Poudre │ [Qté: 10]    │ [Qté: 5]     │ [Qté: 20]    │ [Qté: 0]      │
│ SKU: MP-001  │ [Prix: 170K] │ [Prix: 170K] │ [Prix: 165K] │               │
│              │ Total: 1.7M  │ Total: 0.85M │ Total: 3.3M  │               │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Javel 1L     │ [Qté: 30]    │ [Qté: 0]     │ [Qté: 0]     │ [Qté: 25]     │
│ SKU: JV-001  │ [Prix: 50K]  │              │              │ [Prix: 50K]   │
│              │ Total: 1.5M  │              │              │ Total: 1.25M  │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Riz 25kg     │ [Qté: 5]     │ [Qté: 15]    │ [Qté: 8]     │ [Qté: 12]     │
│ SKU: RZ-001  │ [Prix: 300K] │ [Prix: 200K] │ [Prix: 200K] │ [Prix: 195K]  │
│              │ Total: 1.5M  │ Total: 3M    │ Total: 1.6M  │ Total: 2.34M  │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ ...          │ ...          │ ...          │ ...          │ ...           │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│              │ TOTAL CLIENT │ TOTAL CLIENT │ TOTAL CLIENT │ TOTAL CLIENT  │
│              │ 1: 4,700,000 │ 2: 3,850,000 │ 3: 4,900,000 │ 10: 3,590,000 │
└──────────────┴──────────────┴──────────────┴──────────────┴───────────────┘
```

---

## ✅ Points Clés à Retenir

1. **Une seule commande** = Plusieurs clients
2. **Chaque client** = Plusieurs articles possibles
3. **Chaque article** peut avoir une quantité différente par client
4. **Chaque article** peut avoir un prix différent par client (modifiable)
5. **Les totaux** sont calculés automatiquement :
   - Total ligne = quantité × prix unitaire
   - Total client = somme de tous ses articles
   - Total commande = somme de tous les clients

---

## 🚀 Workflow Utilisateur Simplifié

```
1. Accéder à /orders/new
   ↓
2. Remplir les informations générales (Date, Notes)
   ↓
3. Ajouter les clients (jusqu'à 10)
   ├─ Cliquer "Ajouter un Client" → Colonne créée
   ├─ Remplir nom, téléphone, adresse, paiement
   └─ Répéter pour chaque client
   ↓
4. Ajouter les articles (autant que nécessaire)
   ├─ Rechercher un article dans la barre de recherche
   ├─ Cliquer sur l'article → Ligne créée
   └─ Répéter pour chaque article
   ↓
5. Remplir les quantités pour chaque client
   ├─ Pour chaque intersection Article × Client
   ├─ Entrer la quantité si le client commande cet article
   └─ Laisser vide/0 si le client ne commande pas
   ↓
6. Vérifier les totaux (calculés automatiquement)
   ↓
7. Enregistrer et soumettre à validation
   ↓
8. La commande passe en "pending_validation"
   ↓
9. La hiérarchie valide ou rejette
   ↓
10. Le magasinier génère les bons de sortie
```

---

## 📈 Exemple Concret : 10 Clients × 10 Articles

### Scénario :
- **10 clients** : Amadou, Fatoumata, Mamadou, Aissatou, Ousmane, Mariam, Ibrahima, Awa, Boubacar, Kadiatou
- **10 articles** : Madar Poudre, Javel 1L, Riz 25kg, Sucre 1kg, Huile 1L, Savon, Pâtes, Tomate concentrée, Oignon, Ail

### Résultat en base :
- **1 CommercialOrder** (référence unique)
- **10 CommercialOrderClient** (un par client)
- **~50-80 CommercialOrderItem** (selon les quantités commandées)

### Calcul des totaux :
- Chaque client a son total individuel
- Le total de la commande = somme de tous les clients
- Chaque ligne article × client a son sous-total

---

## 🔍 Avantages de cette Architecture

1. **Vue d'ensemble** : Tous les clients et articles sur une seule page
2. **Comparaison facile** : Voir qui commande quoi en un coup d'œil
3. **Gestion centralisée** : Une seule commande à valider
4. **Flexibilité** : Chaque client peut commander des articles différents
5. **Prix personnalisés** : Possibilité d'ajuster le prix par client

---

## ⚠️ Limitations Actuelles

1. **Maximum 10 clients** par commande (limite technique)
2. **Scroll horizontal** si beaucoup d'articles
3. **Tableau peut devenir large** avec beaucoup de clients

---

## 💡 Améliorations Possibles

1. Pagination des articles si trop nombreux
2. Export Excel de la commande
3. Vue détaillée par client
4. Historique des commandes par client
5. Templates de commandes récurrentes

