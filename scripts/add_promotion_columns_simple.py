#!/usr/bin/env python3
"""
Script simple pour ajouter les colonnes manquantes à promotion_members
Utilise la même configuration que l'application
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def add_columns():
    """Ajoute les colonnes manquantes"""
    with app.app_context():
        try:
            print("🔧 Ajout des colonnes manquantes...")
            
            # Ajouter home_latitude
            try:
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `home_latitude` DECIMAL(10, 8) NULL AFTER `address`
                """))
                print("✅ home_latitude ajoutée")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    print("✓ home_latitude existe déjà")
                else:
                    raise
            
            # Ajouter home_longitude
            try:
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `home_longitude` DECIMAL(11, 8) NULL AFTER `home_latitude`
                """))
                print("✅ home_longitude ajoutée")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    print("✓ home_longitude existe déjà")
                else:
                    raise
            
            # Renommer ou ajouter intermediaire_id
            try:
                # Essayer de renommer d'abord
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    CHANGE COLUMN `intermediary_id` `intermediaire_id` BIGINT UNSIGNED NULL
                """))
                print("✅ intermediary_id renommée en intermediaire_id")
            except Exception as e:
                if "Unknown column" in str(e) or "doesn't exist" in str(e):
                    # La colonne n'existe pas, l'ajouter
                    try:
                        db.session.execute(text("""
                            ALTER TABLE `promotion_members` 
                            ADD COLUMN `intermediaire_id` BIGINT UNSIGNED NULL AFTER `home_longitude`
                        """))
                        print("✅ intermediaire_id ajoutée")
                    except Exception as e2:
                        if "Duplicate column name" in str(e2) or "already exists" in str(e2):
                            print("✓ intermediaire_id existe déjà")
                        else:
                            raise
                elif "Duplicate column name" in str(e) or "already exists" in str(e):
                    print("✓ intermediaire_id existe déjà")
                else:
                    raise
            
            db.session.commit()
            print("\n✅ Toutes les colonnes ont été ajoutées avec succès!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    add_columns()

