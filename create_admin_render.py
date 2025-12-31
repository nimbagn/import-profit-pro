#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer un utilisateur administrateur sur Render
Utilisable aussi en local
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC

def create_admin():
    """Créer un utilisateur administrateur"""
    with app.app_context():
        try:
            print("=" * 60)
            print("🔧 CRÉATION / VÉRIFICATION DE L'UTILISATEUR ADMIN")
            print("=" * 60)
            print()
            
            # Vérifier si l'admin existe déjà
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print("⚠️  L'utilisateur 'admin' existe déjà")
                print(f"   ID: {admin_user.id}")
                print(f"   Email: {admin_user.email}")
                print(f"   Actif: {admin_user.is_active}")
                print()
                
                # Vérifier le mot de passe
                if not admin_user.password_hash:
                    print("   ❌ Pas de mot de passe - Réinitialisation...")
                    admin_user.password_hash = generate_password_hash('admin123')
                    db.session.commit()
                    print("   ✅ Mot de passe réinitialisé: admin123")
                else:
                    print("   ✅ Mot de passe présent")
                    # Proposer de réinitialiser
                    print()
                    print("   💡 Pour réinitialiser le mot de passe, exécutez:")
                    print("      python3 create_admin_render.py --reset-password")
                
                # Vérifier le rôle
                if admin_user.role:
                    print(f"   ✅ Rôle: {admin_user.role.name} ({admin_user.role.code})")
                else:
                    print("   ⚠️  Pas de rôle associé")
                    admin_role = Role.query.filter_by(code='admin').first()
                    if admin_role:
                        admin_user.role_id = admin_role.id
                        db.session.commit()
                        print(f"   ✅ Rôle admin assigné")
                
                # Activer si désactivé
                if not admin_user.is_active:
                    admin_user.is_active = True
                    db.session.commit()
                    print("   ✅ Compte activé")
                
                print()
                print("=" * 60)
                print("✅ UTILISATEUR ADMIN PRÊT")
                print("=" * 60)
                print(f"Username: admin")
                print(f"Password: {'admin123' if not admin_user.password_hash or 'admin123' in str(admin_user.password_hash) else '(défini précédemment)'}")
                print(f"Email: {admin_user.email}")
                print("=" * 60)
                
                return admin_user
            
            # Récupérer le rôle admin
            admin_role = Role.query.filter_by(code='admin').first()
            if not admin_role:
                print("❌ Le rôle 'admin' n'existe pas")
                print()
                print("📋 Rôles existants:")
                roles = Role.query.all()
                if roles:
                    for role in roles:
                        print(f"   - {role.name} ({role.code})")
                else:
                    print("   (Aucun rôle trouvé)")
                print()
                print("💡 Créez d'abord les rôles dans la base de données")
                return None
            
            # Créer l'utilisateur admin
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrateur',
                role_id=admin_role.id,
                is_active=True,
                created_at=datetime.now(UTC)
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("=" * 60)
            print("✅ UTILISATEUR ADMIN CRÉÉ AVEC SUCCÈS")
            print("=" * 60)
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"Email: admin@example.com")
            print(f"Rôle: {admin_role.name}")
            print()
            print("⚠️  IMPORTANT: Changez le mot de passe après la première connexion!")
            print("=" * 60)
            
            return admin_user
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'admin: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None

def reset_password():
    """Réinitialiser le mot de passe de l'admin"""
    with app.app_context():
        try:
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ Utilisateur 'admin' non trouvé")
                return False
            
            admin_user.password_hash = generate_password_hash('admin123')
            db.session.commit()
            
            print("=" * 60)
            print("✅ MOT DE PASSE RÉINITIALISÉ")
            print("=" * 60)
            print(f"Username: admin")
            print(f"Password: admin123")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset-password':
        reset_password()
    else:
        create_admin()

