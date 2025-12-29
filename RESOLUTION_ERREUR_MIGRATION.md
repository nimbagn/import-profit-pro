# 🔴 Résolution de l'Erreur de Migration

**Date**: 24 Décembre 2025

---

## ❌ ERREUR ACTUELLE

```
pymysql.err.OperationalError: (1054, "Unknown column 'commercial_order_clients_1.rejection_reason' in 'field list'")
```

**Cause** : Les colonnes pour le rejet de clients individuels n'ont pas encore été créées dans la base de données MySQL.

---

## ✅ SOLUTION RAPIDE

### Exécutez cette commande SQL dans MySQL :

```bash
mysql -u root -p madargn < migration_simple.sql
```

Ou copiez-collez ces commandes dans votre client MySQL :

```sql
USE madargn;

ALTER TABLE commercial_order_clients 
ADD COLUMN status ENUM('pending', 'approved', 'rejected') 
NOT NULL DEFAULT 'pending' AFTER comments;

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

1. ✅ Redémarrez le serveur Flask (si nécessaire)
2. ✅ Accédez à http://localhost:5002/orders/3
3. ✅ L'erreur devrait disparaître
4. ✅ Vous verrez les boutons pour rejeter/approuver des clients

---

## 📋 FICHIERS CRÉÉS

- ✅ `migration_simple.sql` : Script SQL simple à exécuter
- ✅ `migrate_client_rejection.py` : Script Python de migration
- ✅ `migrations/add_client_rejection_fields.sql` : Script SQL complet avec vérifications

---

**⚠️ Exécutez la migration maintenant pour résoudre l'erreur !**

