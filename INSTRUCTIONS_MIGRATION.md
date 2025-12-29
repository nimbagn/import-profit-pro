# Instructions pour Exécuter la Migration

**Date**: 24 Décembre 2025

---

## ⚠️ ERREUR DÉTECTÉE

L'erreur suivante apparaît :
```
Unknown column 'commercial_order_clients_1.rejection_reason' in 'field list'
```

Cela signifie que les colonnes pour le rejet de clients individuels n'ont pas encore été créées dans la base de données.

---

## ✅ SOLUTION : EXÉCUTER LA MIGRATION

### Option 1 : Script Python (Recommandé)

Exécutez le script de migration :

```bash
python3 migrate_client_rejection.py
```

Ce script va :
- ✅ Vérifier si les colonnes existent déjà
- ✅ Ajouter les colonnes manquantes
- ✅ Créer les index nécessaires
- ✅ Ajouter les contraintes de clé étrangère

### Option 2 : SQL Direct

Si vous préférez exécuter le SQL directement :

```bash
mysql -u votre_user -p votre_database < migrations/add_client_rejection_fields.sql
```

Ou via MySQL :

```sql
USE votre_database;

ALTER TABLE commercial_order_clients 
ADD COLUMN status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending' AFTER comments;

ALTER TABLE commercial_order_clients 
ADD COLUMN rejection_reason TEXT NULL AFTER status;

ALTER TABLE commercial_order_clients 
ADD COLUMN rejected_by_id BIGINT UNSIGNED NULL AFTER rejection_reason;

ALTER TABLE commercial_order_clients 
ADD COLUMN rejected_at DATETIME NULL AFTER rejected_by_id;

ALTER TABLE commercial_order_clients 
ADD INDEX idx_orderclient_status (status);

ALTER TABLE commercial_order_clients 
ADD CONSTRAINT fk_orderclient_rejected_by 
FOREIGN KEY (rejected_by_id) REFERENCES users (id) 
ON UPDATE CASCADE ON DELETE SET NULL;
```

---

## 🔄 APRÈS LA MIGRATION

Une fois la migration exécutée :

1. ✅ Redémarrez le serveur Flask si nécessaire
2. ✅ Accédez à http://localhost:5002/orders/3
3. ✅ Vous devriez voir les boutons pour rejeter/approuver des clients individuels
4. ✅ Les colonnes seront disponibles et l'erreur disparaîtra

---

## 📋 COLONNES AJOUTÉES

- `status` : Statut du client (pending, approved, rejected)
- `rejection_reason` : Raison du rejet
- `rejected_by_id` : ID de l'utilisateur qui a rejeté
- `rejected_at` : Date/heure du rejet

---

**⚠️ IMPORTANT : Exécutez la migration avant d'utiliser la fonctionnalité !**

