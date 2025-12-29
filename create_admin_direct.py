#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer l'utilisateur admin directement avec la bonne configuration
"""

import pymysql
from werkzeug.security import generate_password_hash
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW

def create_admin_direct():
    """Créer l'utilisateur admin directement via MySQL"""
    try:
        # Connexion directe à MySQL
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD_RAW,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 1. Créer le rôle admin s'il n'existe pas
        cursor.execute("""
            INSERT INTO `roles` (`name`, `code`, `permissions`, `description`, `created_at`)
            SELECT 'Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW()
            WHERE NOT EXISTS (SELECT 1 FROM `roles` WHERE `code` = 'admin')
        """)
        
        # 2. Récupérer l'ID du rôle admin
        cursor.execute("SELECT id FROM roles WHERE code = 'admin' LIMIT 1")
        result = cursor.fetchone()
        admin_role_id = result[0] if result else None
        
        if not admin_role_id:
            print("❌ Impossible de trouver ou créer le rôle admin")
            return False
        
        # 3. Générer le hash du mot de passe
        password_hash = generate_password_hash('admin123')
        
        # 4. Vérifier si l'utilisateur existe
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Mettre à jour l'utilisateur existant
            cursor.execute("""
                UPDATE `users` 
                SET `password_hash` = %s,
                    `role_id` = %s,
                    `is_active` = 1,
                    `email` = 'admin@importprofit.pro',
                    `full_name` = 'Administrateur'
                WHERE `username` = 'admin'
            """, (password_hash, admin_role_id))
            print("✅ Utilisateur admin mis à jour")
        else:
            # Créer l'utilisateur
            cursor.execute("""
                INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
            """, ('admin', 'admin@importprofit.pro', password_hash, 'Administrateur', admin_role_id))
            print("✅ Utilisateur admin créé")
        
        connection.commit()
        
        # Afficher les informations
        cursor.execute("SELECT id, username, email, role_id, is_active FROM users WHERE username = 'admin'")
        user_info = cursor.fetchone()
        
        if user_info:
            print(f"   ID: {user_info[0]}")
            print(f"   Username: {user_info[1]}")
            print(f"   Email: {user_info[2]}")
            print(f"   Role ID: {user_info[3]}")
            print(f"   Actif: {user_info[4]}")
        
        cursor.close()
        connection.close()
        
        print("\n✅ Utilisateur admin prêt!")
        print("   Username: admin")
        print("   Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔄 Création de l'utilisateur admin...")
    print("=" * 60)
    print(f"Base de données: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("=" * 60)
    success = create_admin_direct()
    if not success:
        exit(1)

