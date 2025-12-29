#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter la colonne client_phone aux tables MySQL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    print(f"🔌 Connexion à MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # Se connecter directement à MySQL
    connection = pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD_RAW,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    print("✅ Connexion MySQL réussie")
    
    try:
        with connection.cursor() as cursor:
            # Vérifier si la colonne existe dans stock_outgoings
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'stock_outgoings'
                  AND COLUMN_NAME = 'client_phone'
            """, (DB_NAME,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                print("🔄 Ajout de la colonne client_phone à stock_outgoings...")
                cursor.execute("""
                    ALTER TABLE stock_outgoings 
                    ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name
                """)
                connection.commit()
                print("✅ Colonne client_phone ajoutée à stock_outgoings")
            else:
                print("✅ La colonne client_phone existe déjà dans stock_outgoings")
            
            # Vérifier si la colonne existe dans stock_returns
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'stock_returns'
                  AND COLUMN_NAME = 'client_phone'
            """, (DB_NAME,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                print("🔄 Ajout de la colonne client_phone à stock_returns...")
                cursor.execute("""
                    ALTER TABLE stock_returns 
                    ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name
                """)
                connection.commit()
                print("✅ Colonne client_phone ajoutée à stock_returns")
            else:
                print("✅ La colonne client_phone existe déjà dans stock_returns")
        
        print("\n✅ Mise à jour MySQL terminée avec succès !")
        connection.close()
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
        connection.rollback()
        connection.close()
        sys.exit(1)
        
except pymysql.err.OperationalError as e:
    if "Access denied" in str(e):
        print("❌ Erreur d'authentification MySQL")
        print(f"   Vérifiez vos identifiants dans config.py ou variables d'environnement")
        print(f"   DB_USER: {DB_USER}")
        print(f"   DB_HOST: {DB_HOST}")
        print("\n💡 Alternative: Exécutez manuellement le script SQL:")
        print(f"   mysql -u {DB_USER} -p {DB_NAME} < scripts/add_client_phone_mysql_simple.sql")
    else:
        print(f"❌ Erreur MySQL: {e}")
    sys.exit(1)
except ImportError:
    print("❌ pymysql n'est pas installé")
    print("   Installez-le avec: pip install pymysql")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

