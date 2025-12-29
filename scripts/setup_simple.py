#!/usr/bin/env python3
"""
Script simple de configuration de la base de données MySQL
Import Profit Pro
"""

import os
import sys
import pymysql

# Ajouter le répertoire parent au path pour importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
except ImportError:
    print("❌ Erreur: Impossible d'importer la configuration de la base de données")
    print("Assurez-vous que le fichier config.py existe et contient les bonnes variables")
    sys.exit(1)

def main():
    """Fonction principale"""
    print("🚀 CONFIGURATION SIMPLE DE LA BASE DE DONNÉES")
    print("=" * 50)
    print(f"🗄️ Base de données: {DB_NAME}")
    print(f"🌐 Serveur: {DB_HOST}:{DB_PORT}")
    print("=" * 50)
    
    try:
        # Connexion à la base de données
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD_RAW,
            database=DB_NAME,
            charset='utf8mb4',
            autocommit=True
        )
        print("✅ Connexion à la base de données réussie")
        
        # Chemin vers le fichier SQL
        sql_file_path = os.path.join(os.path.dirname(__file__), 'simple_database_setup.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"❌ Fichier SQL non trouvé: {sql_file_path}")
            return 1
        
        print(f"📄 Fichier SQL trouvé: {sql_file_path}")
        
        # Lire et exécuter le fichier SQL
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        cursor = connection.cursor()
        
        # Diviser le contenu en requêtes individuelles
        queries = [query.strip() for query in sql_content.split(';') if query.strip() and not query.strip().startswith('--')]
        
        print(f"🔄 Exécution de {len(queries)} requêtes...")
        
        for i, query in enumerate(queries, 1):
            if query:
                try:
                    cursor.execute(query)
                    if i % 10 == 0:  # Afficher le progrès tous les 10 requêtes
                        print(f"✅ {i}/{len(queries)} requêtes exécutées")
                except Exception as e:
                    print(f"⚠️ Erreur requête {i}: {e}")
                    continue
        
        print("✅ Toutes les requêtes exécutées")
        
        # Vérifier les tables créées
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ {len(tables)} tables créées")
        
        # Vérifier les données
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        print(f"✅ {articles_count} articles insérés")
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        categories_count = cursor.fetchone()[0]
        print(f"✅ {categories_count} catégories insérées")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 50)
        print("✅ Base de données configurée")
        print("✅ Tables créées")
        print("✅ Données insérées")
        print("=" * 50)
        print("🌐 Votre application Flask peut maintenant fonctionner!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
