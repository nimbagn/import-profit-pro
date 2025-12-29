#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer un utilisateur commercial de test
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from models import db, User, Role
from app import app

def create_commercial_test():
    """Créer un utilisateur commercial de test"""
    with app.app_context():
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username='commercial_test').first()
        if existing_user:
            print("⚠️  L'utilisateur 'commercial_test' existe déjà.")
            print(f"   ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            print(f"   Rôle: {existing_user.role.code if existing_user.role else 'Aucun'}")
            response = input("\nVoulez-vous le mettre à jour ? (o/n): ")
            if response.lower() != 'o':
                print("❌ Opération annulée.")
                return False
            
            # Mettre à jour l'utilisateur existant
            commercial_role = Role.query.filter_by(code='commercial').first()
            if not commercial_role:
                print("❌ Erreur: Le rôle 'commercial' n'existe pas dans la base de données.")
                return False
            
            existing_user.email = 'commercial_test@importprofit.pro'
            existing_user.password_hash = generate_password_hash('commercial123')
            existing_user.role_id = commercial_role.id
            existing_user.is_active = True
            existing_user.full_name = 'Commercial Test'
            
            db.session.commit()
            print("✅ Utilisateur 'commercial_test' mis à jour avec succès!")
            return True
        
        # Récupérer le rôle commercial
        commercial_role = Role.query.filter_by(code='commercial').first()
        if not commercial_role:
            print("❌ Erreur: Le rôle 'commercial' n'existe pas dans la base de données.")
            print("   Vérifiez que les rôles sont initialisés correctement.")
            return False
        
        # Créer le nouvel utilisateur
        password = 'commercial123'
        password_hash = generate_password_hash(password)
        
        new_user = User(
            username='commercial_test',
            email='commercial_test@importprofit.pro',
            password_hash=password_hash,
            full_name='Commercial Test',
            role_id=commercial_role.id,
            is_active=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print("=" * 60)
        print("✅ UTILISATEUR COMMERCIAL DE TEST CRÉÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"\n📋 Identifiants de connexion:")
        print(f"   Username: commercial_test")
        print(f"   Password: commercial123")
        print(f"   Email: commercial_test@importprofit.pro")
        print(f"   Rôle: {commercial_role.name} (code: {commercial_role.code})")
        print(f"\n🔗 URL de connexion: http://localhost:5002/auth/login")
        print(f"🔗 URL des commandes: http://localhost:5002/orders")
        print("=" * 60)
        
        return True

if __name__ == '__main__':
    try:
        create_commercial_test()
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

