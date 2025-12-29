-- Migration simple pour ajouter les champs de rejet de clients
-- À exécuter directement dans MySQL

USE madargn;

-- Ajouter la colonne status
ALTER TABLE commercial_order_clients 
ADD COLUMN status ENUM('pending', 'approved', 'rejected') 
NOT NULL DEFAULT 'pending' 
AFTER comments;

-- Ajouter la colonne rejection_reason
ALTER TABLE commercial_order_clients 
ADD COLUMN rejection_reason TEXT NULL 
AFTER status;

-- Ajouter la colonne rejected_by_id
ALTER TABLE commercial_order_clients 
ADD COLUMN rejected_by_id BIGINT UNSIGNED NULL 
AFTER rejection_reason;

-- Ajouter la colonne rejected_at
ALTER TABLE commercial_order_clients 
ADD COLUMN rejected_at DATETIME NULL 
AFTER rejected_by_id;

-- Ajouter l'index
ALTER TABLE commercial_order_clients 
ADD INDEX idx_orderclient_status (status);

-- Ajouter la contrainte de clé étrangère
ALTER TABLE commercial_order_clients 
ADD CONSTRAINT fk_orderclient_rejected_by 
FOREIGN KEY (rejected_by_id) REFERENCES users (id) 
ON UPDATE CASCADE ON DELETE SET NULL;

SELECT 'Migration terminée avec succès' AS result;

