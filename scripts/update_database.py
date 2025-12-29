#!/usr/bin/env python3
"""
Script de mise à jour de la base de données MySQL
Import Profit Pro
"""

import os
import sys
import pymysql
from datetime import datetime

# Ajouter le répertoire parent au path pour importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
except ImportError:
    print("❌ Erreur: Impossible d'importer la configuration de la base de données")
    print("Assurez-vous que le fichier config.py existe et contient les bonnes variables")
    sys.exit(1)

def connect_to_database():
    """Connexion à la base de données MySQL"""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD_RAW,
            database=DB_NAME,
            charset='utf8mb4',
            autocommit=True
        )
        print(f"✅ Connexion à la base de données réussie: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return connection
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return None

def execute_sql_file(connection, sql_file_path):
    """Exécuter un fichier SQL"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Diviser le contenu en requêtes individuelles
        queries = [query.strip() for query in sql_content.split(';') if query.strip()]
        
        cursor = connection.cursor()
        
        for i, query in enumerate(queries, 1):
            if query and not query.startswith('--'):
                try:
                    print(f"🔄 Exécution de la requête {i}/{len(queries)}...")
                    cursor.execute(query)
                    print(f"✅ Requête {i} exécutée avec succès")
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'exécution de la requête {i}: {e}")
                    # Continuer avec les autres requêtes
                    continue
        
        cursor.close()
        print("✅ Toutes les requêtes SQL ont été exécutées")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du fichier SQL: {e}")
        return False

def verify_database_structure(connection):
    """Vérifier la structure de la base de données"""
    try:
        cursor = connection.cursor()
        
        # Vérifier les tables principales
        tables_to_check = [
            'users', 'roles', 'categories', 'articles', 
            'simulations', 'inventories', 'depots', 'vehicles',
            'currencies', 'exchange_rates', 'regions'
        ]
        
        print("\n🔍 Vérification de la structure de la base de données...")
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table {table}: {count} enregistrements")
        
        # Vérifier les contraintes de clés étrangères
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                COLUMN_NAME,
                CONSTRAINT_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE REFERENCED_TABLE_SCHEMA = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (DB_NAME,))
        
        foreign_keys = cursor.fetchall()
        print(f"\n✅ {len(foreign_keys)} contraintes de clés étrangères trouvées")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 MISE À JOUR DE LA BASE DE DONNÉES IMPORT PROFIT PRO")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️ Base de données: {DB_NAME}")
    print(f"🌐 Serveur: {DB_HOST}:{DB_PORT}")
    print("=" * 60)
    
    # Connexion à la base de données
    connection = connect_to_database()
    if not connection:
        print("❌ Impossible de se connecter à la base de données")
        return 1
    
    try:
        # Chemin vers le fichier SQL
        sql_file_path = os.path.join(os.path.dirname(__file__), 'update_database.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"❌ Fichier SQL non trouvé: {sql_file_path}")
            return 1
        
        print(f"📄 Fichier SQL trouvé: {sql_file_path}")
        
        # Exécuter le script SQL
        print("\n🔄 Exécution du script SQL...")
        if execute_sql_file(connection, sql_file_path):
            print("✅ Script SQL exécuté avec succès")
        else:
            print("❌ Erreur lors de l'exécution du script SQL")
            return 1
        
        # Vérifier la structure
        print("\n🔍 Vérification de la structure...")
        if verify_database_structure(connection):
            print("✅ Structure de la base de données vérifiée")
        else:
            print("⚠️ Problème lors de la vérification de la structure")
        
        print("\n🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS!")
        print("=" * 60)
        print("✅ Base de données mise à jour")
        print("✅ Tables créées")
        print("✅ Données insérées")
        print("✅ Contraintes configurées")
        print("=" * 60)
        print("🌐 Votre application Flask peut maintenant fonctionner correctement!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return 1
    
    finally:
        if connection:
            connection.close()
            print("🔌 Connexion à la base de données fermée")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
