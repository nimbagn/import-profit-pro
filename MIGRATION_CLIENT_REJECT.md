# Migration - Rejet de Clients Individuels

**Date**: 21 Décembre 2025

---

## ✅ MODIFICATIONS APPLIQUÉES

### 1. Modèle de Données (`models.py`)

#### Ajout de champs à `CommercialOrderClient` :
- ✅ `status` : Enum('pending', 'approved', 'rejected') - Statut du client dans la commande
- ✅ `rejection_reason` : Text - Raison du rejet du client
- ✅ `rejected_by_id` : FK vers User - Utilisateur qui a rejeté le client
- ✅ `rejected_at` : DateTime - Date de rejet
- ✅ Relation `rejected_by` vers User

### 2. Routes Backend (`orders.py`)

#### Nouvelle route : `client_reject`
- ✅ Route : `POST /orders/<order_id>/client/<client_id>/reject`
- ✅ Permission : `orders.validate`
- ✅ Validation : Commande doit être `pending_validation` ou `validated`
- ✅ Action : Met le statut du client à `rejected` et enregistre la raison

#### Nouvelle route : `client_approve`
- ✅ Route : `POST /orders/<order_id>/client/<client_id>/approve`
- ✅ Permission : `orders.validate`
- ✅ Validation : Commande doit être `pending_validation` ou `validated`
- ✅ Action : Met le statut du client à `approved` et efface les données de rejet

#### Modification de `order_detail`
- ✅ Ajout du `joinedload` pour `rejected_by` pour optimiser les requêtes

### 3. Template (`templates/orders/order_detail.html`)

#### Affichage du Statut
- ✅ Badge de statut pour chaque client :
  - **En attente** : Badge orange
  - **Approuvé** : Badge vert
  - **Rejeté** : Badge rouge

#### Affichage Visuel
- ✅ Clients rejetés : Opacité réduite, bordure rouge, fond rouge clair
- ✅ Clients approuvés : Bordure verte, fond vert clair
- ✅ Total barré pour les clients rejetés

#### Raison du Rejet
- ✅ Affichage de la raison du rejet si le client est rejeté
- ✅ Affichage de qui a rejeté et quand

#### Actions
- ✅ Formulaire pour rejeter un client (si pas déjà rejeté)
- ✅ Formulaire pour approuver un client rejeté
- ✅ Actions disponibles uniquement si :
  - Commande en `pending_validation` ou `validated`
  - Utilisateur a la permission `orders.validate`

#### Calcul du Total
- ✅ Exclusion des clients rejetés du calcul du total global
- ✅ Total par client toujours affiché mais barré si rejeté

---

## 📋 MIGRATION BASE DE DONNÉES

### Script SQL à exécuter :

```sql
-- Ajouter les colonnes pour le rejet de clients
ALTER TABLE `commercial_order_clients` 
ADD COLUMN `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending' AFTER `comments`,
ADD COLUMN `rejection_reason` TEXT NULL AFTER `status`,
ADD COLUMN `rejected_by_id` BIGINT UNSIGNED NULL AFTER `rejection_reason`,
ADD COLUMN `rejected_at` DATETIME NULL AFTER `rejected_by_id`,
ADD INDEX `idx_orderclient_status` (`status`),
ADD CONSTRAINT `fk_orderclient_rejected_by` FOREIGN KEY (`rejected_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL;
```

---

## 🎯 FONCTIONNALITÉS

### Pour les Superviseurs/Admins
- ✅ Rejeter un client individuel dans une commande
- ✅ Approuver un client rejeté
- ✅ Voir la raison du rejet et qui l'a rejeté
- ✅ Les clients rejetés sont exclus du total global

### Affichage
- ✅ Statut visuel clair pour chaque client
- ✅ Raison du rejet affichée
- ✅ Total global exclut les clients rejetés
- ✅ Design cohérent avec le reste de l'application

---

## ✅ TESTS À EFFECTUER

### Test 1 : Rejet d'un Client
1. Ouvrir une commande en `pending_validation` ou `validated`
2. Cliquer sur "Rejeter ce client" pour un client
3. Entrer une raison de rejet
4. Vérifier que le client est marqué comme rejeté
5. Vérifier que le total global exclut ce client

### Test 2 : Approbation d'un Client Rejeté
1. Ouvrir une commande avec un client rejeté
2. Cliquer sur "Approuver ce client"
3. Vérifier que le client est marqué comme approuvé
4. Vérifier que le total global inclut maintenant ce client

### Test 3 : Calcul du Total
1. Créer une commande avec plusieurs clients
2. Rejeter un client
3. Vérifier que le total global exclut le client rejeté
4. Approuver le client rejeté
5. Vérifier que le total global inclut maintenant ce client

### Test 4 : Permissions
1. Se connecter en tant que commercial
2. Vérifier que les boutons de rejet/approuver ne sont pas visibles
3. Se connecter en tant que superviseur/admin
4. Vérifier que les boutons sont visibles

---

## 📝 NOTES

- Les clients sont créés avec le statut `pending` par défaut
- Seuls les superviseurs/admins peuvent rejeter/approuver des clients
- Le rejet d'un client n'affecte pas le statut de la commande globale
- Le total global exclut automatiquement les clients rejetés
- Un client rejeté peut être approuvé ultérieurement

---

**✅ Toutes les modifications sont appliquées !**

**⚠️ IMPORTANT : Exécuter le script SQL de migration avant d'utiliser cette fonctionnalité !**

