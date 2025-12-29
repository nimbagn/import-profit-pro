# 🎯 PLAN D'ACTION COMPLET - TRANSFORMATION DU PROJET

**Date :** 24 Octobre 2025  
**Objectif :** Transformer le projet actuel en système complet de gestion de stocks, flotte et rentabilité d'importation

---

## 📊 ÉTAT ACTUEL vs CIBLE

### ✅ Ce qui existe déjà
- ✅ Modèles de base : Category, Article, Simulation, SimulationItem
- ✅ Interface Import Profit Pro (simulations, articles, forecast)
- ✅ Design premium moderne
- ✅ Base Flask + MySQL/SQLite
- ✅ APIs REST de base

### ❌ Ce qui manque (à implémenter)
- ❌ Modèles : Régions, Dépôts, Véhicules, Familles, StockItems
- ❌ Gestion des stocks (Dépôt + Véhicule)
- ❌ Mouvements de stock
- ❌ Inventaires
- ❌ Gestion de flotte (documents, maintenance, odomètre)
- ❌ Système d'authentification et rôles
- ❌ Notifications et alertes
- ❌ Dashboard par rôle

---

## 🗺️ ROADMAP D'IMPLÉMENTATION

### PHASE 1 : FONDATIONS (Semaine 1-2)

#### 1.1 Extension des Modèles de Données
**Priorité : 🔴 HAUTE**

Ajouter dans `models.py` :

```python
# Référentiels
- Region
- Depot  
- Vehicle
- Family
- StockItem
- Role
- User

# Stocks
- DepotStock
- VehicleStock
- StockMovement
- Reception

# Inventaires
- InventorySession
- InventoryDetail

# Flotte
- VehicleDocument
- VehicleMaintenance
- VehicleOdometer
```

**Actions :**
1. Créer tous les modèles manquants
2. Ajouter les relations et contraintes
3. Créer les index nécessaires
4. Tester la création des tables

#### 1.2 Système d'Authentification
**Priorité : 🔴 HAUTE**

**Actions :**
1. Installer Flask-Login
2. Créer système de login/logout
3. Implémenter gestion des sessions
4. Créer middleware de protection des routes
5. Templates login/register

#### 1.3 Système de Rôles (RBAC)
**Priorité : 🔴 HAUTE**

**Actions :**
1. Créer table Role avec permissions JSON
2. Créer table User avec relation Role
3. Décorateurs pour vérifier les permissions
4. Middleware pour masquer actions selon rôle

---

### PHASE 2 : GESTION DES STOCKS (Semaine 3-4)

#### 2.1 Référentiels
**Priorité : 🔴 HAUTE**

**Routes à créer :**
- `/regions` - CRUD Régions
- `/depots` - CRUD Dépôts (avec affectation région)
- `/vehicles` - CRUD Véhicules (avec conducteur, infos)
- `/families` - CRUD Familles
- `/stock-items` - CRUD Articles de stock (SKU, nom, PU, poids)

**Templates :**
- `regions_list.html`, `region_form.html`
- `depots_list.html`, `depot_form.html`
- `vehicles_list.html`, `vehicle_form.html`
- `families_list.html`, `family_form.html`
- `stock_items_list.html`, `stock_item_form.html`

#### 2.2 Gestion des Stocks
**Priorité : 🔴 HAUTE**

**Routes :**
- `/stocks/depot/<id>` - Stock d'un dépôt
- `/stocks/vehicle/<id>` - Stock d'un véhicule
- `/stocks/depot/<id>/low` - Alertes mini-stock dépôt
- `/stocks/vehicle/<id>/low` - Alertes mini-stock véhicule

**Fonctionnalités :**
- Affichage tableau avec seuils colorés
- Filtres et recherche
- Export CSV/Excel

#### 2.3 Mouvements de Stock
**Priorité : 🔴 HAUTE**

**Routes :**
- `/movements` - Liste des mouvements
- `/movements/new` - Créer mouvement
- `/movements/transfer` - Transfert dépôt↔véhicule, véhicule↔véhicule
- `/movements/reception` - Réception en dépôt
- `/movements/adjustment` - Ajustement de stock

**Règles métier :**
- Transaction atomique (décrément source, incrément destination)
- Validation stock suffisant (ou autoriser négatif contrôlé)
- Log dans StockMovement

---

### PHASE 3 : INVENTAIRES (Semaine 5)

#### 3.1 Sessions d'Inventaire
**Priorité : 🟡 MOYENNE**

**Routes :**
- `/inventory/sessions` - Liste des sessions
- `/inventory/sessions/new` - Créer session
- `/inventory/sessions/<id>` - Détails session
- `/inventory/sessions/<id>/validate` - Valider et générer ajustements

**Fonctionnalités :**
- Saisie "piles" (ex: 2x5+3x4)
- Calcul automatique des écarts
- Génération d'ajustements après validation

---

### PHASE 4 : GESTION DE FLOTTE (Semaine 6-7)

#### 4.1 Documents Véhicule
**Priorité : 🟡 MOYENNE**

**Routes :**
- `/vehicles/<id>/documents` - Liste documents
- `/vehicles/<id>/documents/new` - Ajouter document
- `/vehicles/<id>/documents/<doc_id>/edit` - Modifier
- `/vehicles/<id>/documents/<doc_id>/upload` - Upload pièce jointe

**Types de documents :**
- Assurance
- Immatriculation
- Visite technique
- Impôt routier
- Permis
- Autre

**Fonctionnalités :**
- Calcul statut (valid/expiring/expired)
- Alertes J-15/J-7/J0
- Upload fichiers

#### 4.2 Maintenance Véhicule
**Priorité : 🟡 MOYENNE**

**Routes :**
- `/vehicles/<id>/maintenances` - Liste maintenances
- `/vehicles/<id>/maintenances/new` - Planifier maintenance
- `/vehicles/<id>/maintenances/<id>/complete` - Marquer réalisée

**Types :**
- Vidange
- Pneus
- Freins
- Autre

**Fonctionnalités :**
- Planification avec km cible
- Suivi coût GNF
- Alertes maintenances dues

#### 4.3 Odomètre
**Priorité : 🟡 MOYENNE**

**Routes :**
- `/vehicles/<id>/odometer` - Historique relevés
- `/vehicles/<id>/odometer/new` - Nouveau relevé

**Fonctionnalités :**
- Validation km croissant
- Calcul coût/km
- Graphique évolution

---

### PHASE 5 : NOTIFICATIONS & ALERTES (Semaine 8)

#### 5.1 Système d'Alertes
**Priorité : 🟡 MOYENNE**

**Tâches planifiées (CRON/Celery-Beat) :**
- 06:00 - Recalcul statuts documents
- 06:00 - Recalcul maintenances dues
- 06:00 - Calcul mini-stocks
- 07:00 - Envoi récap (Email/WhatsApp)

**Routes :**
- `/alerts/today` - Alertes du jour
- `/alerts/documents` - Documents expirant/expirés
- `/alerts/maintenances` - Maintenances dues
- `/alerts/stocks` - Mini-stocks

**Canaux :**
- Email
- WhatsApp (Message Pro)
- Bannière dashboard

---

### PHASE 6 : DASHBOARDS PAR RÔLE (Semaine 9)

#### 6.1 Dashboard Admin
**Priorité : 🟡 MOYENNE**

**KPI :**
- Total stocks (dépôts + véhicules)
- Écarts inventaire
- Documents expirant
- Maintenances à venir
- Derniers mouvements

#### 6.2 Dashboard Magasinier
**Priorité : 🟡 MOYENNE**

**Raccourcis :**
- Réception
- Transfert
- Inventaire
- Ajustement

#### 6.3 Dashboard Superviseur
**Priorité : 🟡 MOYENNE**

**Vue région :**
- Heatmap stocks
- Tops ruptures
- Alertes régionales

#### 6.4 Dashboard Commercial
**Priorité : 🟡 MOYENNE**

**Vue véhicule :**
- Stock véhicule
- Demande réassort
- Prochain entretien
- Documents à renouveler

---

### PHASE 7 : APIs REST COMPLÈTES (Semaine 10)

#### 7.1 Endpoints à créer
**Priorité : 🟢 BASSE**

```
/api/auth/login
/api/users
/api/roles
/api/regions
/api/depots
/api/vehicles
/api/catalog/families
/api/catalog/items
/api/catalog/articles
/api/catalog/categories
/api/stocks/depots/:id
/api/stocks/vehicles/:id
/api/movements (POST: transfer/reception/adjustment)
/api/inventory/sessions
/api/inventory/:session_id/details
/api/inventory/:session_id/validate
/api/vehicle/documents
/api/vehicle/maintenances
/api/vehicle/odometers
/api/simulations/:id/compute
/api/alerts/today
```

**Fonctionnalités :**
- Pagination
- Filtres (region_id, depot_id, date_from/to)
- Auth JWT (phase 2)

---

### PHASE 8 : AMÉLIORATIONS (Semaine 11-12)

#### 8.1 Migrations Alembic
**Priorité : 🟡 MOYENNE**

**Actions :**
1. Initialiser Alembic
2. Créer migration initiale
3. Remplacer `db.create_all()` par migrations
4. Scripts de migration pour prod

#### 8.2 Tests
**Priorité : 🟡 MOYENNE**

**Tests unitaires :**
- Utils (parsing piles, calculs)
- Règles métier (transferts, inventaires)
- Calcul statut documents

**Tests d'intégration :**
- Endpoints mouvements
- Réceptions
- Inventaires
- Gestion erreurs

#### 8.3 Exports
**Priorité : 🟢 BASSE**

- CSV/Excel (inventaires, mouvements, simulations)
- PDF rapports

---

## 📋 CHECKLIST D'IMPLÉMENTATION

### Modèles de Données
- [ ] Region
- [ ] Depot
- [ ] Vehicle
- [ ] Family
- [ ] StockItem
- [ ] DepotStock
- [ ] VehicleStock
- [ ] StockMovement
- [ ] Reception
- [ ] InventorySession
- [ ] InventoryDetail
- [ ] VehicleDocument
- [ ] VehicleMaintenance
- [ ] VehicleOdometer
- [ ] Role
- [ ] User

### Authentification & Sécurité
- [ ] Flask-Login installé
- [ ] Système de login/logout
- [ ] Protection des routes
- [ ] Gestion des sessions
- [ ] RBAC avec permissions

### Routes & Templates
- [ ] Routes référentiels (régions, dépôts, véhicules, familles, stock-items)
- [ ] Routes stocks (dépôt, véhicule)
- [ ] Routes mouvements (transfert, réception, ajustement)
- [ ] Routes inventaires
- [ ] Routes flotte (documents, maintenance, odomètre)
- [ ] Routes alertes
- [ ] Templates pour toutes les routes

### Fonctionnalités Métier
- [ ] Calcul statut documents
- [ ] Alertes mini-stock
- [ ] Parsing piles inventaire
- [ ] Calcul écarts inventaire
- [ ] Génération ajustements
- [ ] Validation km odomètre

### APIs REST
- [ ] Tous les endpoints listés
- [ ] Pagination
- [ ] Filtres
- [ ] Format JSON standardisé

### Dashboards
- [ ] Dashboard Admin
- [ ] Dashboard Magasinier
- [ ] Dashboard Superviseur
- [ ] Dashboard Commercial

### DevOps
- [ ] Alembic migrations
- [ ] Tâches planifiées (CRON/Celery)
- [ ] Logging structuré
- [ ] Variables d'environnement (.env)

### Tests
- [ ] Tests unitaires
- [ ] Tests d'intégration
- [ ] Tests E2E

---

## 🚀 PROCHAINES ACTIONS IMMÉDIATES

### Action 1 : Extension des Modèles (PRIORITÉ 1)
**Fichier :** `models.py`

Créer tous les modèles manquants avec :
- BIGINT UNSIGNED pour PK/FK
- Contraintes d'unicité
- Index nécessaires
- Relations SQLAlchemy

### Action 2 : Système d'Authentification (PRIORITÉ 1)
**Fichiers :** `auth.py`, templates `login.html`, `register.html`

- Installer Flask-Login
- Créer User model avec password hash
- Routes login/logout
- Protection des routes

### Action 3 : Routes Référentiels (PRIORITÉ 2)
**Fichier :** `app.py`

Créer routes CRUD pour :
- Régions
- Dépôts
- Véhicules
- Familles
- StockItems

### Action 4 : Gestion des Stocks (PRIORITÉ 2)
**Fichier :** `app.py`

Créer routes et logique pour :
- Affichage stocks dépôt/véhicule
- Mouvements de stock
- Validation règles métier

---

## 📊 ESTIMATION

### Temps Total Estimé
- **Phase 1 (Fondations) :** 2 semaines
- **Phase 2 (Stocks) :** 2 semaines
- **Phase 3 (Inventaires) :** 1 semaine
- **Phase 4 (Flotte) :** 2 semaines
- **Phase 5 (Alertes) :** 1 semaine
- **Phase 6 (Dashboards) :** 1 semaine
- **Phase 7 (APIs) :** 1 semaine
- **Phase 8 (Améliorations) :** 2 semaines

**Total :** 12 semaines (3 mois)

### Ressources Nécessaires
- 1 développeur full-stack
- Accès MySQL 8
- Serveur de développement
- Outils : Git, Alembic, Celery (optionnel)

---

## ✅ VALIDATION

### Critères de Succès Phase 1
- [ ] Tous les modèles créés et testés
- [ ] Authentification fonctionnelle
- [ ] RBAC opérationnel
- [ ] Base de données migrée

### Critères de Succès Phase 2
- [ ] CRUD référentiels complet
- [ ] Gestion stocks dépôt/véhicule
- [ ] Mouvements fonctionnels
- [ ] Validation règles métier

### Critères de Succès Global
- [ ] Toutes les fonctionnalités cibles implémentées
- [ ] Tests > 80% coverage
- [ ] Documentation complète
- [ ] Déploiement production réussi

---

**📅 Prochaine révision :** Après Phase 1  
**👨‍💻 Responsable :** Équipe de développement  
**🎯 Objectif :** Système complet opérationnel en 3 mois

