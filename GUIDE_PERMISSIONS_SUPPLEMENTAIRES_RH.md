# 🔐 GUIDE DES PERMISSIONS SUPPLÉMENTAIRES - DÉPARTEMENT RH

**Date :** 2025-01-XX  
**Version :** 1.0

---

## 📋 VUE D'ENSEMBLE

Le système de permissions supplémentaires permet d'attribuer des accès additionnels aux utilisateurs du département RH, au-delà de leurs permissions de rôle standard.

### 🎯 Objectif

Permettre aux administrateurs d'attribuer des accès spécifiques (comme la vue du stock, les commandes, etc.) à certains utilisateurs RH selon leurs besoins opérationnels.

---

## 🔧 INSTALLATION

### 1. Ajouter la colonne dans la base de données

#### Pour PostgreSQL (Recommandé pour Render)

**Méthode 1 : Script Python (Recommandé)**

```bash
# Sur Render : Shell Render
python3 execute_migration_additional_permissions_postgresql.py

# En local
export DATABASE_URL="postgresql://user:password@host:port/database"
python3 execute_migration_additional_permissions_postgresql.py
```

**Méthode 2 : Script SQL direct**

```bash
# Via psql
psql -h host -U user -d database -f scripts/add_additional_permissions_column_postgresql.sql
```

**Méthode 3 : Via SQLAlchemy dans Python**

```python
from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    with open('scripts/add_additional_permissions_column_postgresql.sql', 'r') as f:
        sql = f.read()
    db.session.execute(text(sql))
    db.session.commit()
```

#### Pour MySQL (Si vous utilisez MySQL)

```bash
mysql -u root -p madargn < scripts/add_additional_permissions_column.sql
```

Ou directement dans MySQL :

```sql
USE madargn;
ALTER TABLE `users` ADD COLUMN `additional_permissions` JSON NULL AFTER `last_login`;
```

---

## 📖 FONCTIONNEMENT

### 1. **Permissions de Rôle vs Permissions Supplémentaires**

- **Permissions de Rôle** : Définies dans le rôle (ex: `rh_manager`, `rh_assistant`)
  - S'appliquent à tous les utilisateurs ayant ce rôle
  - Gérées dans `/auth/roles`

- **Permissions Supplémentaires** : Attribuées individuellement à un utilisateur
  - S'ajoutent aux permissions du rôle
  - Gérées dans `/auth/users/<id>/edit`
  - Visibles uniquement pour les utilisateurs RH

### 2. **Ordre de Vérification des Permissions**

La fonction `has_permission()` vérifie dans cet ordre :

1. ✅ **Admin** : Accès complet (retourne `True` immédiatement)
2. ✅ **Permissions Supplémentaires** : Vérifie `user.additional_permissions`
3. ✅ **Permissions du Rôle** : Vérifie `user.role.permissions`

Si une permission est trouvée à n'importe quelle étape, l'accès est accordé.

---

## 🎨 INTERFACE UTILISATEUR

### Attribution des Permissions Supplémentaires

1. **Accéder à l'édition d'un utilisateur RH** :
   - Menu : `/auth/users`
   - Cliquer sur "Modifier" pour un utilisateur RH

2. **Section "Permissions Supplémentaires"** :
   - Visible uniquement si l'utilisateur a un rôle RH
   - Liste tous les modules disponibles avec leurs actions
   - Cases à cocher pour sélectionner les permissions

3. **Modules Disponibles** :
   - **Stocks** : `stocks.read`, `stocks.create`, `stocks.update`, `stocks.delete`
   - **Mouvements de Stock** : `movements.read`, `movements.create`, etc.
   - **Inventaires** : `inventory.read`, `inventory.create`, `inventory.validate`
   - **Flotte** : `vehicles.read`, `vehicles.create`, etc.
   - **Commandes** : `orders.read`, `orders.create`, `orders.validate`
   - **Rapports** : `reports.read`, `reports.export`
   - **Analytics** : `analytics.read`, `analytics.export`
   - Et tous les autres modules disponibles

---

## 💡 EXEMPLES D'UTILISATION

### Exemple 1 : RH Manager avec accès au stock

**Scénario** : Un RH Manager doit pouvoir consulter les stocks pour analyser les besoins en personnel.

**Configuration** :
1. Aller dans `/auth/users/<id>/edit`
2. Dans "Permissions Supplémentaires", cocher :
   - ✅ `stocks.read`
   - ✅ `stock_items.read`
   - ✅ `depots.read`

**Résultat** : L'utilisateur peut maintenant accéder aux pages de stocks en plus de ses permissions RH.

### Exemple 2 : RH Assistant avec accès aux commandes

**Scénario** : Un RH Assistant doit suivre les commandes pour gérer les affectations de personnel.

**Configuration** :
1. Aller dans `/auth/users/<id>/edit`
2. Dans "Permissions Supplémentaires", cocher :
   - ✅ `orders.read`
   - ✅ `reports.read`

**Résultat** : L'utilisateur peut consulter les commandes et générer des rapports.

### Exemple 3 : RH Analyst avec accès complet aux analytics

**Scénario** : Un RH Analyst doit avoir accès à tous les analytics pour des analyses croisées.

**Configuration** :
1. Aller dans `/auth/users/<id>/edit`
2. Dans "Permissions Supplémentaires", cocher :
   - ✅ `analytics.read`
   - ✅ `analytics.export`
   - ✅ `reports.read`
   - ✅ `reports.export`
   - ✅ `stocks.read`

**Résultat** : L'utilisateur peut accéder à tous les analytics et rapports.

---

## 🔍 VÉRIFICATION DES PERMISSIONS

### Dans le Code Python

```python
from auth import has_permission

# Vérifier si un utilisateur RH a accès au stock
if has_permission(current_user, 'stocks.read'):
    # Afficher les stocks
    pass
```

### Dans les Templates Jinja2

```jinja2
{% if has_permission(current_user, 'stocks.read') %}
  <a href="{{ url_for('stocks.stock_summary') }}">Voir les Stocks</a>
{% endif %}
```

---

## 📊 STRUCTURE DES DONNÉES

### Format JSON dans `additional_permissions`

```json
{
  "stocks": ["read"],
  "orders": ["read", "create"],
  "reports": ["read", "export"]
}
```

### Format dans la Base de Données

La colonne `additional_permissions` est de type `JSON` et stocke un objet avec :
- **Clés** : Noms des modules (ex: `stocks`, `orders`)
- **Valeurs** : Listes d'actions (ex: `["read", "create"]`)

---

## ⚠️ NOTES IMPORTANTES

1. **Permissions Supplémentaires = Permissions Additionnelles**
   - Elles s'ajoutent aux permissions du rôle
   - Elles ne remplacent pas les permissions du rôle
   - Si le rôle a déjà `stocks.read`, l'ajouter en supplémentaire ne change rien

2. **Visibilité de l'Interface**
   - La section "Permissions Supplémentaires" n'apparaît que pour les utilisateurs RH
   - Rôles concernés : `rh`, `rh_manager`, `rh_assistant`, `rh_recruiter`, `rh_analyst`

3. **Permissions du Rôle Admin**
   - Les administrateurs ont automatiquement tous les droits
   - Les permissions supplémentaires ne sont pas nécessaires pour les admins

4. **Sécurité**
   - Seuls les utilisateurs avec `users.update` peuvent modifier les permissions supplémentaires
   - Les permissions sont vérifiées à chaque requête

---

## 🛠️ MAINTENANCE

### Supprimer toutes les permissions supplémentaires d'un utilisateur

```sql
UPDATE users SET additional_permissions = NULL WHERE id = <user_id>;
```

### Voir les permissions supplémentaires d'un utilisateur

```sql
SELECT id, username, additional_permissions 
FROM users 
WHERE additional_permissions IS NOT NULL;
```

---

## ✅ CHECKLIST D'IMPLÉMENTATION

- [x] Colonne `additional_permissions` ajoutée au modèle `User`
- [x] Fonction `has_permission()` mise à jour pour vérifier les permissions supplémentaires
- [x] Interface d'édition utilisateur mise à jour avec section "Permissions Supplémentaires"
- [x] Script SQL de migration créé
- [x] Documentation complète

---

## 📞 SUPPORT

Pour toute question ou problème :
1. Vérifier que la colonne `additional_permissions` existe dans la table `users`
2. Vérifier que l'utilisateur a bien un rôle RH
3. Vérifier les logs d'erreur dans la console
4. Consulter la documentation des permissions dans `/auth/roles`

---

**Dernière mise à jour :** 2025-01-XX

