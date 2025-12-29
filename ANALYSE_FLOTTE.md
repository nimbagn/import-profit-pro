# 🚗 ANALYSE DE LA SECTION FLOTTE - FONCTIONNALITÉS POSSIBLES

**Date :** 19 Novembre 2025  
**Statut :** 📊 **ANALYSE COMPLÈTE**

---

## 📋 ÉTAT ACTUEL DE LA FLOTTE

### ✅ Fonctionnalités Existantes

#### 1. **Gestion de Base des Véhicules** (`referentiels.py`)
- ✅ Liste des véhicules avec statut (actif, inactif, maintenance)
- ✅ Création de véhicule (immatriculation, marque, modèle, année, couleur, VIN)
- ✅ Modification des informations véhicule
- ✅ Assignation de conducteur (current_user_id)
- ✅ Gestion du statut (active, inactive, maintenance)
- ✅ WhatsApp du véhicule

#### 2. **Documents Véhicule** (`flotte.py`)
- ✅ Types de documents : Assurance, Carte grise, Contrôle technique, Taxe route, Permis, Autre
- ✅ Suivi des dates d'expiration
- ✅ Alertes pour documents expirés ou expirant bientôt (≤15 jours)
- ✅ Création, modification de documents
- ✅ Numéro de document, dates d'émission et d'expiration

#### 3. **Maintenances** (`flotte.py`)
- ✅ Planification de maintenances (vidange, pneus, freins, etc.)
- ✅ Suivi par date ou kilométrage
- ✅ Statut : planifiée, réalisée, annulée
- ✅ Coût des maintenances
- ✅ Alertes pour maintenances dues

#### 4. **Odomètre** (`flotte.py`)
- ✅ Relevés kilométriques avec date
- ✅ Sources : manuel, GPS, système
- ✅ Vérification de cohérence (pas de kilométrage en arrière)
- ✅ Historique des relevés

#### 5. **Stock par Véhicule** (`stocks.py`)
- ✅ Gestion du stock dans chaque véhicule
- ✅ Mouvements de stock vers/depuis véhicules
- ✅ Alertes stock faible par véhicule

---

## 🎯 FONCTIONNALITÉS POSSIBLES À AJOUTER

### 1. **DASHBOARD FLOTTE** 📊
**Objectif :** Vue d'ensemble de la flotte avec indicateurs clés

**Fonctionnalités :**
- **Statistiques globales :**
  - Nombre total de véhicules (actifs, inactifs, en maintenance)
  - Taux de disponibilité de la flotte
  - Nombre de véhicules sans conducteur assigné
  - Kilométrage total parcouru (période)
  
- **Alertes centralisées :**
  - Documents expirés/expirant bientôt (tous véhicules)
  - Maintenances dues (par date ou kilométrage)
  - Véhicules sans documents obligatoires
  - Véhicules en maintenance depuis X jours
  
- **Graphiques :**
  - Évolution du kilométrage par véhicule
  - Coûts de maintenance par véhicule
  - Répartition des statuts
  - Consommation moyenne (si carburant suivi)

**Route proposée :** `/vehicles/dashboard`

---

### 2. **GESTION DES COÛTS ET BUDGETS** 💰
**Objectif :** Suivi financier complet de la flotte

**Fonctionnalités :**
- **Coûts par catégorie :**
  - Carburant (si suivi)
  - Maintenances (déjà partiellement)
  - Assurances et documents
  - Réparations
  - Pneus
  - Autres frais
  
- **Budgets :**
  - Budget annuel par véhicule
  - Budget par catégorie de coût
  - Suivi des dépassements
  
- **Rapports financiers :**
  - Coût total par véhicule
  - Coût au kilomètre
  - Comparaison entre véhicules
  - Évolution des coûts dans le temps

**Tables à créer :**
- `vehicle_costs` (type, montant, date, véhicule, notes)
- `vehicle_budgets` (année, véhicule, catégorie, montant)

**Routes proposées :**
- `/vehicles/<id>/costs` - Liste des coûts
- `/vehicles/<id>/costs/new` - Ajouter un coût
- `/vehicles/budgets` - Gestion des budgets

---

### 3. **HISTORIQUE DES CONDUCTEURS** 👤
**Objectif :** Traçabilité complète des assignations

**Fonctionnalités :**
- **Historique des assignations :**
  - Qui a conduit quel véhicule et quand
  - Durée d'assignation
  - Raison du changement
  
- **Statistiques par conducteur :**
  - Nombre de véhicules assignés
  - Kilométrage total parcouru
  - Incidents/accidents (si suivi)
  
- **Alertes :**
  - Conducteur sans véhicule assigné
  - Véhicule sans conducteur

**Table à créer :**
- `vehicle_assignments` (véhicule, conducteur, date_début, date_fin, raison, notes)

**Routes proposées :**
- `/vehicles/<id>/assignments` - Historique des assignations
- `/vehicles/<id>/assignments/new` - Nouvelle assignation
- `/users/<id>/vehicles` - Véhicules assignés à un utilisateur

---

### 4. **GESTION DES PNEUS** 🛞
**Objectif :** Suivi détaillé des pneus par véhicule

**Fonctionnalités :**
- **Inventaire des pneus :**
  - Nombre de pneus par véhicule
  - Marque, modèle, dimension
  - Date d'installation
  - Kilométrage d'installation
  - État (neuf, usé, à changer)
  
- **Rotation des pneus :**
  - Planification des rotations
  - Historique des rotations
  - Kilométrage par position
  
- **Alertes :**
  - Pneus à changer (usure ou kilométrage)
  - Rotation due

**Table à créer :**
- `vehicle_tires` (véhicule, position, marque, modèle, dimension, date_installation, km_installation, état)
- `tire_rotations` (véhicule, date, pneus_avant, pneus_arrière, km)

**Routes proposées :**
- `/vehicles/<id>/tires` - Gestion des pneus
- `/vehicles/<id>/tires/new` - Ajouter pneu
- `/vehicles/<id>/tires/rotate` - Rotation des pneus

---

### 5. **SUIVI CARBURANT** ⛽
**Objectif :** Consommation et coûts de carburant

**Fonctionnalités :**
- **Relevés de carburant :**
  - Date, quantité (litres), prix unitaire, montant total
  - Kilométrage au moment du plein
  - Type de carburant
  - Station-service
  
- **Calculs automatiques :**
  - Consommation (L/100km)
  - Coût au kilomètre
  - Évolution de la consommation
  - Comparaison entre véhicules
  
- **Alertes :**
  - Consommation anormale (augmentation soudaine)
  - Plein manquant (véhicule actif sans plein récent)

**Table à créer :**
- `vehicle_fuel` (véhicule, date, quantité_litres, prix_unitaire, montant_total, km_au_plein, type_carburant, station, notes)

**Routes proposées :**
- `/vehicles/<id>/fuel` - Historique carburant
- `/vehicles/<id>/fuel/new` - Nouveau plein
- `/vehicles/fuel/consumption` - Rapport consommation

---

### 6. **GÉOLOCALISATION / TRACKING** 📍
**Objectif :** Suivi de la position des véhicules (si GPS disponible)

**Fonctionnalités :**
- **Position actuelle :**
  - Dernière position connue
  - Date/heure du dernier signal
  - Vitesse actuelle (si disponible)
  
- **Historique des trajets :**
  - Trajets par jour
  - Carte des déplacements
  - Temps d'arrêt
  
- **Zones géographiques :**
  - Définition de zones (géofencing)
  - Alertes entrée/sortie de zone
  - Temps passé dans chaque zone

**Table à créer :**
- `vehicle_locations` (véhicule, latitude, longitude, date_heure, vitesse, direction, précision)

**Routes proposées :**
- `/vehicles/<id>/location` - Position actuelle
- `/vehicles/<id>/routes` - Historique des trajets
- `/vehicles/map` - Carte de tous les véhicules

---

### 7. **RAPPORTS ET ANALYTICS** 📈
**Objectif :** Analyses approfondies de la flotte

**Fonctionnalités :**
- **Rapports prédéfinis :**
  - Rapport mensuel par véhicule
  - Coûts totaux par période
  - Kilométrage par conducteur
  - Maintenances préventives réalisées
  - Documents à renouveler
  
- **Graphiques interactifs :**
  - Évolution des coûts
  - Kilométrage cumulé
  - Consommation de carburant
  - Fréquence des maintenances
  
- **Export :**
  - PDF des rapports
  - Excel pour analyses externes
  - CSV pour import dans autres outils

**Routes proposées :**
- `/vehicles/reports` - Liste des rapports
- `/vehicles/reports/monthly` - Rapport mensuel
- `/vehicles/reports/costs` - Rapport coûts
- `/vehicles/reports/export` - Export données

---

### 8. **PLANIFICATION MAINTENANCES PRÉVENTIVES** 🔧
**Objectif :** Automatisation des maintenances récurrentes

**Fonctionnalités :**
- **Templates de maintenance :**
  - Types de maintenance récurrente (vidange 5000km, révision 20000km, etc.)
  - Fréquence (kilométrage ou temps)
  - Coût estimé
  
- **Génération automatique :**
  - Création automatique de maintenances planifiées
  - Basée sur le kilométrage actuel
  - Alertes pour maintenances à venir
  
- **Historique :**
  - Toutes les maintenances réalisées
  - Prochaine maintenance prévue
  - Coûts réels vs estimés

**Table à créer :**
- `maintenance_templates` (type, fréquence_km, fréquence_days, coût_estimé, description)

**Routes proposées :**
- `/vehicles/maintenances/templates` - Templates
- `/vehicles/<id>/maintenances/auto-schedule` - Planification auto

---

### 9. **GESTION DES INCIDENTS / ACCIDENTS** ⚠️
**Objectif :** Suivi des incidents et accidents

**Fonctionnalités :**
- **Enregistrement d'incidents :**
  - Date, heure, lieu
  - Type (accident, panne, vol, etc.)
  - Description détaillée
  - Conducteur au moment de l'incident
  - Photos/documents
  
- **Suivi :**
  - Statut (signalé, en cours, résolu)
  - Coûts associés
  - Actions correctives
  
- **Statistiques :**
  - Nombre d'incidents par véhicule
  - Par conducteur
  - Par type d'incident

**Table à créer :**
- `vehicle_incidents` (véhicule, date_heure, type, description, conducteur_id, lieu, statut, coût, photos_urls, notes)

**Routes proposées :**
- `/vehicles/<id>/incidents` - Liste des incidents
- `/vehicles/<id>/incidents/new` - Nouvel incident
- `/vehicles/incidents/report` - Rapport incidents

---

### 10. **FICHE VÉHICULE COMPLÈTE** 📄
**Objectif :** Vue détaillée de tous les aspects d'un véhicule

**Fonctionnalités :**
- **Onglets organisés :**
  - Informations générales
  - Documents (avec alertes visuelles)
  - Maintenances (planifiées et réalisées)
  - Odomètre (graphique d'évolution)
  - Stock dans le véhicule
  - Coûts et budgets
  - Historique des conducteurs
  - Pneus
  - Carburant (si suivi)
  - Incidents
  
- **Résumé en haut :**
  - Statut actuel
  - Conducteur actuel
  - Kilométrage actuel
  - Alertes actives
  - Coûts du mois

**Route proposée :**
- `/vehicles/<id>` - Fiche complète du véhicule

---

### 11. **ALERTES ET NOTIFICATIONS** 🔔
**Objectif :** Système d'alertes automatiques

**Fonctionnalités :**
- **Types d'alertes :**
  - Documents expirant (7, 15, 30 jours)
  - Maintenances dues
  - Véhicule sans conducteur
  - Kilométrage anormal
  - Consommation anormale
  - Pneus à changer
  
- **Configuration :**
  - Seuils personnalisables
  - Destinataires des alertes (email, notification in-app)
  - Fréquence des rappels
  
- **Tableau de bord des alertes :**
  - Toutes les alertes actives
  - Par priorité
  - Par véhicule

**Table à créer :**
- `vehicle_alerts` (véhicule, type_alerte, message, priorité, date_creation, statut, résolu_le)

**Routes proposées :**
- `/vehicles/alerts` - Toutes les alertes
- `/vehicles/alerts/settings` - Configuration alertes

---

### 12. **INTÉGRATION AVEC STOCKS** 📦
**Objectif :** Améliorer le lien entre flotte et stocks

**Fonctionnalités :**
- **Vue stock par véhicule :**
  - Liste complète des articles en stock
  - Valeur du stock
  - Articles à réapprovisionner
  
- **Mouvements liés :**
  - Historique des mouvements de stock pour ce véhicule
  - Entrées/sorties
  - Transferts vers/depuis dépôts
  
- **Rapport de chargement :**
  - Liste des articles chargés dans le véhicule
  - Par date
  - Par mission/route

**Routes proposées :**
- `/vehicles/<id>/stock` - Stock du véhicule (existe déjà)
- `/vehicles/<id>/stock/movements` - Mouvements de stock
- `/vehicles/<id>/stock/loading-report` - Rapport de chargement

---

## 🎯 PRIORISATION DES FONCTIONNALITÉS

### 🔴 **PRIORITÉ HAUTE** (Essentiel)
1. **Dashboard Flotte** - Vue d'ensemble indispensable
2. **Fiche Véhicule Complète** - Centraliser toutes les infos
3. **Alertes et Notifications** - Prévenir les problèmes
4. **Historique des Conducteurs** - Traçabilité importante

### 🟡 **PRIORITÉ MOYENNE** (Important)
5. **Gestion des Coûts** - Suivi financier
6. **Rapports et Analytics** - Analyses et décisions
7. **Planification Maintenances Préventives** - Automatisation
8. **Gestion des Pneus** - Suivi détaillé

### 🟢 **PRIORITÉ BASSE** (Amélioration)
9. **Suivi Carburant** - Si besoin de suivi détaillé
10. **Géolocalisation** - Si GPS disponible
11. **Gestion des Incidents** - Si besoin de traçabilité incidents

---

## 📊 STRUCTURE DE DONNÉES PROPOSÉE

### Tables à Ajouter

```sql
-- Historique des assignations
CREATE TABLE vehicle_assignments (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    reason VARCHAR(255),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Coûts véhicule
CREATE TABLE vehicle_costs (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    cost_type ENUM('fuel', 'maintenance', 'insurance', 'repair', 'tire', 'other'),
    amount DECIMAL(18,2) NOT NULL,
    cost_date DATE NOT NULL,
    description VARCHAR(255),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Budgets
CREATE TABLE vehicle_budgets (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    year INT NOT NULL,
    category ENUM('fuel', 'maintenance', 'insurance', 'repair', 'tire', 'other', 'total'),
    budget_amount DECIMAL(18,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Pneus
CREATE TABLE vehicle_tires (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    position ENUM('front_left', 'front_right', 'rear_left', 'rear_right', 'spare'),
    brand VARCHAR(50),
    model VARCHAR(50),
    dimension VARCHAR(20),
    installation_date DATE NOT NULL,
    installation_km INT NOT NULL,
    condition ENUM('new', 'good', 'worn', 'replace'),
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Carburant
CREATE TABLE vehicle_fuel (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    fuel_date DATE NOT NULL,
    quantity_liters DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(18,2) NOT NULL,
    odometer_km INT NOT NULL,
    fuel_type ENUM('gasoline', 'diesel', 'electric'),
    station_name VARCHAR(255),
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Incidents
CREATE TABLE vehicle_incidents (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    incident_date DATETIME NOT NULL,
    incident_type ENUM('accident', 'breakdown', 'theft', 'vandalism', 'other'),
    location VARCHAR(255),
    description TEXT NOT NULL,
    driver_id BIGINT UNSIGNED,
    status ENUM('reported', 'in_progress', 'resolved', 'closed'),
    cost DECIMAL(18,2),
    photos_urls JSON,
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (driver_id) REFERENCES users(id)
);

-- Alertes
CREATE TABLE vehicle_alerts (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    vehicle_id BIGINT UNSIGNED NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical'),
    status ENUM('active', 'acknowledged', 'resolved'),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);
```

---

## 🚀 PLAN D'IMPLÉMENTATION RECOMMANDÉ

### Phase 1 : Fondations (Semaine 1)
1. ✅ Dashboard Flotte avec statistiques de base
2. ✅ Fiche Véhicule Complète (onglets)
3. ✅ Système d'alertes basique

### Phase 2 : Traçabilité (Semaine 2)
4. ✅ Historique des conducteurs
5. ✅ Amélioration du suivi des maintenances
6. ✅ Rapports de base

### Phase 3 : Financier (Semaine 3)
7. ✅ Gestion des coûts
8. ✅ Budgets
9. ✅ Rapports financiers

### Phase 4 : Optimisation (Semaine 4)
10. ✅ Gestion des pneus
11. ✅ Planification automatique des maintenances
12. ✅ Suivi carburant (optionnel)

---

## 💡 RECOMMANDATIONS

1. **Commencer par le Dashboard** - Donne une vue d'ensemble immédiate
2. **Centraliser dans la Fiche Véhicule** - Toutes les infos au même endroit
3. **Automatiser les alertes** - Réduit les oublis
4. **Traçabilité complète** - Important pour la conformité
5. **Rapports exportables** - Utile pour la comptabilité

---

**Prochaine étape :** Implémenter les fonctionnalités prioritaires selon vos besoins spécifiques.

