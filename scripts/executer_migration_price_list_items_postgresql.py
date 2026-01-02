#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter la migration price_list_items vers stock_items
PostgreSQL - Idempotent (peut être exécuté plusieurs fois sans erreur)
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text, inspect
from sqlalchemy.exc import ProgrammingError, OperationalError

def check_column_exists(table_name, column_name):
    """Vérifier si une colonne existe dans une table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_constraint_exists(constraint_name):
    """Vérifier si une contrainte existe"""
    try:
        result = db.session.execute(text("""
            SELECT 1 FROM pg_constraint 
            WHERE conname = :constraint_name
        """), {'constraint_name': constraint_name})
        return result.fetchone() is not None
    except Exception:
        return False

def check_index_exists(index_name):
    """Vérifier si un index existe"""
    try:
        result = db.session.execute(text("""
            SELECT 1 FROM pg_indexes 
            WHERE indexname = :index_name
        """), {'index_name': index_name})
        return result.fetchone() is not None
    except Exception:
        return False

def execute_migration():
    """Exécuter la migration"""
    print("🔄 Début de la migration price_list_items vers stock_items...")
    print("")
    
    with app.app_context():
        try:
            # Vérifier si la migration a déjà été effectuée
            has_article_id = check_column_exists('price_list_items', 'article_id')
            has_stock_item_id = check_column_exists('price_list_items', 'stock_item_id')
            
            if has_stock_item_id and not has_article_id:
                print("✅ La migration a déjà été effectuée (stock_item_id existe, article_id n'existe pas)")
                return True
            
            if not has_article_id and not has_stock_item_id:
                print("❌ Erreur: Ni article_id ni stock_item_id n'existent dans price_list_items")
                print("   La table price_list_items semble avoir une structure inattendue.")
                return False
            
            print("📋 État actuel:")
            print(f"   - Colonne article_id existe: {has_article_id}")
            print(f"   - Colonne stock_item_id existe: {has_stock_item_id}")
            print("")
            
            # Étape 1 : Supprimer les données existantes
            print("🗑️  Étape 1: Suppression des données existantes...")
            try:
                db.session.execute(text("DELETE FROM price_list_items"))
                db.session.commit()
                print("   ✅ Données supprimées")
            except Exception as e:
                print(f"   ⚠️  Avertissement lors de la suppression: {e}")
                db.session.rollback()
            
            # Étape 2 : Supprimer l'ancienne contrainte de clé étrangère
            print("🔧 Étape 2: Suppression de l'ancienne contrainte fk_pricelistitem_article...")
            if check_constraint_exists('fk_pricelistitem_article'):
                try:
                    db.session.execute(text("""
                        ALTER TABLE price_list_items 
                        DROP CONSTRAINT fk_pricelistitem_article
                    """))
                    db.session.commit()
                    print("   ✅ Contrainte supprimée")
                except Exception as e:
                    print(f"   ⚠️  Erreur: {e}")
                    db.session.rollback()
            else:
                print("   ℹ️  Contrainte n'existe pas (déjà supprimée)")
            
            # Étape 3 : Supprimer l'ancien index
            print("🔧 Étape 3: Suppression de l'ancien index idx_pricelistitem_article...")
            if check_index_exists('idx_pricelistitem_article'):
                try:
                    db.session.execute(text("DROP INDEX IF EXISTS idx_pricelistitem_article"))
                    db.session.commit()
                    print("   ✅ Index supprimé")
                except Exception as e:
                    print(f"   ⚠️  Erreur: {e}")
                    db.session.rollback()
            else:
                print("   ℹ️  Index n'existe pas (déjà supprimé)")
            
            # Étape 4 : Supprimer l'ancienne contrainte unique
            print("🔧 Étape 4: Suppression de l'ancienne contrainte unique uk_pricelistitem_unique...")
            if check_constraint_exists('uk_pricelistitem_unique'):
                try:
                    db.session.execute(text("""
                        ALTER TABLE price_list_items 
                        DROP CONSTRAINT uk_pricelistitem_unique
                    """))
                    db.session.commit()
                    print("   ✅ Contrainte unique supprimée")
                except Exception as e:
                    print(f"   ⚠️  Erreur: {e}")
                    db.session.rollback()
            else:
                print("   ℹ️  Contrainte unique n'existe pas (déjà supprimée)")
            
            # Étape 5 : Supprimer l'ancienne colonne article_id
            print("🔧 Étape 5: Suppression de l'ancienne colonne article_id...")
            if has_article_id:
                try:
                    db.session.execute(text("ALTER TABLE price_list_items DROP COLUMN article_id"))
                    db.session.commit()
                    print("   ✅ Colonne article_id supprimée")
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
                    db.session.rollback()
                    return False
            else:
                print("   ℹ️  Colonne article_id n'existe pas (déjà supprimée)")
            
            # Étape 6 : Ajouter la nouvelle colonne stock_item_id
            print("🔧 Étape 6: Ajout de la nouvelle colonne stock_item_id...")
            if not has_stock_item_id:
                try:
                    db.session.execute(text("""
                        ALTER TABLE price_list_items 
                        ADD COLUMN stock_item_id BIGINT NOT NULL DEFAULT 0
                    """))
                    db.session.commit()
                    print("   ✅ Colonne stock_item_id ajoutée")
                    
                    # Supprimer la valeur par défaut après création
                    db.session.execute(text("""
                        ALTER TABLE price_list_items 
                        ALTER COLUMN stock_item_id DROP DEFAULT
                    """))
                    db.session.commit()
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
                    db.session.rollback()
                    return False
            else:
                print("   ℹ️  Colonne stock_item_id existe déjà")
            
            # Étape 7 : Ajouter la contrainte de clé étrangère
            print("🔧 Étape 7: Ajout de la contrainte de clé étrangère fk_pricelistitem_stock_item...")
            if not check_constraint_exists('fk_pricelistitem_stock_item'):
                try:
                    db.session.execute(text("""
                        ALTER TABLE price_list_items 
                        ADD CONSTRAINT fk_pricelistitem_stock_item 
                        FOREIGN KEY (stock_item_id) REFERENCES stock_items(id) 
                        ON UPDATE CASCADE ON DELETE CASCADE
                    """))
                    db.session.commit()
                    print("   ✅ Contrainte de clé étrangère ajoutée")
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
                    db.session.rollback()
                    return False
            else:
                print("   ℹ️  Contrainte de clé étrangère existe déjà")
            
            # Étape 8 : Ajouter l'index
            print("🔧 Étape 8: Ajout de l'index idx_pricelistitem_stock_item...")
            if not check_index_exists('idx_pricelistitem_stock_item'):
                try:
                    db.session.execute(text("""
                        CREATE INDEX idx_pricelistitem_stock_item 
                        ON price_list_items(stock_item_id)
                    """))
                    db.session.commit()
                    print("   ✅ Index ajouté")
                except Exception as e:
                    print(f"   ⚠️  Erreur: {e}")
                    db.session.rollback()
            else:
                print("   ℹ️  Index existe déjà")
            
            # Étape 9 : Ajouter la contrainte unique
            print("🔧 Étape 9: Ajout de la contrainte unique uk_pricelistitem_unique...")
            if not check_constraint_exists('uk_pricelistitem_unique'):
                try:
                    db.session.execute(text("""
                        ALTER TABLE price_list_items 
                        ADD CONSTRAINT uk_pricelistitem_unique 
                        UNIQUE (price_list_id, stock_item_id)
                    """))
                    db.session.commit()
                    print("   ✅ Contrainte unique ajoutée")
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
                    db.session.rollback()
                    return False
            else:
                print("   ℹ️  Contrainte unique existe déjà")
            
            print("")
            print("✅ Migration terminée avec succès!")
            print("")
            print("📊 Vérification de la structure finale:")
            inspector = inspect(db.engine)
            columns = inspector.get_columns('price_list_items')
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"")
            print(f"❌ Erreur lors de la migration: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = execute_migration()
    sys.exit(0 if success else 1)

