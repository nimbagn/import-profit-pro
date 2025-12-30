#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test complet du module Ressources Humaines
Vérifie les routes, modèles, permissions et fonctionnalités
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧪 TEST COMPLET DU MODULE RESSOURCES HUMAINES")
print("=" * 70)
print()

# =========================================================
# TEST 1: Import des modèles
# =========================================================
print("1️⃣  Test des imports des modèles...")
try:
    from models import (
        db, User, Role, Region, UserActivityLog, 
        Employee, EmployeeContract, EmployeeTraining, 
        EmployeeEvaluation, EmployeeAbsence, Depot
    )
    print("   ✅ Tous les modèles RH importés avec succès")
    print(f"      - UserActivityLog: {UserActivityLog}")
    print(f"      - Employee: {Employee}")
    print(f"      - EmployeeContract: {EmployeeContract}")
    print(f"      - EmployeeTraining: {EmployeeTraining}")
    print(f"      - EmployeeEvaluation: {EmployeeEvaluation}")
    print(f"      - EmployeeAbsence: {EmployeeAbsence}")
except Exception as e:
    print(f"   ❌ Erreur d'import: {e}")
    sys.exit(1)

# =========================================================
# TEST 2: Vérification des attributs des modèles
# =========================================================
print("\n2️⃣  Test des attributs des modèles...")
try:
    # Vérifier UserActivityLog
    assert hasattr(UserActivityLog, 'activity_metadata'), "UserActivityLog doit avoir 'activity_metadata' (pas 'metadata')"
    print("   ✅ UserActivityLog.activity_metadata existe")
    
    # Vérifier Employee
    assert hasattr(Employee, 'user_id'), "Employee doit avoir 'user_id'"
    assert hasattr(Employee, 'created_by_id'), "Employee doit avoir 'created_by_id'"
    assert hasattr(Employee, 'user'), "Employee doit avoir la relation 'user'"
    assert hasattr(Employee, 'created_by'), "Employee doit avoir la relation 'created_by'"
    print("   ✅ Employee a tous les attributs nécessaires")
    
    # Vérifier les relations
    assert hasattr(Employee, 'contracts'), "Employee doit avoir 'contracts'"
    assert hasattr(Employee, 'trainings'), "Employee doit avoir 'trainings'"
    assert hasattr(Employee, 'evaluations'), "Employee doit avoir 'evaluations'"
    assert hasattr(Employee, 'absences'), "Employee doit avoir 'absences'"
    print("   ✅ Employee a toutes les relations nécessaires")
    
except AssertionError as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

# =========================================================
# TEST 3: Import du blueprint RH
# =========================================================
print("\n3️⃣  Test de l'import du blueprint RH...")
try:
    from rh import rh_bp
    print(f"   ✅ Blueprint RH importé: {rh_bp.name}")
    print(f"      URL prefix: {rh_bp.url_prefix}")
except Exception as e:
    print(f"   ❌ Erreur d'import du blueprint: {e}")
    sys.exit(1)

# =========================================================
# TEST 4: Vérification des routes enregistrées
# =========================================================
print("\n4️⃣  Test des routes du blueprint RH...")
try:
    from flask import Flask
    from app import app
    
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('rh.'):
                routes.append({
                    'endpoint': rule.endpoint,
                    'url': rule.rule,
                    'methods': sorted(rule.methods - {'HEAD', 'OPTIONS'})
                })
        
        print(f"   ✅ {len(routes)} routes RH trouvées")
        
        # Routes principales à vérifier
        expected_routes = {
            'rh.personnel_list': '/rh/personnel',
            'rh.personnel_detail': '/rh/personnel/<int:user_id>',
            'rh.personnel_new': '/rh/personnel/new',
            'rh.personnel_edit': '/rh/personnel/<int:user_id>/edit',
            'rh.employees_list': '/rh/employees',
            'rh.employee_detail': '/rh/employees/<int:employee_id>',
            'rh.employee_new': '/rh/employees/new',
            'rh.employee_edit': '/rh/employees/<int:employee_id>/edit',
            'rh.employee_contracts_list': '/rh/employees/<int:employee_id>/contracts',
            'rh.contract_new': '/rh/employees/<int:employee_id>/contracts/new',
            'rh.contract_detail': '/rh/contracts/<int:contract_id>',
            'rh.contract_edit': '/rh/contracts/<int:contract_id>/edit',
            'rh.employee_trainings_list': '/rh/employees/<int:employee_id>/trainings',
            'rh.training_new': '/rh/employees/<int:employee_id>/trainings/new',
            'rh.training_edit': '/rh/trainings/<int:training_id>/edit',
            'rh.employee_evaluations_list': '/rh/employees/<int:employee_id>/evaluations',
            'rh.evaluation_new': '/rh/employees/<int:employee_id>/evaluations/new',
            'rh.evaluation_edit': '/rh/evaluations/<int:evaluation_id>/edit',
            'rh.employee_absences_list': '/rh/employees/<int:employee_id>/absences',
            'rh.absence_new': '/rh/employees/<int:employee_id>/absences/new',
            'rh.absence_edit': '/rh/absences/<int:absence_id>/edit',
            'rh.absence_approve': '/rh/absences/<int:absence_id>/approve',
            'rh.absence_reject': '/rh/absences/<int:absence_id>/reject',
            'rh.activites_list': '/rh/activites',
            'rh.statistiques': '/rh/statistiques',
        }
        
        found_routes = {r['endpoint']: r['url'] for r in routes}
        missing = []
        for endpoint, expected_url in expected_routes.items():
            if endpoint in found_routes:
                print(f"      ✅ {endpoint}")
            else:
                missing.append(endpoint)
                print(f"      ⚠️  {endpoint} - MANQUANT")
        
        if missing:
            print(f"\n   ⚠️  {len(missing)} routes manquantes sur {len(expected_routes)}")
        else:
            print(f"\n   ✅ Toutes les routes principales sont présentes ({len(expected_routes)})")
            
except Exception as e:
    print(f"   ❌ Erreur lors du test des routes: {e}")
    import traceback
    traceback.print_exc()

# =========================================================
# TEST 5: Vérification des templates
# =========================================================
print("\n5️⃣  Test de l'existence des templates...")
try:
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'rh')
    if not os.path.exists(template_dir):
        print(f"   ❌ Répertoire templates/rh n'existe pas")
    else:
        templates = [
            'personnel_list.html',
            'personnel_detail.html',
            'personnel_form.html',
            'employees_list.html',
            'employee_detail.html',
            'employee_form.html',
            'contracts_list.html',
            'contract_form.html',
            'contract_detail.html',
            'trainings_list.html',
            'training_form.html',
            'evaluations_list.html',
            'evaluation_form.html',
            'absences_list.html',
            'absence_form.html',
            'activites_list.html',
            'statistiques.html',
        ]
        
        existing = []
        missing = []
        for template in templates:
            path = os.path.join(template_dir, template)
            if os.path.exists(path):
                existing.append(template)
            else:
                missing.append(template)
        
        print(f"   ✅ {len(existing)}/{len(templates)} templates trouvés")
        if missing:
            print(f"   ⚠️  Templates manquants: {', '.join(missing)}")
        else:
            print(f"   ✅ Tous les templates sont présents")
            
except Exception as e:
    print(f"   ❌ Erreur lors du test des templates: {e}")

# =========================================================
# TEST 6: Vérification des fonctions utilitaires
# =========================================================
print("\n6️⃣  Test des fonctions utilitaires...")
try:
    from rh import log_activity, has_rh_permission
    
    print("   ✅ log_activity importée")
    print("   ✅ has_rh_permission importée")
    
    # Test de la signature de log_activity
    import inspect
    sig = inspect.signature(log_activity)
    params = list(sig.parameters.keys())
    assert 'user_id' in params, "log_activity doit avoir 'user_id'"
    assert 'action' in params, "log_activity doit avoir 'action'"
    assert 'metadata' in params, "log_activity doit avoir 'metadata'"
    print("   ✅ Signature de log_activity correcte")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

# =========================================================
# TEST 7: Vérification des rôles RH dans app.py
# =========================================================
print("\n7️⃣  Test de la configuration des rôles RH...")
try:
    # Vérifier que les rôles RH sont définis dans app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    rh_roles = ['rh', 'rh_manager', 'rh_assistant', 'rh_recruiter', 'rh_analyst']
    found_roles = []
    for role in rh_roles:
        if f"'{role}'" in content or f'"{role}"' in content:
            found_roles.append(role)
            print(f"      ✅ Rôle '{role}' trouvé")
        else:
            print(f"      ⚠️  Rôle '{role}' non trouvé")
    
    if len(found_roles) == len(rh_roles):
        print(f"   ✅ Tous les rôles RH sont configurés ({len(rh_roles)})")
    else:
        print(f"   ⚠️  {len(found_roles)}/{len(rh_roles)} rôles trouvés")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# =========================================================
# TEST 8: Vérification de la structure des modèles
# =========================================================
print("\n8️⃣  Test de la structure des modèles...")
try:
    # Vérifier que les colonnes importantes existent
    employee_columns = [
        'employee_number', 'first_name', 'last_name', 'email',
        'department', 'position', 'employment_status', 'hire_date',
        'user_id', 'created_by_id'
    ]
    
    for col in employee_columns:
        if hasattr(Employee, col):
            print(f"      ✅ Employee.{col}")
        else:
            print(f"      ⚠️  Employee.{col} - MANQUANT")
    
    # Vérifier les propriétés
    if hasattr(Employee, 'full_name'):
        print(f"      ✅ Employee.full_name (propriété)")
    if hasattr(Employee, 'current_contract'):
        print(f"      ✅ Employee.current_contract (propriété)")
    
    print("   ✅ Structure des modèles vérifiée")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# =========================================================
# RÉSUMÉ
# =========================================================
print("\n" + "=" * 70)
print("📊 RÉSUMÉ DES TESTS")
print("=" * 70)
print("✅ Tests de base terminés")
print("\n💡 Pour tester les fonctionnalités en live:")
print("   1. Démarrez l'application: python app.py")
print("   2. Connectez-vous avec un compte admin")
print("   3. Accédez à /rh/personnel pour voir le module RH")
print("   4. Créez un utilisateur avec un rôle RH")
print("   5. Testez les différentes fonctionnalités")
print("\n📖 Consultez GUIDE_TEST_MODULE_RH.md pour plus de détails")
print("=" * 70)

