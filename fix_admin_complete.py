#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script complet pour créer/corriger l'utilisateur admin
Utilise directement la connexion Flask pour éviter les problèmes de configuration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import generate_password_hash, check_password_hash

def fix_admin():
    """Créer ou corriger l'utilisateur admin"""
    with app.app_context():
        try:
            print("=" * 60)
            print("CRÉATION/CORRECTION DE L'UTILISATEUR ADMIN")
            print("=" * 60)
            
            # 1. Vérifier/Créer le rôle admin
            print("\n1. Vérification du rôle admin...")
            admin_role = Role.query.filter_by(code='admin').first()
            
            if not admin_role:
                print("   ⚠️ Rôle admin non trouvé. Création...")
                admin_role = Role(
                    name='Administrateur',
                    code='admin',
                    permissions={'all': ['*']},
                    description='Accès complet à toutes les fonctionnalités'
                )
                db.session.add(admin_role)
                db.session.commit()
                print("   ✅ Rôle admin créé")
            else:
                print(f"   ✅ Rôle admin existe (ID: {admin_role.id})")
            
            # 2. Générer le hash du mot de passe
            password = 'admin123'
            password_hash = generate_password_hash(password)
            print(f"\n2. Hash du mot de passe généré: {password_hash[:50]}...")
            
            # 3. Vérifier/Créer l'utilisateur admin
            print("\n3. Vérification de l'utilisateur admin...")
            admin_user = User.query.filter_by(username='admin').first()
            
            if admin_user:
                print(f"   ⚠️ Utilisateur admin existe (ID: {admin_user.id})")
                print(f"      Email actuel: {admin_user.email}")
                print(f"      Role ID actuel: {admin_user.role_id}")
                print(f"      Actif: {admin_user.is_active}")
                
                # Vérifier le hash actuel
                if admin_user.password_hash:
                    is_valid = check_password_hash(admin_user.password_hash, password)
                    print(f"      Hash actuel valide: {'Oui' if is_valid else 'Non'}")
                    
                    if not is_valid:
                        print("   ⚠️ Le hash actuel est invalide. Mise à jour...")
                        admin_user.password_hash = password_hash
                else:
                    print("   ⚠️ Pas de hash. Ajout...")
                    admin_user.password_hash = password_hash
                
                # Mettre à jour les autres champs
                admin_user.email = 'admin@importprofit.pro'
                admin_user.full_name = 'Administrateur'
                admin_user.role_id = admin_role.id
                admin_user.is_active = True
                
                db.session.commit()
                print("   ✅ Utilisateur admin mis à jour")
            else:
                print("   ⚠️ Utilisateur admin non trouvé. Création...")
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
            
            # 4. Vérification finale
            print("\n4. Vérification finale...")
            final_user = User.query.filter_by(username='admin').first()
            
            if final_user:
                print(f"   ✅ Utilisateur trouvé:")
                print(f"      ID: {final_user.id}")
                print(f"      Username: {final_user.username}")
                print(f"      Email: {final_user.email}")
                print(f"      Full Name: {final_user.full_name}")
                print(f"      Role ID: {final_user.role_id}")
                print(f"      Actif: {final_user.is_active}")
                
                # Vérifier la relation avec le rôle
                if final_user.role:
                    print(f"      Role: {final_user.role.name} ({final_user.role.code})")
                else:
                    print("      ⚠️ Pas de rôle associé!")
                
                # Test final du hash
                if final_user.password_hash:
                    is_valid = check_password_hash(final_user.password_hash, password)
                    print(f"      Test mot de passe 'admin123': {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
                else:
                    print("      ❌ Pas de hash de mot de passe!")
            
            print("\n" + "=" * 60)
            print("✅ TERMINÉ!")
            print("=" * 60)
            print("Identifiants de connexion:")
            print("   Username: admin")
            print("   Password: admin123")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_admin()
    sys.exit(0 if success else 1)

