#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration pour permettre NULL dans unit_price_gnf
Aligne la base de données avec le modèle Python
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text
from db_utils.db_adapter import get_db_type, is_mysql, is_postgresql

def migrate_unit_price_gnf_nullable():
    """Permettre NULL pour unit_price_gnf dans reception_details"""
    
    with app.app_context():
        try:
            db_type = get_db_type()
            print(f"📊 Type de base de données détecté: {db_type}")
            
            # Étape 1: Mettre à jour les valeurs NULL existantes avec 0
            print("\n🔄 Étape 1: Mise à jour des valeurs NULL existantes...")
            result = db.session.execute(
                text("UPDATE reception_details SET unit_price_gnf = 0 WHERE unit_price_gnf IS NULL")
            )
            updated_rows = result.rowcount
            db.session.commit()
            print(f"✅ {updated_rows} enregistrement(s) mis à jour")
            
            # Étape 2: Modifier la colonne pour permettre NULL
            print("\n🔄 Étape 2: Modification de la colonne pour permettre NULL...")
            
            if is_mysql():
                # MySQL
                db.session.execute(
                    text("ALTER TABLE reception_details MODIFY COLUMN unit_price_gnf DECIMAL(18,2) NULL")
                )
                print("✅ Colonne modifiée pour MySQL")
                
            elif is_postgresql():
                # PostgreSQL
                db.session.execute(
                    text("ALTER TABLE reception_details ALTER COLUMN unit_price_gnf DROP NOT NULL")
                )
                print("✅ Colonne modifiée pour PostgreSQL")
            else:
                print("⚠️  Type de base de données non supporté")
                return False
            
            db.session.commit()
            
            # Vérification
            print("\n🔍 Vérification de la modification...")
            if is_mysql():
                result = db.session.execute(text("""
                    SELECT 
                        COLUMN_NAME,
                        IS_NULLABLE,
                        COLUMN_TYPE,
                        COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'reception_details'
                      AND COLUMN_NAME = 'unit_price_gnf'
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
                      AND table_name = 'reception_details'
                      AND column_name = 'unit_price_gnf'
                """))
            
            row = result.fetchone()
            if row:
                if is_mysql():
                    is_nullable = row[1]
                    print(f"✅ Colonne unit_price_gnf: IS_NULLABLE = {is_nullable}")
                else:
                    is_nullable = row[1]
                    print(f"✅ Colonne unit_price_gnf: is_nullable = {is_nullable}")
                
                if is_nullable == 'YES' or is_nullable:
                    print("✅ Migration réussie ! La colonne permet maintenant NULL")
                    return True
                else:
                    print("⚠️  La colonne ne permet toujours pas NULL")
                    return False
            else:
                print("⚠️  Impossible de vérifier la colonne")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: unit_price_gnf nullable dans reception_details")
    print("=" * 60)
    
    success = migrate_unit_price_gnf_nullable()
    
    if success:
        print("\n✅ Migration terminée avec succès !")
        sys.exit(0)
    else:
        print("\n❌ Migration échouée !")
        sys.exit(1)

