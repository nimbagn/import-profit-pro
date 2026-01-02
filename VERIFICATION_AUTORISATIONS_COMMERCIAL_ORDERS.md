# Vérification des Autorisations Commercial - Module Commandes

## 📋 Permissions du Rôle Commercial

### Permissions Définies (app.py ligne 270)
```python
'orders': ['read', 'create', 'update']
```

**✅ Permissions accordées :**
- ✅ `orders.read` - Lire les commandes
- ✅ `orders.create` - Créer des commandes
- ✅ `orders.update` - Modifier des commandes

**❌ Permissions non accordées (normal) :**
- ❌ `orders.validate` - Valider des commandes (réservé aux superviseurs/admins)

## 🔍 Routes Vérifiées

### 1. `/orders/` - Liste des commandes
**Route :** `orders_list()`
**Permission requise :** `orders.read`
**Comportement pour commercial :**
- ✅ Accès autorisé
- ✅ Voit uniquement SES commandes (filtrées par `commercial_id == current_user.id`)
- ✅ Peut filtrer par statut, recherche, tri

**Code de vérification :**
```python
if current_user.role and current_user.role.code == 'commercial':
    query = query.filter(CommercialOrder.commercial_id == current_user.id)
```

### 2. `/orders/new` - Créer une commande
**Route :** `order_new()`
**Permission requise :** `orders.create`
**Comportement pour commercial :**
- ✅ Accès autorisé
- ✅ Vérification que l'utilisateur est bien commercial
- ✅ La commande est automatiquement associée au commercial connecté

**Code de vérification :**
```python
if not has_permission(current_user, 'orders.create'):
    flash('Vous n\'avez pas la permission de créer une commande', 'error')
    return redirect(url_for('orders.orders_list'))

if current_user.role and current_user.role.code != 'commercial':
    flash('Seuls les commerciaux peuvent créer des commandes', 'error')
    return redirect(url_for('orders.orders_list'))
```

### 3. `/orders/<id>` - Détail d'une commande
**Route :** `order_detail(id)`
**Permission requise :** `orders.read` (implicite)
**Comportement pour commercial :**
- ✅ Accès autorisé UNIQUEMENT à SES commandes
- ✅ Si la commande n'est pas la sienne, redirection avec message d'erreur
- ✅ Peut voir les détails, clients, articles

**Code de vérification :**
```python
if current_user.role and current_user.role.code == 'commercial':
    if order.commercial_id != current_user.id:
        flash('Vous n\'avez pas accès à cette commande. Vous ne pouvez voir que vos propres commandes dans votre session.', 'error')
        return redirect(url_for('orders.orders_list'))
```

### 4. `/orders/<id>/edit` - Modifier une commande
**Route :** `order_edit(id)`
**Permission requise :** `orders.update`
**Comportement pour commercial :**
- ✅ Accès autorisé
- ✅ Peut modifier UNIQUEMENT SES commandes
- ✅ Peut modifier seulement si statut = 'draft', 'rejected', ou 'pending_validation'
- ✅ Ne peut pas modifier les commandes validées

**Code de vérification :**
```python
if not has_permission(current_user, 'orders.update'):
    flash('Vous n\'avez pas la permission de modifier une commande', 'error')
    return redirect(url_for('orders.order_detail', id=id))

if order.status not in ('draft', 'rejected', 'pending_validation'):
    flash('Cette commande ne peut pas être modifiée', 'error')
    return redirect(url_for('orders.order_detail', id=id))

if current_user.role and current_user.role.code == 'commercial':
    if order.commercial_id != current_user.id:
        flash('Vous ne pouvez modifier que vos propres commandes', 'error')
        return redirect(url_for('orders.order_detail', id=id))
```

### 5. `/orders/<id>/validate` - Valider une commande
**Route :** `order_validate(id)`
**Permission requise :** `orders.validate`
**Comportement pour commercial :**
- ❌ Accès refusé (normal, réservé aux superviseurs/admins)
- ✅ Message d'erreur clair

**Code de vérification :**
```python
if not has_permission(current_user, 'orders.validate'):
    flash('Vous n\'avez pas la permission de valider des commandes', 'error')
    return redirect(url_for('orders.orders_list'))
```

### 6. `/orders/<id>/reject` - Rejeter une commande
**Route :** `order_reject(id)`
**Permission requise :** `orders.validate`
**Comportement pour commercial :**
- ❌ Accès refusé (normal, réservé aux superviseurs/admins)

### 7. `/orders/<order_id>/client/<client_id>/approve` - Approuver un client
**Route :** `client_approve(order_id, client_id)`
**Permission requise :** `orders.validate`
**Comportement pour commercial :**
- ❌ Accès refusé (normal, réservé aux superviseurs/admins)

### 8. `/orders/<order_id>/client/<client_id>/reject` - Rejeter un client
**Route :** `client_reject(order_id, client_id)`
**Permission requise :** `orders.validate`
**Comportement pour commercial :**
- ❌ Accès refusé (normal, réservé aux superviseurs/admins)

### 9. `/orders/<id>/generate-outgoing` - Générer un bon de sortie
**Route :** `order_generate_outgoing(id)`
**Permission requise :** `outgoings.create`
**Comportement pour commercial :**
- ❌ Accès refusé (normal, réservé au magasinier)
- ✅ Le commercial n'a pas la permission `outgoings.create`
- ✅ Le bouton ne s'affiche pas dans le template (vérification `has_permission(current_user, 'outgoings.create')`)

## ✅ Résumé des Vérifications

### Routes Accessibles au Commercial
1. ✅ `/orders/` - Liste (ses commandes uniquement)
2. ✅ `/orders/new` - Créer
3. ✅ `/orders/<id>` - Détail (ses commandes uniquement)
4. ✅ `/orders/<id>/edit` - Modifier (ses commandes uniquement, statuts spécifiques)

### Routes Inaccessibles au Commercial (Normal)
1. ❌ `/orders/<id>/validate` - Valider (superviseur/admin)
2. ❌ `/orders/<id>/reject` - Rejeter (superviseur/admin)
3. ❌ `/orders/<order_id>/client/<client_id>/approve` - Approuver client (superviseur/admin)
4. ❌ `/orders/<order_id>/client/<client_id>/reject` - Rejeter client (superviseur/admin)

## 🔧 Points à Vérifier

1. **Route generate-outgoing** : Vérifier les permissions
2. **Filtrage par région** : Vérifier que le commercial ne voit que les commandes de sa région
3. **Templates** : Vérifier que les boutons de validation/rejet ne s'affichent pas pour le commercial

## 📝 Recommandations

1. ✅ Les permissions sont correctement configurées
2. ✅ Le filtrage par commercial_id fonctionne
3. ✅ Les vérifications de sécurité sont en place
4. ⚠️ Vérifier la route `generate-outgoing` pour les permissions

