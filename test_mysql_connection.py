#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour tester la connexion MySQL et proposer des solutions"""

import pymysql
import sys

def test_connection(host, port, user, password, database):
    """Teste une connexion MySQL"""
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT VERSION()')
        version = cursor.fetchone()
        cursor.execute('SELECT COUNT(*) FROM commercial_orders')
        count = cursor.fetchone()
        cursor.execute('SELECT id, reference FROM commercial_orders LIMIT 5')
        orders = cursor.fetchall()
        conn.close()
        return True, version[0], count[0], orders
    except pymysql.Error as e:
        return False, str(e), None, None

def main():
    print("=" * 60)
    print("🔍 TEST DE CONNEXION MYSQL")
    print("=" * 60)
    print()
    
    # Configuration actuelle
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    print("📋 Configuration actuelle:")
    print(f"   Host: {DB_HOST}")
    print(f"   Port: {DB_PORT}")
    print(f"   Database: {DB_NAME}")
    print(f"   User: {DB_USER}")
    print(f"   Password: {'*' * len(DB_PASSWORD_RAW) if DB_PASSWORD_RAW else 'Non défini'}")
    print()
    
    # Test avec la configuration actuelle
    print("🔍 Test de connexion avec la configuration actuelle...")
    success, result, count, orders = test_connection(
        DB_HOST, DB_PORT, DB_USER, DB_PASSWORD_RAW, DB_NAME
    )
    
    if success:
        print("✅ Connexion réussie!")
        print(f"   Version MySQL: {result}")
        print(f"   Nombre de commandes: {count}")
        if orders:
            print("   Exemples de commandes:")
            for order_id, ref in orders:
                print(f"      - ID {order_id}: {ref}")
        return 0
    else:
        print(f"❌ Connexion échouée: {result}")
        print()
        print("💡 Solutions possibles:")
        print()
        print("1️⃣  Créer un fichier .env avec les bonnes valeurs:")
        print("   Créez un fichier .env à la racine du projet avec:")
        print("   DB_HOST=127.0.0.1")
        print("   DB_PORT=3306")
        print("   DB_NAME=madargn")
        print("   DB_USER=root")
        print("   DB_PASSWORD=votre_mot_de_passe_mysql")
        print()
        print("2️⃣  Vérifier que MySQL est démarré:")
        print("   sudo service mysql start  # Linux")
        print("   brew services start mysql  # macOS")
        print()
        print("3️⃣  Vérifier les identifiants MySQL:")
        print("   mysql -u root -p")
        print("   SHOW DATABASES;")
        print("   USE madargn;")
        print("   SHOW TABLES;")
        print()
        print("4️⃣  Tester avec un mot de passe vide:")
        print("   DB_PASSWORD= python3 test_mysql_connection.py")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())

