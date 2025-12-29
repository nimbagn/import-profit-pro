#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de débogage pour diagnostiquer les problèmes de connexion
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role
from werkzeug.security import check_password_hash

with app.app_context():
    print("=" * 60)
    print("DIAGNOSTIC DE CONNEXION")
    print("=" * 60)
    
    # 1. Vérifier la connexion à la base
    try:
        db.engine.connect()
        print("✅ Connexion à la base de données: OK")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)
    
    # 2. Vérifier les tables
    print("\n📋 Vérification des tables...")
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"   Tables trouvées: {len(tables)}")
    
    if 'users' not in tables:
        print("❌ La table 'users' n'existe pas!")
        sys.exit(1)
    else:
        print("   ✅ Table 'users' existe")
    
    if 'roles' not in tables:
        print("❌ La table 'roles' n'existe pas!")
        sys.exit(1)
    else:
        print("   ✅ Table 'roles' existe")
    
    # 3. Vérifier les colonnes de users
    print("\n📋 Vérification des colonnes de 'users'...")
    columns = [col['name'] for col in inspector.get_columns('users')]
    required = ['username', 'password_hash', 'email', 'role_id', 'is_active']
    for col in required:
        if col in columns:
            print(f"   ✅ Colonne '{col}' existe")
        else:
            print(f"   ❌ Colonne '{col}' MANQUANTE!")
    
    # 4. Vérifier le rôle admin
    print("\n📋 Vérification du rôle admin...")
    admin_role = Role.query.filter_by(code='admin').first()
    if admin_role:
        print(f"   ✅ Rôle admin trouvé (ID: {admin_role.id}, Name: {admin_role.name})")
    else:
        print("   ❌ Rôle admin NON TROUVÉ!")
        print("   💡 Exécutez CREATE_ADMIN_FINAL.sql pour créer le rôle")
    
    # 5. Vérifier l'utilisateur admin
    print("\n📋 Vérification de l'utilisateur admin...")
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print(f"   ✅ Utilisateur admin trouvé (ID: {admin_user.id})")
        print(f"      Email: {admin_user.email}")
        print(f"      Role ID: {admin_user.role_id}")
        print(f"      Actif: {admin_user.is_active}")
        print(f"      Password hash présent: {'Oui' if admin_user.password_hash else 'Non'}")
        
        # Tester le mot de passe
        if admin_user.password_hash:
            test_password = 'admin123'
            is_valid = check_password_hash(admin_user.password_hash, test_password)
            print(f"      Test mot de passe 'admin123': {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
            
            if not is_valid:
                print("\n   ⚠️ Le hash du mot de passe ne correspond pas!")
                print("   💡 Exécutez CREATE_ADMIN_FINAL.sql pour corriger")
        else:
            print("   ❌ Pas de hash de mot de passe!")
    else:
        print("   ❌ Utilisateur admin NON TROUVÉ!")
        print("   💡 Exécutez CREATE_ADMIN_FINAL.sql pour créer l'utilisateur")
    
    # 6. Test de requête complète
    print("\n📋 Test de requête complète...")
    try:
        user = User.query.filter_by(username='admin').first()
        if user and user.role:
            print(f"   ✅ Requête complète OK")
            print(f"      User: {user.username}")
            print(f"      Role: {user.role.name} ({user.role.code})")
        elif user:
            print("   ⚠️ Utilisateur trouvé mais sans rôle")
        else:
            print("   ❌ Utilisateur non trouvé")
    except Exception as e:
        print(f"   ❌ Erreur lors de la requête: {e}")
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    
    if admin_role and admin_user and admin_user.password_hash:
        test_valid = check_password_hash(admin_user.password_hash, 'admin123')
        if test_valid:
            print("✅ Tout semble correct! Vous devriez pouvoir vous connecter.")
            print("   Username: admin")
            print("   Password: admin123")
        else:
            print("❌ Le hash du mot de passe est incorrect.")
            print("   💡 Exécutez: mysql -u root -p madargn < CREATE_ADMIN_FINAL.sql")
    else:
        print("❌ Des éléments manquent.")
        print("   💡 Exécutez: mysql -u root -p madargn < CREATE_ADMIN_FINAL.sql")
    
    print("=" * 60)

