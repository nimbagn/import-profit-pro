#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic complet pour l'utilisateur admin sur Render
Vérifie tous les aspects qui peuvent empêcher la connexion
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import check_password_hash
from datetime import datetime, UTC

def diagnostic_complet():
    """Diagnostic complet de l'utilisateur admin"""
    with app.app_context():
        print("=" * 70)
        print("🔍 DIAGNOSTIC COMPLET - UTILISATEUR ADMIN")
        print("=" * 70)
        print()
        
        # 1. Vérifier la connexion à la base de données
        print("1️⃣ VÉRIFICATION DE LA BASE DE DONNÉES")
        print("-" * 70)
        try:
            # Test de connexion
            db.session.execute(db.text('SELECT 1'))
            print("✅ Connexion à la base de données: OK")
            
            # Vérifier que la table users existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'users' in tables:
                print("✅ Table 'users' existe")
            else:
                print("❌ Table 'users' n'existe pas")
                print("   → Exécutez les migrations nécessaires")
                return False
            
            if 'roles' in tables:
                print("✅ Table 'roles' existe")
            else:
                print("❌ Table 'roles' n'existe pas")
                print("   → Exécutez les migrations nécessaires")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion à la base de données: {e}")
            return False
        
        print()
        
        # 2. Vérifier l'utilisateur admin
        print("2️⃣ VÉRIFICATION DE L'UTILISATEUR ADMIN")
        print("-" * 70)
        
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ Utilisateur 'admin' NON TROUVÉ")
            print()
            print("💡 Solution:")
            print("   python3 create_admin_render.py")
            return False
        
        print(f"✅ Utilisateur 'admin' trouvé")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Nom complet: {admin_user.full_name or 'N/A'}")
        print()
        
        # 3. Vérifier le statut actif
        print("3️⃣ STATUT DU COMPTE")
        print("-" * 70)
        if admin_user.is_active:
            print("✅ Compte ACTIF")
        else:
            print("❌ Compte INACTIF")
            print()
            print("💡 Solution:")
            print("   python3 -c \"")
            print("   from app import app")
            print("   from models import User")
            print("   with app.app_context():")
            print("       admin = User.query.filter_by(username='admin').first()")
            print("       admin.is_active = True")
            print("       db.session.commit()")
            print("       print('✅ Compte activé')")
            print("   \"")
            return False
        
        print()
        
        # 4. Vérifier le mot de passe
        print("4️⃣ VÉRIFICATION DU MOT DE PASSE")
        print("-" * 70)
        
        if not admin_user.password_hash:
            print("❌ Aucun hash de mot de passe")
            print()
            print("💡 Solution:")
            print("   python3 create_admin_render.py --reset-password")
            return False
        
        pwd_length = len(admin_user.password_hash)
        print(f"✅ Hash de mot de passe présent ({pwd_length} caractères)")
        
        # Tester différents mots de passe courants
        test_passwords = ['admin123', 'admin', 'password', 'Admin123']
        valid_password = None
        
        for test_pwd in test_passwords:
            if check_password_hash(admin_user.password_hash, test_pwd):
                valid_password = test_pwd
                break
        
        if valid_password:
            print(f"✅ Mot de passe valide trouvé: '{valid_password}'")
        else:
            print("⚠️  Aucun mot de passe testé n'est valide")
            print("   Mots de passe testés:", ', '.join(test_passwords))
            print()
            print("💡 Solution: Réinitialiser le mot de passe")
            print("   python3 create_admin_render.py --reset-password")
            return False
        
        print()
        
        # 5. Vérifier le rôle
        print("5️⃣ VÉRIFICATION DU RÔLE")
        print("-" * 70)
        
        if not admin_user.role_id:
            print("❌ Aucun rôle_id assigné")
            print()
            print("💡 Solution:")
            print("   python3 -c \"")
            print("   from app import app")
            print("   from models import User, Role")
            print("   with app.app_context():")
            print("       admin = User.query.filter_by(username='admin').first()")
            print("       admin_role = Role.query.filter_by(code='admin').first()")
            print("       if admin_role:")
            print("           admin.role_id = admin_role.id")
            print("           db.session.commit()")
            print("           print('✅ Rôle assigné')")
            print("   \"")
            return False
        
        if admin_user.role:
            print(f"✅ Rôle assigné: {admin_user.role.name} ({admin_user.role.code})")
        else:
            print(f"⚠️  role_id={admin_user.role_id} mais le rôle n'existe pas")
            print()
            print("💡 Vérifiez que le rôle admin existe dans la table roles")
            return False
        
        print()
        
        # 6. Vérifier SECRET_KEY
        print("6️⃣ VÉRIFICATION DE LA CONFIGURATION")
        print("-" * 70)
        
        secret_key = app.config.get('SECRET_KEY')
        if secret_key:
            if len(secret_key) >= 32:
                print(f"✅ SECRET_KEY configurée ({len(secret_key)} caractères)")
            else:
                print(f"⚠️  SECRET_KEY trop courte ({len(secret_key)} caractères)")
                print("   Recommandé: au moins 32 caractères")
        else:
            print("❌ SECRET_KEY non configurée")
            print()
            print("💡 Solution:")
            print("   Dans Render Dashboard > Environment, ajoutez:")
            print("   SECRET_KEY=<générez une clé avec: python3 generate_secret_key.py>")
        
        print()
        
        # 7. Résumé et recommandations
        print("=" * 70)
        print("📋 RÉSUMÉ")
        print("=" * 70)
        print()
        print("✅ Utilisateur admin: OK")
        print(f"✅ Compte actif: OK")
        print(f"✅ Mot de passe: OK (testé avec '{valid_password}')")
        print(f"✅ Rôle: OK ({admin_user.role.name if admin_user.role else 'N/A'})")
        print()
        print("🔐 IDENTIFIANTS DE CONNEXION:")
        print(f"   Username: admin")
        print(f"   Password: {valid_password}")
        print()
        print("🌐 URL de connexion:")
        print("   https://import-profit-pro.onrender.com/auth/login")
        print()
        
        # 8. Si tout est OK mais que ça ne fonctionne pas
        print("=" * 70)
        print("⚠️  SI LA CONNEXION NE FONCTIONNE TOUJOURS PAS")
        print("=" * 70)
        print()
        print("1. Vérifiez les logs Render:")
        print("   Dashboard > Service > Logs")
        print()
        print("2. Vérifiez les cookies dans le navigateur:")
        print("   - Ouvrez les outils de développement (F12)")
        print("   - Onglet Application > Cookies")
        print("   - Vérifiez que les cookies de session sont créés")
        print()
        print("3. Essayez en navigation privée:")
        print("   - Parfois les cookies/cache peuvent causer des problèmes")
        print()
        print("4. Vérifiez que SECRET_KEY est bien configurée dans Render")
        print()
        print("5. Redémarrez le service Render si nécessaire")
        print()
        
        return True

if __name__ == '__main__':
    success = diagnostic_complet()
    sys.exit(0 if success else 1)

