#!/usr/bin/env python3
"""
Script pour corriger les tables de promotion
Ajoute les colonnes manquantes pour la géolocalisation et l'intermédiaire
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text, inspect

def check_and_add_columns():
    """Vérifie et ajoute les colonnes manquantes"""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('promotion_members')]
        
        print("📋 Colonnes actuelles dans promotion_members:")
        for col in columns:
            print(f"   - {col}")
        
        missing_columns = []
        
        # Vérifier les colonnes manquantes
        if 'home_latitude' not in columns:
            missing_columns.append('home_latitude')
        if 'home_longitude' not in columns:
            missing_columns.append('home_longitude')
        if 'intermediaire_id' not in columns:
            missing_columns.append('intermediaire_id')
        
        if not missing_columns:
            print("\n✅ Toutes les colonnes nécessaires existent déjà!")
            return
        
        print(f"\n⚠️  Colonnes manquantes: {', '.join(missing_columns)}")
        print("🔧 Ajout des colonnes...")
        
        try:
            # Ajouter home_latitude
            if 'home_latitude' not in columns:
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `home_latitude` DECIMAL(10, 8) NULL AFTER `address`
                """))
                print("   ✅ home_latitude ajoutée")
            
            # Ajouter home_longitude
            if 'home_longitude' not in columns:
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `home_longitude` DECIMAL(11, 8) NULL AFTER `home_latitude`
                """))
                print("   ✅ home_longitude ajoutée")
            
            # Ajouter intermediaire_id
            if 'intermediaire_id' not in columns:
                db.session.execute(text("""
                    ALTER TABLE `promotion_members` 
                    ADD COLUMN `intermediaire_id` BIGINT UNSIGNED NULL AFTER `home_longitude`
                """))
                print("   ✅ intermediaire_id ajoutée")
            
            # Ajouter les index
            indexes = [idx['name'] for idx in inspector.get_indexes('promotion_members')]
            
            if 'idx_promomember_intermediary' not in indexes:
                try:
                    db.session.execute(text("""
                        ALTER TABLE `promotion_members`
                        ADD INDEX `idx_promomember_intermediary` (`intermediaire_id`)
                    """))
                    print("   ✅ Index intermediaire ajouté")
                except Exception as e:
                    print(f"   ⚠️  Index intermediaire déjà existant ou erreur: {e}")
            
            if 'idx_promomember_location' not in indexes:
                try:
                    db.session.execute(text("""
                        ALTER TABLE `promotion_members`
                        ADD INDEX `idx_promomember_location` (`home_latitude`, `home_longitude`)
                    """))
                    print("   ✅ Index location ajouté")
                except Exception as e:
                    print(f"   ⚠️  Index location déjà existant ou erreur: {e}")
            
            # Ajouter la contrainte de clé étrangère
            foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('promotion_members')]
            
            if 'fk_promomember_intermediary' not in foreign_keys:
                try:
                    db.session.execute(text("""
                        ALTER TABLE `promotion_members`
                        ADD CONSTRAINT `fk_promomember_intermediary` 
                        FOREIGN KEY (`intermediaire_id`) REFERENCES `promotion_members` (`id`) 
                        ON UPDATE CASCADE ON DELETE SET NULL
                    """))
                    print("   ✅ Contrainte FK intermediaire ajoutée")
                except Exception as e:
                    print(f"   ⚠️  Contrainte FK déjà existante ou erreur: {e}")
            
            db.session.commit()
            print("\n✅ Toutes les colonnes ont été ajoutées avec succès!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de l'ajout des colonnes: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Vérifier la table promotion_gamme_articles
        print("\n📋 Vérification de la table promotion_gamme_articles...")
        try:
            gamme_articles_columns = [col['name'] for col in inspector.get_columns('promotion_gamme_articles')]
            print(f"   Colonnes: {', '.join(gamme_articles_columns)}")
            
            if not gamme_articles_columns:
                print("   ⚠️  Table promotion_gamme_articles n'existe pas, création...")
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
                db.session.commit()
                print("   ✅ Table promotion_gamme_articles créée")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    check_and_add_columns()

