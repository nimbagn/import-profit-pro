# Guide : Permissions du Rôle Magasinier

## 🔍 Problème Identifié

Le magasinier n'avait pas accès à toutes les fonctionnalités du module `/stocks` car il lui manquait les permissions pour :
- **Réceptions** (`receptions.read`, `receptions.create`, `receptions.update`)
- **Retours** (`returns.read`, `returns.create`, `returns.update`)

## ✅ Solution Appliquée

### 1. Mise à Jour du Code Python

Les permissions ont été ajoutées au rôle magasinier dans `app.py` :

```python
{
    'name': 'Magasinier',
    'code': 'warehouse',
    'description': 'Gestion des réceptions, transferts et inventaires',
    'permissions': {
        'stocks': ['read', 'create', 'update'],
        'movements': ['read', 'create'],
        'inventory': ['read', 'create', 'update'],
        'receptions': ['read', 'create', 'update'],  # ✅ AJOUTÉ
        'outgoings': ['read', 'create', 'update'],
        'returns': ['read', 'create', 'update'],     # ✅ AJOUTÉ
        'vehicles': ['read'],
        'regions': ['read'],
        'depots': ['read'],
        'families': ['read'],
        'stock_items': ['read'],
        'orders': ['read'],
        'stock_loading': ['read', 'verify', 'load']
    }
}
```

### 2. Mise à Jour de la Base de Données

**⚠️ IMPORTANT** : Vous devez exécuter le script SQL approprié pour mettre à jour les permissions dans votre base de données.

#### Pour PostgreSQL (Render)

```bash
# Via psql ou l'interface Render
psql $DATABASE_URL -f scripts/ajouter_permissions_magasinier_postgresql.sql
```

Ou directement dans l'interface Render :
1. Aller dans votre base de données PostgreSQL
2. Ouvrir l'onglet "SQL Editor"
3. Copier-coller le contenu de `scripts/ajouter_permissions_magasinier_postgresql.sql`
4. Exécuter le script

#### Pour MySQL

```bash
mysql -u USERNAME -p DATABASE_NAME < scripts/ajouter_permissions_magasinier_mysql.sql
```

## 📋 Permissions Complètes du Magasinier

Le magasinier a maintenant accès à **toutes** les fonctionnalités suivantes :

### ✅ Stocks
- ✅ Voir les stocks (dépôt, véhicule)
- ✅ Voir les alertes mini-stock
- ✅ Créer des mouvements de stock
- ✅ Mettre à jour les stocks
- ✅ Voir l'historique des mouvements
- ✅ Exporter les données (Excel, PDF)

### ✅ Mouvements
- ✅ Voir la liste des mouvements
- ✅ Créer des mouvements (transferts, ajustements)
- ✅ Voir les détails d'un mouvement
- ✅ Exporter les mouvements (Excel)
- ❌ Modifier/Supprimer des mouvements (réservé à l'admin)

### ✅ Réceptions
- ✅ Voir la liste des réceptions
- ✅ Créer une nouvelle réception
- ✅ Voir les détails d'une réception
- ✅ Mettre à jour une réception
- ✅ Exporter les réceptions (Excel)

### ✅ Sorties (Outgoings)
- ✅ Voir la liste des sorties
- ✅ Créer une nouvelle sortie
- ✅ Voir les détails d'une sortie
- ✅ Mettre à jour une sortie
- ✅ Exporter les sorties (Excel)

### ✅ Retours
- ✅ Voir la liste des retours
- ✅ Créer un nouveau retour
- ✅ Voir les détails d'un retour
- ✅ Mettre à jour un retour
- ✅ Exporter les retours (Excel)

### ✅ Inventaires
- ✅ Voir les inventaires
- ✅ Créer un inventaire
- ✅ Mettre à jour un inventaire

### ✅ Dashboard Magasinier
- ✅ Accéder au dashboard magasinier (`/stocks/warehouse/dashboard`)
- ✅ Voir les récapitulatifs de chargement
- ✅ Vérifier le stock avant chargement
- ✅ Effectuer le chargement

### ✅ Résumés et Exports
- ✅ Voir le récapitulatif de stock (`/stocks/summary`)
- ✅ Prévisualiser avant export
- ✅ Exporter en PDF
- ✅ Exporter en Excel
- ✅ API JSON pour mise à jour en temps réel

## 🔒 Fonctionnalités Réservées à l'Admin

Les fonctionnalités suivantes restent réservées à l'administrateur :
- ❌ Modifier un mouvement (`/stocks/movements/<id>/edit`)
- ❌ Supprimer un mouvement (`/stocks/movements/<id>/delete`)
- ❌ Mettre à jour les signes des mouvements (`/stocks/update-movements-signs`)

## 🧪 Test des Permissions

Pour vérifier que les permissions fonctionnent correctement :

1. **Se connecter avec un compte magasinier**
2. **Accéder à `/stocks`**
3. **Vérifier l'accès aux sections suivantes** :
   - ✅ `/stocks/receptions` - Liste des réceptions
   - ✅ `/stocks/receptions/new` - Créer une réception
   - ✅ `/stocks/returns` - Liste des retours
   - ✅ `/stocks/returns/new` - Créer un retour
   - ✅ `/stocks/outgoings` - Liste des sorties
   - ✅ `/stocks/movements` - Liste des mouvements
   - ✅ `/stocks/summary` - Récapitulatif
   - ✅ `/stocks/warehouse/dashboard` - Dashboard magasinier

## 📝 Notes Importantes

1. **Les permissions sont stockées en JSON** dans la colonne `permissions` de la table `roles`
2. **Le format JSON** est : `{"module": ["action1", "action2"]}`
3. **Les permissions sont vérifiées** par la fonction `has_permission()` dans `auth.py`
4. **L'admin a tous les droits** et passe toutes les vérifications de permissions

## 🚀 Déploiement

Après avoir exécuté le script SQL, redémarrez l'application pour que les changements prennent effet :

```bash
# Sur Render, le redémarrage est automatique après un push
git add .
git commit -m "fix: Ajout permissions receptions et returns au rôle magasinier"
git push origin main
```

## 📞 Support

Si vous rencontrez des problèmes après la mise à jour :
1. Vérifiez que le script SQL a été exécuté avec succès
2. Vérifiez les permissions dans la base de données : `SELECT permissions FROM roles WHERE code = 'warehouse';`
3. Vérifiez les logs de l'application pour les erreurs de permissions
4. Assurez-vous que l'utilisateur a bien le rôle `warehouse` assigné

