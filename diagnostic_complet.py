#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic complet de l'utilisateur admin
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import check_password_hash, generate_password_hash

def diagnostic_complet():
    """Diagnostic complet"""
    with app.app_context():
        try:
            print("=" * 70)
            print("DIAGNOSTIC COMPLET - UTILISATEUR ADMIN")
            print("=" * 70)
            
            # 1. Vérifier la connexion
            try:
                db.engine.connect()
                print("✅ Connexion à la base de données: OK")
            except Exception as e:
                print(f"❌ Erreur de connexion: {e}")
                return False
            
            # 2. Vérifier le rôle
            print("\n" + "-" * 70)
            print("1. VÉRIFICATION DU RÔLE ADMIN")
            print("-" * 70)
            admin_role = Role.query.filter_by(code='admin').first()
            if admin_role:
                print(f"   ✅ Rôle trouvé:")
                print(f"      ID: {admin_role.id}")
                print(f"      Nom: {admin_role.name}")
                print(f"      Code: {admin_role.code}")
                print(f"      Permissions: {admin_role.permissions}")
            else:
                print("   ❌ Rôle admin NON TROUVÉ")
                print("   💡 Création du rôle...")
                admin_role = Role(
                    name='Administrateur',
                    code='admin',
                    permissions={'all': ['*']},
                    description='Accès complet'
                )
                db.session.add(admin_role)
                db.session.commit()
                print("   ✅ Rôle créé")
            
            # 3. Vérifier l'utilisateur
            print("\n" + "-" * 70)
            print("2. VÉRIFICATION DE L'UTILISATEUR ADMIN")
            print("-" * 70)
            
            # Chercher par username
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("   ❌ Utilisateur 'admin' NON TROUVÉ par username")
                
                # Chercher tous les utilisateurs
                all_users = User.query.all()
                print(f"\n   📋 Tous les utilisateurs dans la base ({len(all_users)}):")
                for u in all_users:
                    print(f"      - ID: {u.id}, Username: {getattr(u, 'username', 'N/A')}, Email: {getattr(u, 'email', 'N/A')}")
                
                print("\n   💡 Création de l'utilisateur admin...")
                password_hash = generate_password_hash('admin123')
                admin_user = User(
                    username='admin',
                    email='admin@importprofit.pro',
                    password_hash=password_hash,
                    full_name='Administrateur',
                    role_id=admin_role.id,
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("   ✅ Utilisateur admin créé")
            else:
                print(f"   ✅ Utilisateur trouvé:")
                print(f"      ID: {admin_user.id}")
                print(f"      Username: {admin_user.username}")
                print(f"      Email: {admin_user.email}")
                print(f"      Full Name: {admin_user.full_name}")
                print(f"      Role ID: {admin_user.role_id}")
                print(f"      Actif: {admin_user.is_active}")
            
            # 4. Vérifier le hash
            print("\n" + "-" * 70)
            print("3. VÉRIFICATION DU HASH DU MOT DE PASSE")
            print("-" * 70)
            
            if not admin_user.password_hash:
                print("   ❌ Pas de hash de mot de passe!")
                print("   💡 Génération d'un nouveau hash...")
                admin_user.password_hash = generate_password_hash('admin123')
                db.session.commit()
                print("   ✅ Hash généré et sauvegardé")
            else:
                print(f"   ✅ Hash présent: {admin_user.password_hash[:60]}...")
                
                # Tester le hash
                test_password = 'admin123'
                is_valid = check_password_hash(admin_user.password_hash, test_password)
                
                if is_valid:
                    print(f"   ✅ Test avec 'admin123': VALIDE")
                else:
                    print(f"   ❌ Test avec 'admin123': INVALIDE")
                    print("   💡 Génération d'un nouveau hash...")
                    admin_user.password_hash = generate_password_hash('admin123')
                    db.session.commit()
                    print("   ✅ Nouveau hash généré et sauvegardé")
            
            # 5. Vérifier la relation
            print("\n" + "-" * 70)
            print("4. VÉRIFICATION DE LA RELATION AVEC LE RÔLE")
            print("-" * 70)
            
            # Recharger l'utilisateur pour avoir la relation
            db.session.refresh(admin_user)
            
            if admin_user.role:
                print(f"   ✅ Relation OK:")
                print(f"      Rôle: {admin_user.role.name} ({admin_user.role.code})")
            else:
                print("   ⚠️ Pas de relation chargée")
                if admin_user.role_id:
                    role_check = Role.query.get(admin_user.role_id)
                    if role_check:
                        print(f"   ✅ Le rôle existe (ID: {role_check.id}, Code: {role_check.code})")
                        print("   💡 La relation devrait fonctionner")
                    else:
                        print(f"   ❌ Le rôle avec ID {admin_user.role_id} n'existe pas")
                        print("   💡 Attribution du rôle admin...")
                        admin_user.role_id = admin_role.id
                        db.session.commit()
                        print("   ✅ Rôle attribué")
            
            # 6. Test final complet
            print("\n" + "-" * 70)
            print("5. TEST FINAL DE CONNEXION")
            print("-" * 70)
            
            # Recharger depuis la base
            db.session.expire_all()
            final_user = User.query.filter_by(username='admin').first()
            
            if final_user:
                print(f"   ✅ Utilisateur récupéré: {final_user.username}")
                print(f"   ✅ Email: {final_user.email}")
                print(f"   ✅ Actif: {final_user.is_active}")
                print(f"   ✅ Hash présent: {'Oui' if final_user.password_hash else 'Non'}")
                
                if final_user.password_hash:
                    is_valid = check_password_hash(final_user.password_hash, 'admin123')
                    if is_valid:
                        print(f"   ✅ Mot de passe 'admin123': VALIDE")
                    else:
                        print(f"   ❌ Mot de passe 'admin123': INVALIDE")
                
                if final_user.role_id:
                    role_final = Role.query.get(final_user.role_id)
                    if role_final:
                        print(f"   ✅ Rôle associé: {role_final.name} ({role_final.code})")
                    else:
                        print(f"   ❌ Rôle avec ID {final_user.role_id} n'existe pas")
            
            # 7. Résumé
            print("\n" + "=" * 70)
            print("RÉSUMÉ")
            print("=" * 70)
            
            final_check = User.query.filter_by(username='admin').first()
            if final_check and final_check.password_hash and final_check.is_active:
                test_final = check_password_hash(final_check.password_hash, 'admin123')
                if test_final:
                    print("✅ L'utilisateur admin est correctement configuré!")
                    print("\n📝 Identifiants:")
                    print("   Username: admin")
                    print("   Password: admin123")
                    print("\n🌐 URL de connexion:")
                    print("   http://localhost:5002/auth/login")
                    print("\n💡 Si la connexion ne fonctionne toujours pas:")
                    print("   1. Vérifiez les logs Flask dans le terminal")
                    print("   2. Cherchez les messages 'DEBUG:'")
                    print("   3. Redémarrez Flask après avoir créé l'utilisateur")
                    return True
                else:
                    print("❌ Le hash du mot de passe n'est pas valide")
                    print("   💡 Le hash a été régénéré, redémarrez Flask")
            else:
                print("❌ Configuration incomplète")
                print("   💡 Vérifiez les détails ci-dessus")
            
            return False
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = diagnostic_complet()
    sys.exit(0 if success else 1)

