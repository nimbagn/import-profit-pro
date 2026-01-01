#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier les permissions du rôle magasinier
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Role, User
from auth import has_permission
from flask_login import login_user
from werkzeug.security import generate_password_hash

def test_warehouse_permissions():
    """Test des permissions du rôle magasinier"""
    
    with app.app_context():
        print("=" * 60)
        print("TEST DES PERMISSIONS DU RÔLE MAGASINIER")
        print("=" * 60)
        print()
        
        # 1. Vérifier que le rôle magasinier existe
        warehouse_role = Role.query.filter_by(code='warehouse').first()
        
        if not warehouse_role:
            print("❌ ERREUR: Le rôle magasinier (warehouse) n'existe pas dans la base de données")
            print("   Veuillez d'abord créer le rôle via l'interface d'administration")
            return False
        
        print(f"✅ Rôle magasinier trouvé: {warehouse_role.name} (ID: {warehouse_role.id})")
        print(f"   Permissions actuelles: {warehouse_role.permissions}")
        print()
        
        # 2. Vérifier les permissions requises
        required_permissions = {
            'stocks': ['read', 'create', 'update'],
            'movements': ['read', 'create'],
            'inventory': ['read', 'create', 'update'],
            'receptions': ['read', 'create', 'update'],
            'outgoings': ['read', 'create', 'update'],
            'returns': ['read', 'create', 'update'],
            'vehicles': ['read'],
            'regions': ['read'],
            'depots': ['read'],
            'families': ['read'],
            'stock_items': ['read'],
            'orders': ['read'],
            'stock_loading': ['read', 'verify', 'load']
        }
        
        print("📋 Vérification des permissions requises:")
        print("-" * 60)
        
        all_ok = True
        missing_permissions = {}
        
        for module, actions in required_permissions.items():
            if not warehouse_role.permissions:
                print(f"❌ {module}: Aucune permission définie")
                all_ok = False
                missing_permissions[module] = actions
                continue
            
            module_perms = warehouse_role.permissions.get(module, [])
            missing_actions = []
            
            for action in actions:
                if action not in module_perms:
                    missing_actions.append(action)
            
            if missing_actions:
                print(f"❌ {module}: Actions manquantes: {', '.join(missing_actions)}")
                print(f"   Permissions actuelles: {module_perms}")
                all_ok = False
                missing_permissions[module] = missing_actions
            else:
                print(f"✅ {module}: Toutes les permissions présentes ({', '.join(actions)})")
        
        print()
        
        if not all_ok:
            print("⚠️  PERMISSIONS MANQUANTES DÉTECTÉES")
            print("-" * 60)
            print("Les permissions suivantes doivent être ajoutées:")
            for module, actions in missing_permissions.items():
                print(f"  - {module}: {actions}")
            print()
            print("💡 SOLUTION:")
            print("   Exécutez le script SQL approprié pour votre base de données:")
            print("   - PostgreSQL: scripts/ajouter_permissions_magasinier_postgresql.sql")
            print("   - MySQL: scripts/ajouter_permissions_magasinier_mysql.sql")
            print()
            return False
        
        # 3. Créer un utilisateur de test magasinier (si nécessaire)
        print("👤 Vérification d'un utilisateur magasinier de test:")
        print("-" * 60)
        
        test_user = User.query.filter_by(username='test_warehouse').first()
        
        if not test_user:
            print("   Création d'un utilisateur de test...")
            test_user = User(
                username='test_warehouse',
                email='test_warehouse@example.com',
                password_hash=generate_password_hash('test123'),
                full_name='Test Magasinier',
                role_id=warehouse_role.id,
                is_active=True
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"   ✅ Utilisateur créé: {test_user.username} (ID: {test_user.id})")
        else:
            # Mettre à jour le rôle si nécessaire
            if test_user.role_id != warehouse_role.id:
                test_user.role_id = warehouse_role.id
                db.session.commit()
                print(f"   ✅ Rôle mis à jour pour: {test_user.username}")
            else:
                print(f"   ✅ Utilisateur existant: {test_user.username} (ID: {test_user.id})")
        
        print()
        
        # 4. Tester les permissions avec has_permission()
        print("🔍 Test des permissions avec has_permission():")
        print("-" * 60)
        
        # Recharger l'utilisateur avec le rôle
        db.session.refresh(test_user)
        test_user.role = warehouse_role
        
        test_permissions = [
            ('stocks.read', True),
            ('stocks.create', True),
            ('stocks.update', True),
            ('movements.read', True),
            ('movements.create', True),
            ('receptions.read', True),
            ('receptions.create', True),
            ('receptions.update', True),
            ('outgoings.read', True),
            ('outgoings.create', True),
            ('outgoings.update', True),
            ('returns.read', True),
            ('returns.create', True),
            ('returns.update', True),
            ('inventory.read', True),
            ('inventory.create', True),
            ('inventory.update', True),
            ('movements.update', False),  # Ne devrait pas avoir cette permission
            ('movements.delete', False),  # Ne devrait pas avoir cette permission
        ]
        
        permissions_ok = True
        for permission, expected in test_permissions:
            result = has_permission(test_user, permission)
            status = "✅" if result == expected else "❌"
            expected_str = "OUI" if expected else "NON"
            actual_str = "OUI" if result else "NON"
            
            if result != expected:
                permissions_ok = False
                print(f"{status} {permission}: Attendu {expected_str}, Obtenu {actual_str} ⚠️")
            else:
                print(f"{status} {permission}: {actual_str} (attendu: {expected_str})")
        
        print()
        
        if permissions_ok:
            print("=" * 60)
            print("✅ TOUS LES TESTS SONT PASSÉS!")
            print("=" * 60)
            print()
            print("📝 RÉSUMÉ:")
            print(f"   - Rôle magasinier: ✅")
            print(f"   - Permissions complètes: ✅")
            print(f"   - Utilisateur de test: {test_user.username}")
            print(f"   - Mot de passe de test: test123")
            print()
            print("🧪 POUR TESTER DANS L'INTERFACE:")
            print(f"   1. Connectez-vous avec: {test_user.username} / test123")
            print(f"   2. Accédez à: http://localhost:5002/stocks")
            print(f"   3. Vérifiez l'accès aux sections:")
            print(f"      - /stocks/receptions")
            print(f"      - /stocks/returns")
            print(f"      - /stocks/outgoings")
            print(f"      - /stocks/movements")
            print(f"      - /stocks/summary")
            print(f"      - /stocks/warehouse/dashboard")
            return True
        else:
            print("=" * 60)
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
            print("=" * 60)
            print()
            print("💡 Vérifiez que les permissions sont correctement définies dans la base de données")
            return False

if __name__ == '__main__':
    try:
        success = test_warehouse_permissions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

