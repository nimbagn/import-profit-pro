#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier si l'utilisateur admin existe dans la base de données
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import check_password_hash

def verifier_admin():
    """Vérifier l'état de l'utilisateur admin"""
    with app.app_context():
        try:
            print("=" * 60)
            print("VÉRIFICATION DE L'UTILISATEUR ADMIN")
            print("=" * 60)
            
            # 1. Vérifier le rôle admin
            print("\n1. Vérification du rôle admin...")
            admin_role = Role.query.filter_by(code='admin').first()
            
            if admin_role:
                print(f"   ✅ Rôle admin trouvé")
                print(f"      ID: {admin_role.id}")
                print(f"      Nom: {admin_role.name}")
                print(f"      Code: {admin_role.code}")
            else:
                print("   ❌ Rôle admin NON TROUVÉ")
                print("   💡 Exécutez: mysql -u root -p madargn < CREER_ADMIN.sql")
                return False
            
            # 2. Vérifier l'utilisateur admin
            print("\n2. Vérification de l'utilisateur admin...")
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("   ❌ Utilisateur admin NON TROUVÉ")
                print("   💡 Exécutez: mysql -u root -p madargn < CREER_ADMIN.sql")
                return False
            
            print(f"   ✅ Utilisateur admin trouvé")
            print(f"      ID: {admin_user.id}")
            print(f"      Username: {admin_user.username}")
            print(f"      Email: {admin_user.email}")
            print(f"      Full Name: {admin_user.full_name}")
            print(f"      Role ID: {admin_user.role_id}")
            print(f"      Actif: {admin_user.is_active}")
            
            # 3. Vérifier le hash du mot de passe
            print("\n3. Vérification du hash du mot de passe...")
            if not admin_user.password_hash:
                print("   ❌ Pas de hash de mot de passe!")
                print("   💡 Exécutez: mysql -u root -p madargn < CREER_ADMIN.sql")
                return False
            
            print(f"   ✅ Hash présent: {admin_user.password_hash[:50]}...")
            
            # 4. Tester le mot de passe
            print("\n4. Test du mot de passe 'admin123'...")
            is_valid = check_password_hash(admin_user.password_hash, 'admin123')
            
            if is_valid:
                print("   ✅ Le mot de passe est VALIDE")
            else:
                print("   ❌ Le mot de passe est INVALIDE")
                print("   💡 Exécutez: mysql -u root -p madargn < CREER_ADMIN.sql")
                return False
            
            # 5. Vérifier la relation avec le rôle
            print("\n5. Vérification de la relation avec le rôle...")
            if admin_user.role:
                print(f"   ✅ Rôle associé: {admin_user.role.name} ({admin_user.role.code})")
            else:
                print("   ⚠️ Pas de rôle associé (mais role_id existe)")
                if admin_user.role_id:
                    role_check = Role.query.get(admin_user.role_id)
                    if role_check:
                        print(f"      Le rôle existe (ID: {role_check.id}, Code: {role_check.code})")
                    else:
                        print(f"      ⚠️ Le rôle avec ID {admin_user.role_id} n'existe pas")
            
            # 6. Résumé
            print("\n" + "=" * 60)
            print("RÉSUMÉ")
            print("=" * 60)
            
            if admin_user and admin_user.password_hash and is_valid and admin_user.is_active:
                print("✅ L'utilisateur admin est correctement configuré!")
                print("\nIdentifiants de connexion:")
                print("   Username: admin")
                print("   Password: admin123")
                print("\nVous pouvez maintenant vous connecter sur:")
                print("   http://localhost:5002/auth/login")
                return True
            else:
                print("❌ L'utilisateur admin n'est pas correctement configuré")
                print("\nActions à effectuer:")
                print("   1. Exécutez: mysql -u root -p madargn < CREER_ADMIN.sql")
                print("   2. Redémarrez Flask")
                print("   3. Essayez de vous connecter")
                return False
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la vérification: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = verifier_admin()
    sys.exit(0 if success else 1)

