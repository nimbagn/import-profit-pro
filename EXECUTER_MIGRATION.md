# ⚠️ MIGRATION REQUISE - Rejet de Clients Individuels

**Date**: 24 Décembre 2025

---

## 🔴 ERREUR ACTUELLE

```
Unknown column 'commercial_order_clients_1.rejection_reason' in 'field list'
```

Cette erreur apparaît car les colonnes pour le rejet de clients individuels n'ont pas encore été créées dans la base de données MySQL.

---

## ✅ SOLUTION : EXÉCUTER LA MIGRATION SQL

### Méthode 1 : Via MySQL en ligne de commande

```bash
mysql -u root -p madargn < migrations/add_client_rejection_fields.sql
```

### Méthode 2 : Via MySQL directement

Connectez-vous à MySQL :

```bash
mysql -u root -p madargn
```

Puis exécutez ces commandes SQL une par une :

```sql
-- 1. Ajouter la colonne status
ALTER TABLE commercial_order_clients 
ADD COLUMN status ENUM('pending', 'approved', 'rejected') 
NOT NULL DEFAULT 'pending' 
AFTER comments;

-- 2. Ajouter la colonne rejection_reason
ALTER TABLE commercial_order_clients 
ADD COLUMN rejection_reason TEXT NULL 
AFTER status;

-- 3. Ajouter la colonne rejected_by_id
ALTER TABLE commercial_order_clients 
ADD COLUMN rejected_by_id BIGINT UNSIGNED NULL 
AFTER rejection_reason;

-- 4. Ajouter la colonne rejected_at
ALTER TABLE commercial_order_clients 
ADD COLUMN rejected_at DATETIME NULL 
AFTER rejected_by_id;

-- 5. Ajouter l'index
ALTER TABLE commercial_order_clients 
ADD INDEX idx_orderclient_status (status);

-- 6. Ajouter la contrainte de clé étrangère
ALTER TABLE commercial_order_clients 
ADD CONSTRAINT fk_orderclient_rejected_by 
FOREIGN KEY (rejected_by_id) REFERENCES users (id) 
ON UPDATE CASCADE ON DELETE SET NULL;
```

### Méthode 3 : Via Python (si MySQL est accessible)

```bash
python3 migrate_client_rejection.py
```

---

## 🔍 VÉRIFICATION

Après avoir exécuté la migration, vérifiez que les colonnes existent :

```sql
SHOW COLUMNS FROM commercial_order_clients;
```

Vous devriez voir :
- `status`
- `rejection_reason`
- `rejected_by_id`
- `rejected_at`

---

## 🔄 APRÈS LA MIGRATION

1. ✅ Redémarrez le serveur Flask si nécessaire
2. ✅ Accédez à http://localhost:5002/orders/3
3. ✅ L'erreur devrait disparaître
4. ✅ Vous verrez les boutons pour rejeter/approuver des clients individuels

---

## 📋 COLONNES AJOUTÉES

| Colonne | Type | Description |
|---------|------|-------------|
| `status` | ENUM('pending', 'approved', 'rejected') | Statut du client dans la commande |
| `rejection_reason` | TEXT | Raison du rejet du client |
| `rejected_by_id` | BIGINT UNSIGNED | ID de l'utilisateur qui a rejeté |
| `rejected_at` | DATETIME | Date/heure du rejet |

---

**⚠️ IMPORTANT : Exécutez la migration avant d'utiliser la fonctionnalité !**

Une fois la migration exécutée, l'erreur disparaîtra et vous pourrez utiliser la fonctionnalité de rejet de clients individuels.

