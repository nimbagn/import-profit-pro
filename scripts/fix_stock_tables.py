#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter les colonnes manquantes aux tables de stock
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import inspect, text

def add_missing_columns():
    """Ajoute les colonnes manquantes aux tables de stock"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Vérifier et ajouter reference à stock_movements
            print("🔍 Vérification de la table stock_movements...")
            if 'stock_movements' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('stock_movements')]
                
                if 'reference' not in columns:
                    print("➕ Ajout de la colonne 'reference' à stock_movements...")
                    try:
                        db.session.execute(text("""
                            ALTER TABLE stock_movements 
                            ADD COLUMN reference VARCHAR(50) NULL,
                            ADD UNIQUE INDEX idx_movement_reference (reference)
                        """))
                        db.session.commit()
                        print("✅ Colonne 'reference' ajoutée à stock_movements")
                    except Exception as e:
                        db.session.rollback()
                        print(f"⚠️ Erreur lors de l'ajout de 'reference' à stock_movements: {e}")
                else:
                    print("✅ La colonne 'reference' existe déjà dans stock_movements")
            
            # Vérifier et ajouter original_outgoing_id à stock_returns
            print("\n🔍 Vérification de la table stock_returns...")
            if 'stock_returns' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('stock_returns')]
                
                if 'original_outgoing_id' not in columns:
                    print("➕ Ajout de la colonne 'original_outgoing_id' à stock_returns...")
                    try:
                        # Vérifier si stock_outgoings existe
                        if 'stock_outgoings' in inspector.get_table_names():
                            db.session.execute(text("""
                                ALTER TABLE stock_returns 
                                ADD COLUMN original_outgoing_id BIGINT UNSIGNED NULL,
                                ADD INDEX idx_return_outgoing (original_outgoing_id),
                                ADD CONSTRAINT fk_returns_outgoing 
                                    FOREIGN KEY (original_outgoing_id) 
                                    REFERENCES stock_outgoings(id) 
                                    ON UPDATE CASCADE ON DELETE SET NULL
                            """))
                            db.session.commit()
                            print("✅ Colonne 'original_outgoing_id' ajoutée à stock_returns")
                        else:
                            print("⚠️ La table stock_outgoings n'existe pas, ajout sans contrainte...")
                            db.session.execute(text("""
                                ALTER TABLE stock_returns 
                                ADD COLUMN original_outgoing_id BIGINT UNSIGNED NULL,
                                ADD INDEX idx_return_outgoing (original_outgoing_id)
                            """))
                            db.session.commit()
                            print("✅ Colonne 'original_outgoing_id' ajoutée à stock_returns (sans contrainte)")
                    except Exception as e:
                        db.session.rollback()
                        print(f"⚠️ Erreur lors de l'ajout de 'original_outgoing_id' à stock_returns: {e}")
                else:
                    print("✅ La colonne 'original_outgoing_id' existe déjà dans stock_returns")
                
                # Vérifier et ajouter reference à stock_returns
                if 'reference' not in columns:
                    print("➕ Ajout de la colonne 'reference' à stock_returns...")
                    try:
                        db.session.execute(text("""
                            ALTER TABLE stock_returns 
                            ADD COLUMN reference VARCHAR(50) NULL,
                            ADD UNIQUE INDEX idx_return_reference (reference)
                        """))
                        db.session.commit()
                        print("✅ Colonne 'reference' ajoutée à stock_returns")
                    except Exception as e:
                        db.session.rollback()
                        print(f"⚠️ Erreur lors de l'ajout de 'reference' à stock_returns: {e}")
                else:
                    print("✅ La colonne 'reference' existe déjà dans stock_returns")
            
            print("\n✅ Vérification terminée !")
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("🚀 Ajout des colonnes manquantes aux tables de stock...")
    print("=" * 60)
    add_missing_columns()
    print("=" * 60)
    print("✅ Script terminé !")

