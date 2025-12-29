#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier et créer/corriger l'utilisateur admin
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(__file__))

try:
    from werkzeug.security import generate_password_hash, check_password_hash
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    print("=" * 60)
    print("VÉRIFICATION ET CRÉATION DE L'UTILISATEUR ADMIN")
    print("=" * 60)
    print(f"Base de données: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print("=" * 60)
    
    # Essayer de se connecter
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD_RAW,
            database=DB_NAME,
            charset='utf8mb4'
        )
        print("✅ Connexion à la base de données réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Essayez de vous connecter manuellement à MySQL et exécutez:")
        print("   mysql -u root -p madargn")
        sys.exit(1)
    
    cursor = connection.cursor()
    
    # 1. Vérifier la structure de la table users
    print("\n📋 Vérification de la structure de la table 'users'...")
    cursor.execute("DESCRIBE users")
    columns = cursor.fetchall()
    column_names = [col[0] for col in columns]
    print(f"   Colonnes trouvées: {', '.join(column_names)}")
    
    if 'username' not in column_names:
        print("❌ La colonne 'username' n'existe pas dans la table users!")
        print("   Exécutez d'abord le script fix_missing_columns.sql")
        sys.exit(1)
    
    if 'password_hash' not in column_names:
        print("❌ La colonne 'password_hash' n'existe pas dans la table users!")
        print("   Exécutez d'abord le script fix_missing_columns.sql")
        sys.exit(1)
    
    # 2. Vérifier/Créer le rôle admin
    print("\n📋 Vérification du rôle admin...")
    cursor.execute("SELECT id, name, code FROM roles WHERE code = 'admin'")
    admin_role = cursor.fetchone()
    
    if not admin_role:
        print("   ⚠️ Le rôle admin n'existe pas. Création...")
        cursor.execute("""
            INSERT INTO roles (name, code, permissions, description, created_at)
            VALUES ('Administrateur', 'admin', '{"all": ["*"]}', 'Accès complet à toutes les fonctionnalités', NOW())
        """)
        connection.commit()
        cursor.execute("SELECT id, name, code FROM roles WHERE code = 'admin'")
        admin_role = cursor.fetchone()
        print(f"   ✅ Rôle admin créé (ID: {admin_role[0]})")
    else:
        print(f"   ✅ Rôle admin existe (ID: {admin_role[0]}, Name: {admin_role[1]})")
    
    admin_role_id = admin_role[0]
    
    # 3. Vérifier l'utilisateur admin
    print("\n📋 Vérification de l'utilisateur admin...")
    cursor.execute("SELECT id, username, email, password_hash, role_id, is_active FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    # Générer le hash du mot de passe
    password = 'admin123'
    password_hash = generate_password_hash(password)
    
    if admin_user:
        print(f"   ✅ Utilisateur admin existe (ID: {admin_user[0]})")
        print(f"   Email: {admin_user[2]}")
        print(f"   Role ID: {admin_user[4]}")
        print(f"   Actif: {admin_user[5]}")
        
        # Vérifier le hash actuel
        current_hash = admin_user[3]
        if current_hash and check_password_hash(current_hash, password):
            print("   ✅ Le mot de passe actuel est correct")
        else:
            print("   ⚠️ Le mot de passe actuel est incorrect ou manquant. Mise à jour...")
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s,
                    role_id = %s,
                    is_active = 1,
                    email = COALESCE(email, 'admin@importprofit.pro'),
                    full_name = COALESCE(full_name, 'Administrateur')
                WHERE username = 'admin'
            """, (password_hash, admin_role_id))
            connection.commit()
            print("   ✅ Mot de passe mis à jour")
    else:
        print("   ⚠️ L'utilisateur admin n'existe pas. Création...")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role_id, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, 1, NOW())
        """, ('admin', 'admin@importprofit.pro', password_hash, 'Administrateur', admin_role_id))
        connection.commit()
        print("   ✅ Utilisateur admin créé")
    
    # 4. Vérification finale
    print("\n📋 Vérification finale...")
    cursor.execute("SELECT id, username, email, role_id, is_active FROM users WHERE username = 'admin'")
    final_user = cursor.fetchone()
    
    if final_user:
        print("   ✅ Utilisateur admin vérifié:")
        print(f"      ID: {final_user[0]}")
        print(f"      Username: {final_user[1]}")
        print(f"      Email: {final_user[2]}")
        print(f"      Role ID: {final_user[3]}")
        print(f"      Actif: {final_user[4]}")
        
        # Test du hash
        cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
        hash_result = cursor.fetchone()
        if hash_result and check_password_hash(hash_result[0], password):
            print("   ✅ Le hash du mot de passe est valide")
        else:
            print("   ⚠️ Le hash du mot de passe n'est pas valide")
    
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 60)
    print("✅ TERMINÉ!")
    print("=" * 60)
    print("Identifiants de connexion:")
    print("   Username: admin")
    print("   Password: admin123")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("   Assurez-vous que tous les modules sont installés")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

