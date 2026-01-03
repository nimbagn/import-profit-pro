#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration pour ajouter la colonne reference à stock_movements
Aligne la base de données avec le modèle Python
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text
from db_utils.db_adapter import get_db_type, is_mysql, is_postgresql

def migrate_add_reference_column():
    """Ajouter la colonne reference à stock_movements si elle n'existe pas"""
    
    with app.app_context():
        try:
            db_type = get_db_type()
            print(f"📊 Type de base de données détecté: {db_type}")
            
            # Vérifier si la colonne existe déjà avec une requête directe
            print("\n🔍 Vérification de l'existence de la colonne 'reference'...")
            column_exists = False
            
            try:
                if is_mysql():
                    result = db.session.execute(text("""
                        SELECT COUNT(*) as count
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'stock_movements'
                          AND COLUMN_NAME = 'reference'
                    """))
                else:  # PostgreSQL
                    result = db.session.execute(text("""
                        SELECT COUNT(*) as count
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'stock_movements'
                          AND column_name = 'reference'
                    """))
                
                row = result.fetchone()
                column_exists = row and row[0] > 0
                
            except Exception as e:
                print(f"⚠️  Erreur lors de la vérification: {e}")
                # Continuer pour essayer de créer la colonne
            
            if column_exists:
                print("✅ La colonne 'reference' existe déjà")
                
                # Vérifier les propriétés de la colonne
                try:
                    if is_mysql():
                        result = db.session.execute(text("""
                            SELECT 
                                COLUMN_NAME,
                                IS_NULLABLE,
                                COLUMN_TYPE,
                                COLUMN_KEY
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_SCHEMA = DATABASE()
                              AND TABLE_NAME = 'stock_movements'
                              AND COLUMN_NAME = 'reference'
                        """))
                    else:  # PostgreSQL
                        result = db.session.execute(text("""
                            SELECT 
                                column_name,
                                is_nullable,
                                data_type,
                                column_default
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'stock_movements'
                              AND column_name = 'reference'
                        """))
                    
                    row = result.fetchone()
                    if row:
                        print(f"✅ Propriétés de la colonne: {dict(row._mapping)}")
                except Exception as e:
                    print(f"⚠️  Impossible de récupérer les propriétés: {e}")
                
                return True
            else:
                print("⚠️  La colonne 'reference' n'existe pas, création en cours...")
                
                try:
                    # Ajouter la colonne
                    if is_mysql():
                        # MySQL
                        db.session.execute(
                            text("ALTER TABLE stock_movements ADD COLUMN reference VARCHAR(50) NULL UNIQUE AFTER id")
                        )
                        print("✅ Colonne 'reference' ajoutée pour MySQL")
                        
                    elif is_postgresql():
                        # PostgreSQL
                        db.session.execute(
                            text("ALTER TABLE stock_movements ADD COLUMN reference VARCHAR(50) NULL")
                        )
                        # Ajouter la contrainte unique
                        db.session.execute(
                            text("CREATE UNIQUE INDEX idx_movement_reference ON stock_movements(reference)")
                        )
                        print("✅ Colonne 'reference' ajoutée pour PostgreSQL")
                    else:
                        print("⚠️  Type de base de données non supporté")
                        return False
                    
                    db.session.commit()
                    print("✅ Colonne 'reference' créée avec succès !")
                    return True
                    
                except Exception as create_error:
                    # Si l'erreur est "Duplicate column", c'est OK (la colonne existe déjà)
                    error_str = str(create_error)
                    if "Duplicate column" in error_str or "duplicate" in error_str.lower() or "already exists" in error_str.lower():
                        print("✅ La colonne 'reference' existe déjà (erreur ignorée)")
                        db.session.rollback()
                        return True
                    else:
                        # Autre erreur, on la propage
                        raise create_error
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: Ajout colonne reference dans stock_movements")
    print("=" * 60)
    
    success = migrate_add_reference_column()
    
    if success:
        print("\n✅ Migration terminée avec succès !")
        sys.exit(0)
    else:
        print("\n❌ Migration échouée !")
        sys.exit(1)

