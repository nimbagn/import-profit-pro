#!/usr/bin/env python3
"""
Script pour corriger les colonnes de promotion_members
Renomme intermediary_id en intermediaire_id et ajoute les colonnes de géolocalisation
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import direct de pymysql pour éviter les problèmes de configuration
try:
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    print(f"🔌 Connexion à MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    connection = pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD_RAW,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        print("🔍 Vérification des colonnes existantes...")
        
        # Vérifier les colonnes existantes
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'promotion_members'
        """, (DB_NAME,))
        existing_cols = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Colonnes existantes: {existing_cols}")
        
        # Renommer intermediary_id en intermediaire_id si elle existe
        if 'intermediary_id' in existing_cols and 'intermediaire_id' not in existing_cols:
            print("   🔄 Renommage de intermediary_id en intermediaire_id...")
            cursor.execute("""
                ALTER TABLE `promotion_members` 
                CHANGE COLUMN `intermediary_id` `intermediaire_id` BIGINT UNSIGNED NULL
            """)
            print("   ✅ Colonne renommée")
        elif 'intermediary_id' in existing_cols:
            print("   ⚠️  Les deux colonnes existent, suppression de intermediary_id...")
            cursor.execute("ALTER TABLE `promotion_members` DROP COLUMN `intermediary_id`")
            print("   ✅ Ancienne colonne supprimée")
        
        # Ajouter home_latitude si elle n'existe pas
        if 'home_latitude' not in existing_cols:
            print("   ➕ Ajout de home_latitude...")
            cursor.execute("""
                ALTER TABLE `promotion_members` 
                ADD COLUMN `home_latitude` DECIMAL(10, 8) NULL AFTER `address`
            """)
            print("   ✅ home_latitude ajoutée")
        else:
            print("   ✓ home_latitude existe déjà")
        
        # Ajouter home_longitude si elle n'existe pas
        if 'home_longitude' not in existing_cols:
            print("   ➕ Ajout de home_longitude...")
            cursor.execute("""
                ALTER TABLE `promotion_members` 
                ADD COLUMN `home_longitude` DECIMAL(11, 8) NULL AFTER `home_latitude`
            """)
            print("   ✅ home_longitude ajoutée")
        else:
            print("   ✓ home_longitude existe déjà")
        
        # Ajouter intermediaire_id si elle n'existe pas
        if 'intermediaire_id' not in existing_cols:
            print("   ➕ Ajout de intermediaire_id...")
            cursor.execute("""
                ALTER TABLE `promotion_members` 
                ADD COLUMN `intermediaire_id` BIGINT UNSIGNED NULL AFTER `home_longitude`
            """)
            print("   ✅ intermediaire_id ajoutée")
        else:
            print("   ✓ intermediaire_id existe déjà")
        
        # Supprimer les anciens index s'ils existent
        cursor.execute("""
            SELECT INDEX_NAME 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'promotion_members'
            AND INDEX_NAME LIKE '%intermediary%'
        """, (DB_NAME,))
        old_indexes = [row[0] for row in cursor.fetchall()]
        
        for idx in old_indexes:
            print(f"   🗑️  Suppression de l'ancien index: {idx}")
            cursor.execute(f"ALTER TABLE `promotion_members` DROP INDEX `{idx}`")
        
        # Créer les nouveaux index
        cursor.execute("""
            SELECT INDEX_NAME 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'promotion_members'
            AND INDEX_NAME = 'idx_promomember_intermediary'
        """, (DB_NAME,))
        if not cursor.fetchone():
            print("   ➕ Création de l'index intermediaire...")
            cursor.execute("""
                ALTER TABLE `promotion_members`
                ADD INDEX `idx_promomember_intermediary` (`intermediaire_id`)
            """)
            print("   ✅ Index intermediaire créé")
        else:
            print("   ✓ Index intermediaire existe déjà")
        
        cursor.execute("""
            SELECT INDEX_NAME 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'promotion_members'
            AND INDEX_NAME = 'idx_promomember_location'
        """, (DB_NAME,))
        if not cursor.fetchone():
            print("   ➕ Création de l'index location...")
            cursor.execute("""
                ALTER TABLE `promotion_members`
                ADD INDEX `idx_promomember_location` (`home_latitude`, `home_longitude`)
            """)
            print("   ✅ Index location créé")
        else:
            print("   ✓ Index location existe déjà")
        
        # Vérifier la contrainte FK
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'promotion_members'
            AND CONSTRAINT_NAME LIKE '%intermediary%'
        """, (DB_NAME,))
        old_fks = [row[0] for row in cursor.fetchall()]
        
        for fk in old_fks:
            print(f"   🗑️  Suppression de l'ancienne FK: {fk}")
            cursor.execute(f"ALTER TABLE `promotion_members` DROP FOREIGN KEY `{fk}`")
        
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'promotion_members'
            AND CONSTRAINT_NAME = 'fk_promomember_intermediary'
        """, (DB_NAME,))
        if not cursor.fetchone():
            print("   ➕ Création de la contrainte FK...")
            cursor.execute("""
                ALTER TABLE `promotion_members`
                ADD CONSTRAINT `fk_promomember_intermediary` 
                FOREIGN KEY (`intermediaire_id`) REFERENCES `promotion_members` (`id`) 
                ON UPDATE CASCADE ON DELETE SET NULL
            """)
            print("   ✅ Contrainte FK créée")
        else:
            print("   ✓ Contrainte FK existe déjà")
        
        connection.commit()
        print("\n✅ Toutes les corrections ont été appliquées avec succès!")
        
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'connection' in locals():
        connection.close()

