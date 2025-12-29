#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer l'utilisateur admin dans la base de données
"""

from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Créer l'utilisateur admin si il n'existe pas"""
    with app.app_context():
        try:
            # Vérifier si le rôle admin existe
            admin_role = Role.query.filter_by(code='admin').first()
            if not admin_role:
                print("⚠️ Le rôle admin n'existe pas. Création du rôle...")
                admin_role = Role(
                    name='Administrateur',
                    code='admin',
                    description='Accès complet à toutes les fonctionnalités',
                    permissions={'all': ['*']}
                )
                db.session.add(admin_role)
                db.session.commit()
                print("✅ Rôle admin créé")
            
            # Vérifier si l'utilisateur admin existe
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("⚠️ L'utilisateur admin n'existe pas. Création...")
                admin_user = User(
                    username='admin',
                    email='admin@importprofit.pro',
                    password_hash=generate_password_hash('admin123'),
                    full_name='Administrateur',
                    role_id=admin_role.id,
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Utilisateur admin créé avec succès")
                print("   Username: admin")
                print("   Password: admin123")
            else:
                print("✅ L'utilisateur admin existe déjà")
                # Mettre à jour le mot de passe au cas où
                admin_user.password_hash = generate_password_hash('admin123')
                admin_user.role_id = admin_role.id
                admin_user.is_active = True
                db.session.commit()
                print("✅ Mot de passe réinitialisé à 'admin123'")
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'utilisateur admin: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🔄 Création de l'utilisateur admin...")
    print("=" * 60)
    success = create_admin_user()
    if success:
        print("=" * 60)
        print("✅ Script terminé avec succès")
    else:
        print("=" * 60)
        print("❌ Erreur lors de l'exécution")
        exit(1)

