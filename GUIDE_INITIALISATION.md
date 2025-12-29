# 🚀 Guide d'Initialisation Complète de la Base de Données

## 📋 Vue d'ensemble

Le script `INITIALISATION_COMPLETE.sql` crée **toutes les tables** nécessaires pour toutes les fonctionnalités du projet et initialise l'utilisateur admin.

## ⚠️ ATTENTION

**Ce script va SUPPRIMER toutes les données existantes** et recréer la base de données de zéro.

## 📦 Fonctionnalités incluses

### ✅ Tables créées (21 tables)

1. **Authentification**
   - `roles` - Rôles avec permissions JSON
   - `users` - Utilisateurs avec hash password

2. **Import Profit**
   - `categories` - Catégories d'articles
   - `articles` - Articles d'import
   - `simulations` - Simulations de rentabilité
   - `simulation_items` - Items de simulation

3. **Référentiels**
   - `regions` - Régions géographiques
   - `depots` - Dépôts physiques
   - `vehicles` - Véhicules de la flotte
   - `families` - Familles d'articles
   - `stock_items` - Articles de stock (SKU)

4. **Stocks**
   - `depot_stocks` - Stock par dépôt
   - `vehicle_stocks` - Stock par véhicule
   - `stock_movements` - Mouvements de stock
   - `receptions` - Réceptions en dépôt
   - `reception_details` - Détails de réception
   - `stock_outgoings` - Sorties de stock
   - `stock_outgoing_details` - Détails de sortie
   - `stock_returns` - Retours de stock
   - `stock_return_details` - Détails de retour

5. **Inventaires**
   - `inventory_sessions` - Sessions d'inventaire
   - `inventory_details` - Détails d'inventaire

6. **Flotte**
   - `vehicle_documents` - Documents véhicule
   - `vehicle_maintenances` - Maintenances
   - `vehicle_odometers` - Relevés odomètre

## 🎯 Utilisation

### Option 1 : Exécution directe (Recommandé)

```bash
mysql -u root -p madargn < INITIALISATION_COMPLETE.sql
```

### Option 2 : Exécution dans MySQL

```bash
mysql -u root -p
```

Puis dans MySQL :

```sql
USE madargn;
SOURCE /Users/dantawi/Documents/mini_flask_import_profitability/INITIALISATION_COMPLETE.sql;
```

### Option 3 : Copier-coller dans MySQL Workbench

1. Ouvrez MySQL Workbench
2. Connectez-vous à votre base `madargn`
3. Ouvrez le fichier `INITIALISATION_COMPLETE.sql`
4. Exécutez le script complet

## ✅ Données initialisées

### Rôles créés
- **Administrateur** (`admin`) - Accès complet
- **Magasinier** (`warehouse`) - Gestion stocks et inventaires
- **Commercial** (`commercial`) - Consultation et simulations
- **Superviseur** (`supervisor`) - Suivi et validation

### Utilisateur admin créé
- **Username** : `admin`
- **Password** : `admin123`
- **Email** : `admin@importprofit.pro`
- **Rôle** : Administrateur

### Catégories créées
- Électronique
- Informatique
- Textile
- Chaussures
- Maroquinerie
- Électroménager
- Mobilier
- Autre

### Articles de démonstration
- Smartphone Samsung Galaxy S24
- Ordinateur Portable Dell XPS
- Vêtements Importés Premium
- Chaussures Nike Air Max

## 🔍 Vérification après exécution

Le script affiche automatiquement :
- ✅ Nombre de rôles créés
- ✅ Nombre d'utilisateurs créés
- ✅ Nombre de catégories créées
- ✅ Nombre d'articles créés
- ✅ Détails de l'utilisateur admin

## 🚀 Après l'initialisation

1. **Redémarrez Flask** (si déjà lancé) :
   ```bash
   pkill -f "python.*app.py"
   python3 app.py
   ```

2. **Connectez-vous** :
   - URL : http://localhost:5002/auth/login
   - Username : `admin`
   - Password : `admin123`

3. **Vérifiez les logs Flask** :
   Vous devriez voir :
   ```
   ✅ Base de données connectée
   ✅ Rôles initialisés
   ✅ Utilisateur admin créé
   ```

## 🛠️ En cas de problème

### Erreur : "Access denied"
Vérifiez vos identifiants MySQL dans `config.py`

### Erreur : "Table already exists"
Le script supprime d'abord toutes les tables. Si l'erreur persiste :
```sql
SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE madargn;
CREATE DATABASE madargn;
SET FOREIGN_KEY_CHECKS = 1;
```
Puis réexécutez le script.

### Erreur : "Duplicate entry"
L'utilisateur admin existe déjà. Le script le recrée automatiquement.

## 📊 Structure complète

Le script crée **595 lignes** de SQL avec :
- ✅ Toutes les contraintes de clés étrangères
- ✅ Tous les index pour les performances
- ✅ Toutes les contraintes d'unicité
- ✅ Tous les types ENUM
- ✅ Tous les champs avec valeurs par défaut

## 🎉 Résultat attendu

Après exécution, vous aurez :
- ✅ Base de données complètement initialisée
- ✅ Utilisateur admin fonctionnel
- ✅ Toutes les tables prêtes pour l'application
- ✅ Données de démonstration pour tester

---

**Prêt à initialiser ?** Exécutez :
```bash
mysql -u root -p madargn < INITIALISATION_COMPLETE.sql
```

