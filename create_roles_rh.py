#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer les rôles RH dans la base de données
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Role
from datetime import datetime, UTC

def create_roles_rh():
    """Créer les rôles RH dans la base de données"""
    with app.app_context():
        print("=" * 70)
        print("🔧 CRÉATION DES RÔLES RH")
        print("=" * 70)
        print()
        
        # Définition des rôles RH
        roles_rh = [
            {
                'name': 'RH Manager',
                'code': 'rh_manager',
                'description': 'Gestion complète du personnel, contrats, formations, évaluations',
                'permissions': {
                    'users': ['read', 'create', 'update', 'delete'],
                    'employees': ['read', 'create', 'update', 'delete'],
                    'contracts': ['read', 'create', 'update', 'delete'],
                    'trainings': ['read', 'create', 'update', 'delete'],
                    'evaluations': ['read', 'create', 'update', 'delete'],
                    'absences': ['read', 'create', 'update', 'delete'],
                    'reports': ['read', 'export'],
                    'analytics': ['read', 'export']
                }
            },
            {
                'name': 'RH Assistant',
                'code': 'rh_assistant',
                'description': 'Assistance RH : saisie données, suivi formations, gestion absences',
                'permissions': {
                    'users': ['read', 'create', 'update'],
                    'employees': ['read', 'create', 'update'],
                    'contracts': ['read', 'create', 'update'],
                    'trainings': ['read', 'create', 'update'],
                    'evaluations': ['read', 'create'],
                    'absences': ['read', 'create', 'update', 'delete'],
                    'reports': ['read']
                }
            },
            {
                'name': 'RH Recruiter',
                'code': 'rh_recruiter',
                'description': 'Recrutement et intégration du personnel',
                'permissions': {
                    'users': ['read', 'create'],
                    'employees': ['read', 'create', 'update'],
                    'contracts': ['read', 'create'],
                    'trainings': ['read', 'create'],
                    'reports': ['read']
                }
            },
            {
                'name': 'RH Analyst',
                'code': 'rh_analyst',
                'description': 'Analyse et reporting RH, statistiques, tableaux de bord',
                'permissions': {
                    'users': ['read'],
                    'employees': ['read'],
                    'contracts': ['read'],
                    'trainings': ['read'],
                    'evaluations': ['read'],
                    'absences': ['read'],
                    'reports': ['read', 'export'],
                    'analytics': ['read', 'export']
                }
            },
            {
                'name': 'RH',
                'code': 'rh',
                'description': 'Gestion des utilisateurs plateforme, consultation des rapports',
                'permissions': {
                    'users': ['read', 'create', 'update'],
                    'reports': ['read']
                }
            }
        ]
        
        roles_crees = []
        roles_existants = []
        erreurs = []
        
        for role_data in roles_rh:
            # Vérifier si le rôle existe déjà
            role_existant = Role.query.filter_by(code=role_data['code']).first()
            
            if role_existant:
                roles_existants.append(role_data['code'])
                print(f"⚠️  {role_data['name']} ({role_data['code']}) existe déjà")
                # Mettre à jour si nécessaire
                if role_existant.name != role_data['name'] or role_existant.description != role_data['description']:
                    role_existant.name = role_data['name']
                    role_existant.description = role_data['description']
                    if role_data.get('permissions'):
                        import json
                        role_existant.permissions = json.dumps(role_data['permissions'])
                    role_existant.updated_at = datetime.now(UTC)
                    print(f"   ✅ Informations mises à jour")
            else:
                # Créer le nouveau rôle
                try:
                    import json
                    new_role = Role(
                        name=role_data['name'],
                        code=role_data['code'],
                        description=role_data['description'],
                        permissions=json.dumps(role_data['permissions']) if role_data.get('permissions') else None,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC)
                    )
                    
                    db.session.add(new_role)
                    db.session.flush()
                    roles_crees.append(role_data['code'])
                    print(f"✅ {role_data['name']} ({role_data['code']}) créé")
                except Exception as e:
                    erreurs.append((role_data['code'], str(e)))
                    print(f"❌ Erreur lors de la création de {role_data['name']} ({role_data['code']}): {e}")
                    db.session.rollback()
        
        # Commit des changements
        try:
            db.session.commit()
            print()
            print("=" * 70)
            print("📊 RÉSUMÉ")
            print("=" * 70)
            print(f"✅ Rôles créés: {len(roles_crees)}")
            print(f"⚠️  Rôles existants: {len(roles_existants)}")
            if erreurs:
                print(f"❌ Erreurs: {len(erreurs)}")
            print()
            
            if roles_crees:
                print("Rôles créés:")
                for code in roles_crees:
                    role_data = next(r for r in roles_rh if r['code'] == code)
                    print(f"   - {role_data['name']} ({code})")
                print()
            
            if erreurs:
                print("Erreurs:")
                for code, error in erreurs:
                    print(f"   - {code}: {error}")
                print()
            
            # Vérification finale
            print("=" * 70)
            print("✅ VÉRIFICATION FINALE")
            print("=" * 70)
            print()
            
            tous_les_roles_rh = Role.query.filter(Role.code.like('rh%')).all()
            print(f"📋 Rôles RH dans la base de données: {len(tous_les_roles_rh)}/5")
            print()
            
            for role in sorted(tous_les_roles_rh, key=lambda x: x.code):
                print(f"✅ {role.name} ({role.code})")
            
            if len(tous_les_roles_rh) == 5:
                print()
                print("🎉 Tous les rôles RH ont été créés avec succès!")
                return True
            else:
                print()
                print(f"⚠️  {5 - len(tous_les_roles_rh)} rôle(s) RH manquant(s)")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du commit: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_roles_rh()
    sys.exit(0 if success else 1)

