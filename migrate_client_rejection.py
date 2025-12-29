#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration pour ajouter les champs de rejet de clients individuels
"""

from app import app, db
from sqlalchemy import text

def migrate_client_rejection_fields():
    """Ajoute les colonnes nécessaires pour le rejet de clients individuels"""
    
    with app.app_context():
        try:
            print("🔄 Début de la migration...")
            
            # Vérifier et ajouter la colonne status
            try:
                result = db.session.execute(text("SHOW COLUMNS FROM commercial_order_clients LIKE 'status'"))
                if result.fetchone():
                    print("✅ Colonne 'status' existe déjà")
                else:
                    db.session.execute(text("""
                        ALTER TABLE commercial_order_clients 
                        ADD COLUMN status ENUM('pending', 'approved', 'rejected') 
                        NOT NULL DEFAULT 'pending' 
                        AFTER comments
                    """))
                    db.session.commit()
                    print("✅ Colonne 'status' ajoutée")
            except Exception as e:
                if 'Duplicate column name' in str(e) or 'already exists' in str(e):
                    print("✅ Colonne 'status' existe déjà")
                else:
                    print(f"⚠️ Erreur pour 'status': {e}")
                    db.session.rollback()
            
            # Vérifier et ajouter la colonne rejection_reason
            try:
                result = db.session.execute(text("SHOW COLUMNS FROM commercial_order_clients LIKE 'rejection_reason'"))
                if result.fetchone():
                    print("✅ Colonne 'rejection_reason' existe déjà")
                else:
                    db.session.execute(text("""
                        ALTER TABLE commercial_order_clients 
                        ADD COLUMN rejection_reason TEXT NULL 
                        AFTER status
                    """))
                    db.session.commit()
                    print("✅ Colonne 'rejection_reason' ajoutée")
            except Exception as e:
                if 'Duplicate column name' in str(e) or 'already exists' in str(e):
                    print("✅ Colonne 'rejection_reason' existe déjà")
                else:
                    print(f"⚠️ Erreur pour 'rejection_reason': {e}")
                    db.session.rollback()
            
            # Vérifier et ajouter la colonne rejected_by_id
            try:
                result = db.session.execute(text("SHOW COLUMNS FROM commercial_order_clients LIKE 'rejected_by_id'"))
                if result.fetchone():
                    print("✅ Colonne 'rejected_by_id' existe déjà")
                else:
                    db.session.execute(text("""
                        ALTER TABLE commercial_order_clients 
                        ADD COLUMN rejected_by_id BIGINT UNSIGNED NULL 
                        AFTER rejection_reason
                    """))
                    db.session.commit()
                    print("✅ Colonne 'rejected_by_id' ajoutée")
            except Exception as e:
                if 'Duplicate column name' in str(e) or 'already exists' in str(e):
                    print("✅ Colonne 'rejected_by_id' existe déjà")
                else:
                    print(f"⚠️ Erreur pour 'rejected_by_id': {e}")
                    db.session.rollback()
            
            # Vérifier et ajouter la colonne rejected_at
            try:
                result = db.session.execute(text("SHOW COLUMNS FROM commercial_order_clients LIKE 'rejected_at'"))
                if result.fetchone():
                    print("✅ Colonne 'rejected_at' existe déjà")
                else:
                    db.session.execute(text("""
                        ALTER TABLE commercial_order_clients 
                        ADD COLUMN rejected_at DATETIME NULL 
                        AFTER rejected_by_id
                    """))
                    db.session.commit()
                    print("✅ Colonne 'rejected_at' ajoutée")
            except Exception as e:
                if 'Duplicate column name' in str(e) or 'already exists' in str(e):
                    print("✅ Colonne 'rejected_at' existe déjà")
                else:
                    print(f"⚠️ Erreur pour 'rejected_at': {e}")
                    db.session.rollback()
            
            # Vérifier et ajouter l'index
            try:
                result = db.session.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.STATISTICS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'commercial_order_clients' 
                    AND INDEX_NAME = 'idx_orderclient_status'
                """))
                count = result.fetchone()[0]
                if count > 0:
                    print("✅ Index 'idx_orderclient_status' existe déjà")
                else:
                    db.session.execute(text("""
                        ALTER TABLE commercial_order_clients 
                        ADD INDEX idx_orderclient_status (status)
                    """))
                    db.session.commit()
                    print("✅ Index 'idx_orderclient_status' ajouté")
            except Exception as e:
                if 'Duplicate key name' in str(e) or 'already exists' in str(e):
                    print("✅ Index 'idx_orderclient_status' existe déjà")
                else:
                    print(f"⚠️ Erreur pour l'index: {e}")
                    db.session.rollback()
            
            # Vérifier et ajouter la contrainte de clé étrangère
            try:
                result = db.session.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'commercial_order_clients' 
                    AND CONSTRAINT_NAME = 'fk_orderclient_rejected_by'
                """))
                count = result.fetchone()[0]
                if count > 0:
                    print("✅ Contrainte 'fk_orderclient_rejected_by' existe déjà")
                else:
                    db.session.execute(text("""
                        ALTER TABLE commercial_order_clients 
                        ADD CONSTRAINT fk_orderclient_rejected_by 
                        FOREIGN KEY (rejected_by_id) 
                        REFERENCES users (id) 
                        ON UPDATE CASCADE 
                        ON DELETE SET NULL
                    """))
                    db.session.commit()
                    print("✅ Contrainte 'fk_orderclient_rejected_by' ajoutée")
            except Exception as e:
                if 'Duplicate foreign key' in str(e) or 'already exists' in str(e):
                    print("✅ Contrainte 'fk_orderclient_rejected_by' existe déjà")
                else:
                    print(f"⚠️ Erreur pour la contrainte: {e}")
                    db.session.rollback()
            
            print("\n✅ Migration terminée avec succès !")
            print("🔄 Vous pouvez maintenant utiliser la fonctionnalité de rejet de clients individuels.")
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la migration: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    migrate_client_rejection_fields()

