#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier les rôles RH dans la base de données
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Role

def verifier_roles_rh():
    """Vérifier les rôles RH dans la base de données"""
    with app.app_context():
        print("=" * 70)
        print("🔍 VÉRIFICATION DES RÔLES RH")
        print("=" * 70)
        print()
        
        # Liste des rôles RH attendus
        roles_rh_attendus = {
            'rh_manager': {
                'name': 'RH Manager',
                'description': 'Gestion complète du personnel, contrats, formations, évaluations'
            },
            'rh_assistant': {
                'name': 'RH Assistant',
                'description': 'Assistance RH : saisie données, suivi formations, gestion absences'
            },
            'rh_recruiter': {
                'name': 'RH Recruiter',
                'description': 'Recrutement et intégration du personnel'
            },
            'rh_analyst': {
                'name': 'RH Analyst',
                'description': 'Analyse et reporting RH, statistiques, tableaux de bord'
            },
            'rh': {
                'name': 'RH',
                'description': 'Gestion des utilisateurs plateforme, consultation des rapports'
            }
        }
        
        # Récupérer tous les rôles RH
        roles_rh_trouves = {}
        roles_existants = Role.query.filter(Role.code.like('rh%')).all()
        
        for role in roles_existants:
            roles_rh_trouves[role.code] = role
        
        print("📋 RÔLES RH TROUVÉS DANS LA BASE DE DONNÉES:")
        print("-" * 70)
        
        if not roles_rh_trouves:
            print("❌ Aucun rôle RH trouvé dans la base de données")
        else:
            for code, role in sorted(roles_rh_trouves.items()):
                print(f"✅ {role.name} ({role.code})")
                if role.description:
                    print(f"   Description: {role.description}")
                print()
        
        print()
        print("=" * 70)
        print("📊 COMPARAISON AVEC LES RÔLES ATTENDUS")
        print("=" * 70)
        print()
        
        roles_manquants = []
        roles_presents = []
        
        for code, info in roles_rh_attendus.items():
            if code in roles_rh_trouves:
                role = roles_rh_trouves[code]
                roles_presents.append(code)
                print(f"✅ {info['name']} ({code}) - PRÉSENT")
                if role.name != info['name']:
                    print(f"   ⚠️  Nom différent: '{role.name}' au lieu de '{info['name']}'")
            else:
                roles_manquants.append(code)
                print(f"❌ {info['name']} ({code}) - MANQUANT")
        
        print()
        print("=" * 70)
        print("📈 RÉSUMÉ")
        print("=" * 70)
        print(f"Rôles présents: {len(roles_presents)}/{len(roles_rh_attendus)}")
        print(f"Rôles manquants: {len(roles_manquants)}/{len(roles_rh_attendus)}")
        print()
        
        if roles_manquants:
            print("⚠️  RÔLES MANQUANTS:")
            for code in roles_manquants:
                info = roles_rh_attendus[code]
                print(f"   - {info['name']} ({code})")
            print()
            print("💡 Pour créer les rôles manquants:")
            print("   1. Allez sur: /auth/roles/new")
            print("   2. Créez chaque rôle avec les informations ci-dessus")
            print("   3. Ou exécutez un script de création des rôles")
        else:
            print("✅ Tous les rôles RH sont présents dans la base de données!")
        
        print()
        print("=" * 70)
        print("📋 TOUS LES RÔLES DANS LA BASE DE DONNÉES")
        print("=" * 70)
        print()
        
        tous_les_roles = Role.query.order_by(Role.code).all()
        if tous_les_roles:
            print(f"Total: {len(tous_les_roles)} rôle(s)")
            print()
            for role in tous_les_roles:
                est_rh = role.code.startswith('rh')
                prefixe = "🔹" if est_rh else "  "
                print(f"{prefixe} {role.name} ({role.code})")
        else:
            print("❌ Aucun rôle trouvé dans la base de données")
        
        print()
        print("=" * 70)
        
        return len(roles_manquants) == 0

if __name__ == '__main__':
    success = verifier_roles_rh()
    sys.exit(0 if success else 1)

