#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'initialisation pour Render
Crée les tables et l'utilisateur admin dans PostgreSQL
"""

from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash

def init_database():
    """Initialise la base de données avec les tables et l'utilisateur admin"""
    with app.app_context():
        try:
            print("🔄 Initialisation de la base de données...")
            print("=" * 60)
            
            # Créer toutes les tables
            print("📋 Création des tables...")
            db.create_all()
            print("✅ Tables créées")
            
            # Créer le rôle admin
            print("\n👤 Création du rôle admin...")
            admin_role = Role.query.filter_by(code='admin').first()
            if not admin_role:
                admin_role = Role(
                    name='Administrateur',
                    code='admin',
                    permissions={"all": ["*"]},
                    description='Accès complet à toutes les fonctionnalités'
                )
                db.session.add(admin_role)
                db.session.commit()
                print("✅ Rôle admin créé")
            else:
                print("ℹ️  Rôle admin existe déjà")
            
            # Créer l'utilisateur admin
            print("\n👤 Création de l'utilisateur admin...")
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
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
                print("✅ Utilisateur admin créé")
            else:
                print("ℹ️  Utilisateur admin existe déjà")
                # Réinitialiser le mot de passe au cas où
                admin_user.password_hash = generate_password_hash('admin123')
                admin_user.role_id = admin_role.id
                admin_user.is_active = True
                db.session.commit()
                print("✅ Mot de passe réinitialisé")
            
            print("\n" + "=" * 60)
            print("✅ Initialisation terminée avec succès!")
            print("=" * 60)
            print("\n📝 Identifiants de connexion:")
            print("   Username: admin")
            print("   Password: admin123")
            print("\n⚠️  IMPORTANT: Changez le mot de passe après la première connexion!")
            print("=" * 60)
            
            return True
        except Exception as e:
            print(f"\n❌ Erreur lors de l'initialisation: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = init_database()
    exit(0 if success else 1)

