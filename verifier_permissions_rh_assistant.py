#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier et corriger les permissions du rôle rh_assistant
"""

import sys
import os
import json

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Role, User

def verifier_et_corriger_permissions():
    """Vérifie et corrige les permissions du rôle rh_assistant"""
    
    with app.app_context():
        print("=" * 70)
        print("🔍 VÉRIFICATION DES PERMISSIONS RH_ASSISTANT")
        print("=" * 70)
        
        # Récupérer le rôle rh_assistant
        role = Role.query.filter_by(code='rh_assistant').first()
        
        if not role:
            print("❌ ERREUR: Le rôle 'rh_assistant' n'existe pas dans la base de données!")
            print("   Exécutez d'abord: python3 create_roles_rh.py")
            return False
        
        print(f"\n✅ Rôle trouvé: {role.name} (code: {role.code})")
        print(f"   Description: {role.description}")
        
        # Permissions attendues
        permissions_attendues = {
            'users': ['read', 'create', 'update'],
            'employees': ['read', 'create', 'update'],
            'contracts': ['read', 'create', 'update'],
            'trainings': ['read', 'create', 'update'],
            'evaluations': ['read', 'create'],
            'absences': ['read', 'create', 'update'],
            'reports': ['read']
        }
        
        print(f"\n📋 Permissions attendues:")
        print(json.dumps(permissions_attendues, indent=2, ensure_ascii=False))
        
        # Vérifier les permissions actuelles
        permissions_actuelles = role.permissions
        if isinstance(permissions_actuelles, str):
            try:
                permissions_actuelles = json.loads(permissions_actuelles)
            except:
                permissions_actuelles = {}
        
        print(f"\n📋 Permissions actuelles dans la base:")
        print(json.dumps(permissions_actuelles, indent=2, ensure_ascii=False))
        
        # Vérifier si employees.create existe
        employees_perms = permissions_actuelles.get('employees', [])
        if isinstance(employees_perms, str):
            employees_perms = [employees_perms] if employees_perms != '*' else ['*']
        
        print(f"\n🔍 Vérification spécifique:")
        print(f"   - employees permissions: {employees_perms}")
        print(f"   - 'create' dans employees: {'create' in employees_perms}")
        
        if 'create' not in employees_perms and '*' not in employees_perms:
            print("\n⚠️  PROBLÈME DÉTECTÉ: La permission 'employees.create' est manquante!")
            print("   Correction en cours...")
            
            # Corriger les permissions
            role.permissions = permissions_attendues
            db.session.commit()
            
            print("✅ Permissions corrigées avec succès!")
            
            # Vérifier à nouveau
            role = Role.query.filter_by(code='rh_assistant').first()
            permissions_actuelles = role.permissions
            if isinstance(permissions_actuelles, str):
                try:
                    permissions_actuelles = json.loads(permissions_actuelles)
                except:
                    permissions_actuelles = {}
            
            employees_perms = permissions_actuelles.get('employees', [])
            if isinstance(employees_perms, str):
                employees_perms = [employees_perms] if employees_perms != '*' else ['*']
            
            print(f"\n✅ Vérification après correction:")
            print(f"   - employees permissions: {employees_perms}")
            print(f"   - 'create' dans employees: {'create' in employees_perms}")
        else:
            print("\n✅ Les permissions sont correctes!")
        
        # Lister les utilisateurs avec ce rôle
        users = User.query.filter_by(role_id=role.id).all()
        print(f"\n👥 Utilisateurs avec le rôle 'rh_assistant': {len(users)}")
        for user in users:
            print(f"   - {user.username} ({user.full_name or 'N/A'}) - Actif: {user.is_active}")
        
        print("\n" + "=" * 70)
        print("✅ VÉRIFICATION TERMINÉE")
        print("=" * 70)
        
        return True

if __name__ == '__main__':
    try:
        verifier_et_corriger_permissions()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

