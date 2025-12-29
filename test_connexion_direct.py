#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test direct de la connexion avec les mêmes paramètres que Flask
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Simuler une tentative de connexion
print("=" * 70)
print("TEST DE CONNEXION - SIMULATION")
print("=" * 70)

try:
    from app import app
    from models import db, User, Role
    from werkzeug.security import check_password_hash
    
    with app.app_context():
        print("\n1. Test de connexion à la base...")
        try:
            db.engine.connect()
            print("   ✅ Connexion OK")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            sys.exit(1)
        
        print("\n2. Recherche de l'utilisateur 'admin'...")
        user = User.query.filter_by(username='admin').first()
        
        if not user:
            print("   ❌ Utilisateur 'admin' NON TROUVÉ")
            print("\n   📋 Liste de tous les utilisateurs:")
            all_users = User.query.all()
            for u in all_users:
                attrs = ['id', 'username', 'email', 'role_id', 'is_active']
                info = {attr: getattr(u, attr, 'N/A') for attr in attrs}
                print(f"      {info}")
            sys.exit(1)
        
        print(f"   ✅ Utilisateur trouvé (ID: {user.id})")
        print(f"      Username: {user.username}")
        print(f"      Email: {user.email}")
        print(f"      Role ID: {user.role_id}")
        print(f"      Actif: {user.is_active}")
        print(f"      Hash présent: {'Oui' if user.password_hash else 'Non'}")
        
        if user.password_hash:
            print(f"      Hash: {user.password_hash[:60]}...")
        
        print("\n3. Test du mot de passe 'admin123'...")
        if not user.password_hash:
            print("   ❌ Pas de hash de mot de passe!")
            sys.exit(1)
        
        is_valid = check_password_hash(user.password_hash, 'admin123')
        if is_valid:
            print("   ✅ Mot de passe VALIDE")
        else:
            print("   ❌ Mot de passe INVALIDE")
            print(f"      Hash stocké: {user.password_hash[:60]}...")
            sys.exit(1)
        
        print("\n4. Vérification du rôle...")
        if user.role:
            print(f"   ✅ Rôle: {user.role.name} ({user.role.code})")
        else:
            print("   ⚠️ Pas de rôle chargé")
            if user.role_id:
                role = Role.query.get(user.role_id)
                if role:
                    print(f"   ✅ Rôle existe: {role.name} ({role.code})")
                else:
                    print(f"   ❌ Rôle avec ID {user.role_id} n'existe pas")
        
        print("\n" + "=" * 70)
        print("✅ TOUT EST CORRECT!")
        print("=" * 70)
        print("L'utilisateur admin existe et le mot de passe est valide.")
        print("Si la connexion ne fonctionne toujours pas, vérifiez:")
        print("  1. Les logs Flask dans le terminal")
        print("  2. Que Flask est bien redémarré après création de l'utilisateur")
        print("  3. Que vous utilisez bien 'admin' et 'admin123'")
        
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

