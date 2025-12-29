# 📋 CHEMINEMENT COMPLET - AJOUT D'ARTICLES DANS UNE COMMANDE COMMERCIALE

## 🎯 Vue d'ensemble

Ce document explique le flux complet depuis l'accès à la page de création de commande jusqu'à la soumission du formulaire avec articles.

---

## 🔄 PHASE 1 : CHARGEMENT DE LA PAGE (GET /orders/new)

### 1.1 Backend - Route Flask (`orders.py` ligne 152-317)

```python
@orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def order_new():
```

**Étapes backend :**

1. **Vérification des permissions** (ligne 156-163)
   - ✅ Vérifie `orders.create`
   - ✅ Vérifie que l'utilisateur est de rôle `'commercial'`

2. **Récupération des articles actifs** (ligne 262)
   ```python
   stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
   ```
   - Récupère tous les `StockItem` actifs de la base de données

3. **Récupération de la fiche de prix active** (ligne 268-275)
   ```python
   active_price_list = PriceList.query.filter(
       PriceList.is_active == True,
       PriceList.start_date <= today,
       db.or_(PriceList.end_date.is_(None), PriceList.end_date >= today)
   ).order_by(PriceList.start_date.desc()).first()
   ```
   - Cherche la fiche de prix active pour la date du jour
   - Priorité : `wholesale_price` (prix grossiste) > `retail_price` (prix détaillant)

4. **Création du dictionnaire de prix** (ligne 277-286)
   ```python
   prices_by_name = {}
   if active_price_list:
       for price_item in active_price_list.items:
           if price_item.article:
               price = price_item.wholesale_price or price_item.retail_price
               if price:
                   prices_by_name[price_item.article.name.lower()] = float(price)
   ```
   - **Lien Article ↔ StockItem** : Par le **nom** (car Article n'a pas de SKU)
   - Crée un dictionnaire `{nom_article: prix}` en minuscules

5. **Conversion en JSON pour JavaScript** (ligne 288-313)
   ```python
   stock_items_json = []
   for item in stock_items:
       item_data = {
           'id': int(item.id),
           'name': str(item.name),
           'sku': str(item.sku),
           'default_price': None
       }
       
       # Chercher le prix dans la fiche de prix
       item_name_lower = item.name.lower()
       if item_name_lower in prices_by_name:
           item_data['default_price'] = float(prices_by_name[item_name_lower])
       # Fallback : prix d'achat
       elif item.purchase_price_gnf:
           item_data['default_price'] = float(item.purchase_price_gnf)
       
       stock_items_json.append(item_data)
   ```
   - Convertit chaque article en objet JSON avec :
     - `id` : ID de l'article
     - `name` : Nom de l'article
     - `sku` : Code SKU
     - `default_price` : Prix par défaut (fiche de prix OU prix d'achat)

6. **Rendu du template** (ligne 315-317)
   ```python
   return render_template('orders/order_form.html',
                        stock_items=stock_items_json,
                        today=datetime.now(UTC).strftime('%Y-%m-%d'))
   ```
   - Passe `stock_items_json` au template Jinja2

---

### 1.2 Frontend - Chargement JavaScript (`order_form.html` ligne 896-917)

```javascript
let stockItems = [];
try {
  stockItems = {{ stock_items|tojson|safe }};
  if (!Array.isArray(stockItems)) {
    stockItems = [];
  }
} catch (e) {
  console.error('❌ Erreur lors du chargement des articles:', e);
  stockItems = [];
}
```

**Résultat :**
- Tableau JavaScript `stockItems` chargé avec tous les articles et leurs prix
- Exemple : `[{id: 1, name: "Madar Poudre 10 kg", sku: "M10KGX01SAC", default_price: 170000}]`

---

## 🔍 PHASE 2 : RECHERCHE D'ARTICLES

### 2.1 Saisie dans le champ de recherche

**HTML** (ligne 836) :
```html
<input type="text" id="itemSearch" placeholder="Tapez le nom ou SKU de l'article..." autocomplete="off">
```

**Événement JavaScript** (ligne 1026-1032) :
```javascript
const searchInput = document.getElementById('itemSearch');
searchInput.addEventListener('input', function() {
    searchItems(this.value);
});
```

### 2.2 Fonction de recherche (`order_form.html` ligne 857-906)

```javascript
function searchItems(query) {
  const resultsDiv = document.getElementById('searchResults');
  
  if (!query || query.length < 2) {
    resultsDiv.style.display = 'none';
    return;
  }
  
  // Filtrer les articles par nom ou SKU
  const filtered = stockItems.filter(item => 
    item.name.toLowerCase().includes(query.toLowerCase()) ||
    (item.sku && item.sku.toLowerCase().includes(query.toLowerCase()))
  );
  
  // Afficher les résultats (max 10)
  filtered.slice(0, 10).forEach(item => {
    const div = document.createElement('div');
    div.onclick = function() { 
      addItemRow(item);  // ← Ajouter l'article au tableau
      document.getElementById('itemSearch').value = '';
      resultsDiv.style.display = 'none';
    };
    div.innerHTML = `
      <strong>${item.name}</strong>
      <small>SKU: ${item.sku || 'N/A'}</small>
      ${item.default_price ? ` • ${item.default_price.toLocaleString('fr-FR')} GNF` : ''}
    `;
    resultsDiv.appendChild(div);
  });
}
```

**Résultat :**
- Affiche les articles correspondants avec leur prix
- Clic sur un résultat → appelle `addItemRow(item)`

---

## ➕ PHASE 3 : AJOUT D'UN ARTICLE AU TABLEAU

### 3.1 Fonction `addItemRow()` (`order_form.html` ligne 1039-1084)

```javascript
function addItemRow(item) {
  const itemsBody = document.getElementById('itemsBody');
  const row = document.createElement('tr');
  row.dataset.itemId = item.id;  // Stocke l'ID de l'article
  
  // 1. Colonne article (nom + SKU + bouton supprimer)
  const itemCell = document.createElement('td');
  itemCell.innerHTML = `
    <strong>${item.name}</strong>
    <small>SKU: ${item.sku || 'N/A'}</small>
    <button onclick="removeItemRow(this)">Supprimer</button>
  `;
  row.appendChild(itemCell);
  
  // 2. Colonnes pour chaque client existant
  const clientHeaders = document.getElementById('clientHeadersRow').querySelectorAll('th.client-col');
  const defaultPrice = item.default_price || '';  // Prix pré-rempli
  
  clientHeaders.forEach((header, index) => {
    const cell = document.createElement('td');
    cell.innerHTML = `
      <input type="number" name="client_${index}_item_${itemCount}_qty" 
             placeholder="Qté" 
             onchange="calculateLineTotal(${index}, ${itemCount})">
      <input type="number" name="client_${index}_item_${itemCount}_price" 
             placeholder="Prix unit. (GNF)" 
             value="${defaultPrice}"  // ← Prix pré-rempli ici
             onchange="calculateLineTotal(${index}, ${itemCount})">
      <div class="line-total">Total: 0 GNF</div>
      <input type="hidden" name="client_${index}_item_${itemCount}_id" value="${item.id}">
    `;
    row.appendChild(cell);
  });
  
  itemsBody.appendChild(row);
  itemCount++;
}
```

**Résultat :**
- Nouvelle ligne ajoutée dans le tableau
- Pour chaque client existant, création de champs :
  - Quantité (`client_X_item_Y_qty`)
  - Prix unitaire (`client_X_item_Y_price`) **pré-rempli avec `default_price`**
  - Total de la ligne (calculé automatiquement)
  - ID de l'article en champ caché (`client_X_item_Y_id`)

---

## 🧮 PHASE 4 : CALCUL AUTOMATIQUE DES TOTAUX

### 4.1 Calcul du total d'une ligne (`order_form.html` ligne 908-924)

```javascript
function calculateLineTotal(clientId, itemIndex) {
  const qtyInput = document.querySelector(`input[name="client_${clientId}_item_${itemIndex}_qty"]`);
  const priceInput = document.querySelector(`input[name="client_${clientId}_item_${itemIndex}_price"]`);
  const totalDiv = document.querySelector(`.line-total[data-client="${clientId}"][data-item="${itemIndex}"]`);
  
  const qty = parseFloat(qtyInput.value) || 0;
  const price = parseFloat(priceInput.value) || 0;
  const total = qty * price;
  
  totalDiv.textContent = `Total: ${total.toLocaleString('fr-FR')} GNF`;
  
  // Mettre à jour les totaux client et commande
  calculateClientTotal(clientId);
  calculateOrderTotal();
}
```

**Déclenchement :**
- Sur changement de quantité OU prix
- Via `onchange="calculateLineTotal(...)"`

### 4.2 Calcul du total client (`order_form.html` ligne 926-961)

```javascript
function calculateClientTotal(clientId) {
  let clientTotal = 0;
  const qtyInputs = document.querySelectorAll(`input[name^="client_${clientId}_item_"][name$="_qty"]`);
  
  qtyInputs.forEach(qtyInput => {
    const name = qtyInput.name;
    const match = name.match(/item_(\d+)_qty/);
    if (match) {
      const itemIndex = match[1];
      const priceInput = document.querySelector(`input[name="client_${clientId}_item_${itemIndex}_price"]`);
      
      const qty = parseFloat(qtyInput.value) || 0;
      const price = parseFloat(priceInput.value) || 0;
      clientTotal += qty * price;
    }
  });
  
  // Afficher dans l'en-tête du client
  const totalDiv = clientHeader.querySelector('.client-total');
  totalDiv.textContent = `Total: ${clientTotal.toLocaleString('fr-FR')} GNF`;
}
```

### 4.3 Calcul du total de la commande (`order_form.html` ligne 963-1005)

```javascript
function calculateOrderTotal() {
  let orderTotal = 0;
  const clientHeaders = document.querySelectorAll('th.client-col');
  
  clientHeaders.forEach((header, index) => {
    const clientId = index;
    // Somme tous les totaux de tous les clients
    // ...
    orderTotal += clientTotal;
  });
  
  // Afficher le total global
  document.getElementById('orderTotal').innerHTML = `
    Total de la commande: ${orderTotal.toLocaleString('fr-FR')} GNF
  `;
}
```

---

## 📤 PHASE 5 : SOUMISSION DU FORMULAIRE (POST /orders/new)

### 5.1 Structure des données envoyées

**Format des noms de champs :**
```
client_0_name          → Nom du premier client
client_0_phone         → Téléphone du premier client
client_0_payment_type  → Type de paiement (cash/credit)
client_0_item_0_id     → ID de l'article 0 pour client 0
client_0_item_0_qty    → Quantité de l'article 0 pour client 0
client_0_item_0_price  → Prix unitaire de l'article 0 pour client 0
client_0_item_1_id     → ID de l'article 1 pour client 0
...
client_1_name          → Nom du deuxième client
...
```

### 5.2 Traitement backend (`orders.py` ligne 165-259)

**1. Création de la commande** (ligne 174-184)
```python
order = CommercialOrder(
    reference=generate_order_reference(),  # Ex: CMD-20251215-0001
    order_date=datetime.strptime(order_date, '%Y-%m-%d'),
    commercial_id=current_user.id,
    region_id=current_user.region_id,
    status='draft',
    user_id=current_user.id
)
db.session.add(order)
db.session.flush()  # Pour obtenir order.id
```

**2. Traitement des clients** (ligne 186-247)
```python
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
        payment_due_date=...,  # Si crédit
        comments=request.form.get(f'client_{i}_comments'),
        notes=request.form.get(f'client_{i}_notes')
    )
    db.session.add(order_client)
    db.session.flush()
    
    # Traiter les articles du client
    j = 0
    while True:
        item_id = request.form.get(f'client_{i}_item_{j}_id', type=int)
        if not item_id:
            break  # Plus d'articles pour ce client
        
        quantity = request.form.get(f'client_{i}_item_{j}_qty', type=Decimal)
        unit_price = request.form.get(f'client_{i}_item_{j}_price', type=Decimal)
        
        if quantity and quantity > 0:
            order_item = CommercialOrderItem(
                order_client_id=order_client.id,
                stock_item_id=item_id,
                quantity=quantity,
                unit_price_gnf=unit_price,
                notes=request.form.get(f'client_{i}_item_{j}_notes')
            )
            db.session.add(order_item)
        
        j += 1
    
    i += 1
```

**3. Validation et sauvegarde** (ligne 254-259)
```python
order.status = 'pending_validation'  # En attente de validation hiérarchique
db.session.commit()

flash(f'Commande "{reference}" créée avec succès et soumise à validation', 'success')
return redirect(url_for('orders.order_detail', id=order.id))
```

---

## 📊 RÉSUMÉ DU FLUX COMPLET

```
1. UTILISATEUR ACCÈDE À /orders/new
   ↓
2. BACKEND (orders.py)
   ├─ Vérifie permissions
   ├─ Récupère StockItem actifs
   ├─ Récupère PriceList active
   ├─ Crée dictionnaire prix par nom
   ├─ Convertit en JSON avec default_price
   └─ Rend template avec stock_items_json
   ↓
3. FRONTEND (order_form.html)
   ├─ Charge stockItems en JavaScript
   ├─ Crée Client 1 automatiquement
   └─ Prêt pour recherche
   ↓
4. UTILISATEUR TAPE DANS LE CHAMP DE RECHERCHE
   ↓
5. JavaScript searchItems()
   ├─ Filtre stockItems par nom/SKU
   ├─ Affiche résultats avec prix
   └─ Clic → addItemRow(item)
   ↓
6. JavaScript addItemRow()
   ├─ Crée ligne dans tableau
   ├─ Ajoute colonnes pour chaque client
   ├─ Pré-remplit prix avec default_price
   └─ Ajoute champs quantité/prix/total
   ↓
7. UTILISATEUR SAISIT QUANTITÉS
   ↓
8. JavaScript calculateLineTotal()
   ├─ Calcule qty × price
   ├─ Met à jour total ligne
   ├─ Appelle calculateClientTotal()
   └─ Appelle calculateOrderTotal()
   ↓
9. UTILISATEUR SOUMET LE FORMULAIRE
   ↓
10. BACKEND TRAITE POST
    ├─ Crée CommercialOrder
    ├─ Crée CommercialOrderClient(s)
    ├─ Crée CommercialOrderItem(s)
    ├─ Status = 'pending_validation'
    └─ Redirige vers détail commande
```

---

## 🔑 POINTS CLÉS

### 1. **Lien Article ↔ StockItem**
- **Par le nom** (pas par SKU)
- `PriceListItem.article.name` → `StockItem.name`
- Conversion en minuscules pour comparaison

### 2. **Priorité des prix**
1. **Prix grossiste** (`wholesale_price`) de la fiche de prix active
2. **Prix détaillant** (`retail_price`) si pas de grossiste
3. **Prix d'achat** (`purchase_price_gnf`) comme fallback

### 3. **Calculs automatiques**
- **Total ligne** = quantité × prix unitaire
- **Total client** = somme des totaux lignes du client
- **Total commande** = somme des totaux clients
- Mise à jour en temps réel sur changement

### 4. **Structure des données**
- Format : `client_{i}_item_{j}_{field}`
- `i` = index du client (0, 1, 2...)
- `j` = index de l'article (0, 1, 2...)
- `field` = id, qty, price, notes

### 5. **Sécurité**
- ✅ Vérification permissions (`orders.create`)
- ✅ Vérification rôle commercial
- ✅ CSRF token dans le formulaire
- ✅ Validation côté serveur

---

## 🎯 EXEMPLE CONCRET

**Scénario :**
- Client 1 : Amadou
- Article : Madar Poudre 10 kg (ID: 1, Prix: 170 000 GNF)
- Quantité : 10 sacs

**Données envoyées :**
```
client_0_name = "Amadou"
client_0_phone = "622123456"
client_0_payment_type = "cash"
client_0_item_0_id = 1
client_0_item_0_qty = 10
client_0_item_0_price = 170000
```

**Résultat en base :**
- `CommercialOrder` : référence CMD-20251215-0001
- `CommercialOrderClient` : Amadou (cash)
- `CommercialOrderItem` : 10 × Madar Poudre @ 170 000 GNF
- Total : 1 700 000 GNF

---

**✅ Le système est maintenant complètement fonctionnel !**

---

## 📌 CLARIFICATION IMPORTANTE : MULTIPLES ARTICLES PAR CLIENT

### ✅ Le système permet déjà cela !

**Chaque client peut commander PLUSIEURS articles avec des quantités différentes.**

### Exemple concret :

**Client 1 : Amadou**
- Article A (Madar Poudre 10 kg) : **10 sacs** @ 170 000 GNF = 1 700 000 GNF
- Article B (Riz 25 kg) : **5 sacs** @ 200 000 GNF = 1 000 000 GNF
- Article C (Javel 1L) : **20 cartons** @ 50 000 GNF = 1 000 000 GNF
- **Total Client 1** : 3 700 000 GNF

**Client 2 : Fatoumata**
- Article A (Madar Poudre 10 kg) : **15 sacs** @ 170 000 GNF = 2 550 000 GNF
- Article C (Javel 1L) : **10 cartons** @ 50 000 GNF = 500 000 GNF
- **Total Client 2** : 3 050 000 GNF

**Total Commande** : 6 750 000 GNF

### Comment ça fonctionne :

1. **Ajouter plusieurs articles** :
   - Rechercher "madar" → Cliquer → Article ajouté
   - Rechercher "riz" → Cliquer → Article ajouté
   - Rechercher "javel" → Cliquer → Article ajouté
   - **Chaque article crée une nouvelle ligne dans le tableau**

2. **Pour chaque client, chaque article a ses propres champs** :
   ```
   Client 0 (Amadou) :
   ├─ client_0_item_0_qty = 10  (Madar Poudre)
   ├─ client_0_item_0_price = 170000
   ├─ client_0_item_1_qty = 5   (Riz)
   ├─ client_0_item_1_price = 200000
   ├─ client_0_item_2_qty = 20  (Javel)
   └─ client_0_item_2_price = 50000
   
   Client 1 (Fatoumata) :
   ├─ client_1_item_0_qty = 15  (Madar Poudre)
   ├─ client_1_item_0_price = 170000
   ├─ client_1_item_1_qty = 10  (Javel)
   └─ client_1_item_1_price = 50000
   ```

3. **Structure du tableau** :
   ```
   | Articles          | Client 1 (Amadou)        | Client 2 (Fatoumata)     |
   |-------------------|--------------------------|--------------------------|
   | Madar Poudre 10kg | Qté: 10, Prix: 170000   | Qté: 15, Prix: 170000   |
   |                   | Total: 1 700 000 GNF     | Total: 2 550 000 GNF     |
   |-------------------|--------------------------|--------------------------|
   | Riz 25kg          | Qté: 5, Prix: 200000     | (vide - pas commandé)    |
   |                   | Total: 1 000 000 GNF     |                          |
   |-------------------|--------------------------|--------------------------|
   | Javel 1L          | Qté: 20, Prix: 50000     | Qté: 10, Prix: 50000     |
   |                   | Total: 1 000 000 GNF     | Total: 500 000 GNF       |
   |-------------------|--------------------------|--------------------------|
   |                   | Total Client: 3 700 000   | Total Client: 3 050 000  |
   ```

### Traitement backend :

Le backend traite chaque client et tous ses articles :

```python
# Pour chaque client
i = 0
while True:
    client_name = request.form.get(f'client_{i}_name')
    if not client_name:
        break
    
    # Créer le client
    order_client = CommercialOrderClient(...)
    
    # Pour chaque article de ce client
    j = 0
    while True:
        item_id = request.form.get(f'client_{i}_item_{j}_id')
        if not item_id:
            break  # Plus d'articles pour ce client
        
        quantity = request.form.get(f'client_{i}_item_{j}_qty')
        unit_price = request.form.get(f'client_{i}_item_{j}_price')
        
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
```

### Résultat en base de données :

```
CommercialOrder (ID: 1, Réf: CMD-20251215-0001)
├─ CommercialOrderClient (ID: 1, Nom: "Amadou")
│  ├─ CommercialOrderItem (ID: 1, Article: Madar Poudre, Qté: 10, Prix: 170000)
│  ├─ CommercialOrderItem (ID: 2, Article: Riz, Qté: 5, Prix: 200000)
│  └─ CommercialOrderItem (ID: 3, Article: Javel, Qté: 20, Prix: 50000)
│
└─ CommercialOrderClient (ID: 2, Nom: "Fatoumata")
   ├─ CommercialOrderItem (ID: 4, Article: Madar Poudre, Qté: 15, Prix: 170000)
   └─ CommercialOrderItem (ID: 5, Article: Javel, Qté: 10, Prix: 50000)
```

### ✅ Points importants :

1. **Chaque client peut commander des articles différents**
2. **Chaque client peut commander les mêmes articles avec des quantités différentes**
3. **Chaque article peut avoir un prix différent par client** (modifiable)
4. **Les totaux sont calculés automatiquement** :
   - Total ligne = quantité × prix unitaire
   - Total client = somme de tous ses articles
   - Total commande = somme de tous les clients

### 🎯 Workflow utilisateur :

1. Ajouter un client → Colonne créée
2. Rechercher "article 1" → Cliquer → Ligne créée avec colonnes pour tous les clients
3. Remplir quantité/prix pour Client 1
4. Remplir quantité/prix pour Client 2 (peut être différent)
5. Rechercher "article 2" → Cliquer → Nouvelle ligne créée
6. Remplir quantités/prix pour chaque client
7. Répéter pour autant d'articles que nécessaire
8. Les totaux se calculent automatiquement

**✅ Le système gère parfaitement plusieurs articles par client avec des quantités différentes !**
