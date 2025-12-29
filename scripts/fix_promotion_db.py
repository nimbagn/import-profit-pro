#!/usr/bin/env python3
"""
Script pour créer les colonnes manquantes dans la table promotion_members
Utilise la même configuration que l'application
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def fix_promotion_tables():
    """Crée les colonnes manquantes dans promotion_members"""
    with app.app_context():
        try:
            print("🔧 Vérification et création des colonnes...")
            
            # Vérifier si les colonnes existent déjà
            result = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'promotion_members'
                AND COLUMN_NAME IN ('home_latitude', 'home_longitude', 'intermediaire_id')
            """))
            existing_cols = [row[0] for row in result]
            
            print(f"📋 Colonnes existantes: {existing_cols}")
            
            # Ajouter home_latitude si elle n'existe pas
            if 'home_latitude' not in existing_cols:
                print("   ➕ Ajout de home_latitude...")
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `home_latitude` DECIMAL(10, 8) NULL AFTER `address`
                """))
                print("   ✅ home_latitude ajoutée")
            else:
                print("   ✓ home_latitude existe déjà")
            
            # Ajouter home_longitude si elle n'existe pas
            if 'home_longitude' not in existing_cols:
                print("   ➕ Ajout de home_longitude...")
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `home_longitude` DECIMAL(11, 8) NULL AFTER `home_latitude`
                """))
                print("   ✅ home_longitude ajoutée")
            else:
                print("   ✓ home_longitude existe déjà")
            
            # Ajouter intermediaire_id si elle n'existe pas
            if 'intermediaire_id' not in existing_cols:
                print("   ➕ Ajout de intermediaire_id...")
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `intermediaire_id` BIGINT UNSIGNED NULL AFTER `home_longitude`
                """))
                print("   ✅ intermediaire_id ajoutée")
            else:
                print("   ✓ intermediaire_id existe déjà")
            
            # Vérifier les index
            result = db.session.execute(text("""
                SELECT INDEX_NAME 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'promotion_members'
                AND INDEX_NAME IN ('idx_promomember_intermediary', 'idx_promomember_location')
            """))
            existing_indexes = [row[0] for row in result]
            
            # Ajouter index intermediaire
            if 'idx_promomember_intermediary' not in existing_indexes:
                print("   ➕ Ajout de l'index intermediaire...")
                try:
                    db.session.execute(text("""
                        ALTER TABLE `promotion_members`
                        ADD INDEX `idx_promomember_intermediary` (`intermediaire_id`)
                    """))
                    print("   ✅ Index intermediaire ajouté")
                except Exception as e:
                    print(f"   ⚠️  Erreur index intermediaire: {e}")
            else:
                print("   ✓ Index intermediaire existe déjà")
            
            # Ajouter index location
            if 'idx_promomember_location' not in existing_indexes:
                print("   ➕ Ajout de l'index location...")
                try:
                    db.session.execute(text("""
                        ALTER TABLE `promotion_members`
                        ADD INDEX `idx_promomember_location` (`home_latitude`, `home_longitude`)
                    """))
                    print("   ✅ Index location ajouté")
                except Exception as e:
                    print(f"   ⚠️  Erreur index location: {e}")
            else:
                print("   ✓ Index location existe déjà")
            
            # Vérifier la contrainte FK
            result = db.session.execute(text("""
                SELECT CONSTRAINT_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'promotion_members'
                AND CONSTRAINT_NAME = 'fk_promomember_intermediary'
            """))
            fk_exists = result.fetchone() is not None
            
            if not fk_exists:
                print("   ➕ Ajout de la contrainte FK intermediaire...")
                try:
                    db.session.execute(text("""
                        ALTER TABLE `promotion_members`
                        ADD CONSTRAINT `fk_promomember_intermediary` 
                        FOREIGN KEY (`intermediaire_id`) REFERENCES `promotion_members` (`id`) 
                        ON UPDATE CASCADE ON DELETE SET NULL
                    """))
                    print("   ✅ Contrainte FK ajoutée")
                except Exception as e:
                    print(f"   ⚠️  Erreur contrainte FK: {e}")
            else:
                print("   ✓ Contrainte FK existe déjà")
            
            # Créer la table promotion_gamme_articles
            print("   ➕ Vérification de promotion_gamme_articles...")
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS `promotion_gamme_articles` (
                        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                        `gamme_id` BIGINT UNSIGNED NOT NULL,
                        `article_id` BIGINT UNSIGNED NOT NULL,
                        `quantity` INT NOT NULL DEFAULT 1,
                        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (`id`),
                        UNIQUE KEY `uq_gamme_article` (`gamme_id`, `article_id`),
                        INDEX `idx_promogammearticle_gamme` (`gamme_id`),
                        INDEX `idx_promogammearticle_article` (`article_id`),
                        CONSTRAINT `fk_gamme_articles_gamme` 
                            FOREIGN KEY (`gamme_id`) REFERENCES `promotion_gammes` (`id`) 
                            ON UPDATE CASCADE ON DELETE CASCADE,
                        CONSTRAINT `fk_gamme_articles_article` 
                            FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) 
                            ON UPDATE CASCADE ON DELETE RESTRICT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                print("   ✅ Table promotion_gamme_articles vérifiée/créée")
            except Exception as e:
                print(f"   ⚠️  Erreur table gamme_articles: {e}")
            
            db.session.commit()
            print("\n✅ Toutes les colonnes et index ont été créés avec succès!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de la création: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    fix_promotion_tables()

