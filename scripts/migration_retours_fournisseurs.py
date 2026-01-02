#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration pour ajouter les champs nécessaires aux retours fournisseurs
Date : 2 Janvier 2026
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from models import db
from sqlalchemy import inspect, text
from db_utils.db_adapter import get_db_type, is_postgresql, is_mysql

def migrate_returns_table():
    """Ajouter les colonnes nécessaires pour les retours fournisseurs"""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('stock_returns')]
        
        print("=" * 80)
        print("MIGRATION : RETOURS FOURNISSEURS")
        print("=" * 80)
        print()
        
        db_type = get_db_type()
        print(f"📊 Type de base de données détecté : {db_type}")
        print()
        
        # 1. Ajouter return_type
        if 'return_type' not in columns:
            print("➕ Ajout de la colonne return_type...")
            try:
                if is_postgresql():
                    db.session.execute(text("""
                        DO $$ 
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'return_type') THEN
                                CREATE TYPE return_type AS ENUM ('client', 'supplier');
                            END IF;
                        END $$;
                    """))
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN return_type return_type NOT NULL DEFAULT 'client';
                    """))
                elif is_mysql():
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN return_type ENUM('client', 'supplier') NOT NULL DEFAULT 'client' AFTER return_date;
                    """))
                db.session.commit()
                print("✅ Colonne return_type ajoutée avec succès")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Erreur lors de l'ajout de return_type: {e}")
        else:
            print("✅ Colonne return_type existe déjà")
        
        # 2. Ajouter supplier_name
        if 'supplier_name' not in columns:
            print("➕ Ajout de la colonne supplier_name...")
            try:
                if is_postgresql():
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN supplier_name VARCHAR(120) NULL;
                    """))
                elif is_mysql():
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN supplier_name VARCHAR(120) NULL AFTER client_phone;
                    """))
                db.session.commit()
                print("✅ Colonne supplier_name ajoutée avec succès")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Erreur lors de l'ajout de supplier_name: {e}")
        else:
            print("✅ Colonne supplier_name existe déjà")
        
        # 3. Ajouter original_reception_id
        if 'original_reception_id' not in columns:
            print("➕ Ajout de la colonne original_reception_id...")
            try:
                if is_postgresql():
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN original_reception_id BIGINT NULL;
                    """))
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD CONSTRAINT fk_return_reception 
                            FOREIGN KEY (original_reception_id) 
                            REFERENCES receptions(id) 
                            ON UPDATE CASCADE 
                            ON DELETE SET NULL;
                    """))
                elif is_mysql():
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN original_reception_id BIGINT UNSIGNED NULL AFTER original_order_id,
                        ADD CONSTRAINT fk_return_reception 
                            FOREIGN KEY (original_reception_id) 
                            REFERENCES receptions(id) 
                            ON UPDATE CASCADE 
                            ON DELETE SET NULL;
                    """))
                db.session.commit()
                print("✅ Colonne original_reception_id ajoutée avec succès")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Erreur lors de l'ajout de original_reception_id: {e}")
        else:
            print("✅ Colonne original_reception_id existe déjà")
        
        # 4. Modifier client_name pour être nullable
        print("🔧 Modification de client_name pour être nullable...")
        try:
            if is_postgresql():
                db.session.execute(text("""
                    ALTER TABLE stock_returns 
                    ALTER COLUMN client_name DROP NOT NULL;
                """))
            elif is_mysql():
                db.session.execute(text("""
                    ALTER TABLE stock_returns 
                    MODIFY COLUMN client_name VARCHAR(120) NULL;
                """))
            db.session.commit()
            print("✅ client_name est maintenant nullable")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erreur lors de la modification de client_name: {e}")
        
        # 5. Ajouter les index
        print("📇 Ajout des index...")
        try:
            if is_postgresql():
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_return_type ON stock_returns(return_type);"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_return_reception ON stock_returns(original_reception_id);"))
            elif is_mysql():
                db.session.execute(text("CREATE INDEX idx_return_type ON stock_returns(return_type);"))
                db.session.execute(text("CREATE INDEX idx_return_reception ON stock_returns(original_reception_id);"))
            db.session.commit()
            print("✅ Index ajoutés avec succès")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erreur lors de l'ajout des index: {e}")
        
        print()
        print("=" * 80)
        print("✅ MIGRATION TERMINÉE")
        print("=" * 80)

def migrate_movement_type():
    """Ajouter le type 'reception_return' à l'enum movement_type"""
    with app.app_context():
        print()
        print("=" * 80)
        print("MIGRATION : TYPE DE MOUVEMENT 'reception_return'")
        print("=" * 80)
        print()
        
        db_type = get_db_type()
        print(f"📊 Type de base de données détecté : {db_type}")
        print()
        
        try:
            if is_postgresql():
                print("➕ Ajout de la valeur 'reception_return' à l'enum movement_type...")
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum 
                            WHERE enumlabel = 'reception_return' 
                            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
                        ) THEN
                            ALTER TYPE movement_type ADD VALUE 'reception_return';
                        END IF;
                    END $$;
                """))
                db.session.commit()
                print("✅ Type 'reception_return' ajouté avec succès")
            elif is_mysql():
                print("➕ Modification de l'enum movement_type pour inclure 'reception_return'...")
                print("⚠️ ATTENTION : Cette opération peut prendre du temps sur une grande table")
                db.session.execute(text("""
                    ALTER TABLE stock_movements 
                    MODIFY COLUMN movement_type ENUM('transfer', 'reception', 'reception_return', 'adjustment', 'inventory') NOT NULL;
                """))
                db.session.commit()
                print("✅ Type 'reception_return' ajouté avec succès")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erreur lors de l'ajout du type: {e}")
            print("💡 Le type existe peut-être déjà, vérifiez manuellement")
        
        print()
        print("=" * 80)
        print("✅ MIGRATION TERMINÉE")
        print("=" * 80)

if __name__ == '__main__':
    migrate_returns_table()
    migrate_movement_type()

