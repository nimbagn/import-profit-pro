#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification des formulaires du module RH
Vérifie que tous les formulaires nécessaires existent et sont complets
"""

import os
import sys

print("=" * 70)
print("🔍 VÉRIFICATION DES FORMULAIRES - MODULE RH")
print("=" * 70)
print()

template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'rh')

# Liste des formulaires attendus
formulaires_attendus = {
    'personnel_form.html': {
        'description': 'Formulaire Personnel Plateforme (création/modification)',
        'routes': ['rh.personnel_new', 'rh.personnel_edit'],
        'champs_obligatoires': ['username', 'email', 'password', 'role_id']
    },
    'employee_form.html': {
        'description': 'Formulaire Employé Externe (création/modification)',
        'routes': ['rh.employee_new', 'rh.employee_edit'],
        'champs_obligatoires': ['employee_number', 'first_name', 'last_name']
    },
    'contract_form.html': {
        'description': 'Formulaire Contrat (création/modification)',
        'routes': ['rh.contract_new', 'rh.contract_edit'],
        'champs_obligatoires': ['contract_number', 'contract_type', 'start_date']
    },
    'training_form.html': {
        'description': 'Formulaire Formation (création/modification)',
        'routes': ['rh.training_new', 'rh.training_edit'],
        'champs_obligatoires': ['training_name', 'training_type', 'start_date']
    },
    'evaluation_form.html': {
        'description': 'Formulaire Évaluation (création/modification)',
        'routes': ['rh.evaluation_new', 'rh.evaluation_edit'],
        'champs_obligatoires': ['evaluation_type', 'evaluation_date']
    },
    'absence_form.html': {
        'description': 'Formulaire Absence (création/modification)',
        'routes': ['rh.absence_new', 'rh.absence_edit'],
        'champs_obligatoires': ['absence_type', 'start_date', 'end_date']
    }
}

# Vérifier l'existence des fichiers
print("1️⃣  Vérification de l'existence des fichiers...")
print("-" * 70)

formulaires_existants = []
formulaires_manquants = []

for fichier, info in formulaires_attendus.items():
    chemin = os.path.join(template_dir, fichier)
    if os.path.exists(chemin):
        taille = os.path.getsize(chemin)
        formulaires_existants.append(fichier)
        print(f"   ✅ {fichier:30} ({taille:,} octets)")
        print(f"      {info['description']}")
    else:
        formulaires_manquants.append(fichier)
        print(f"   ❌ {fichier:30} - MANQUANT")
        print(f"      {info['description']}")

print()

# Vérifier le contenu des formulaires
print("2️⃣  Vérification du contenu des formulaires...")
print("-" * 70)

for fichier, info in formulaires_attendus.items():
    chemin = os.path.join(template_dir, fichier)
    if os.path.exists(chemin):
        with open(chemin, 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Vérifier les éléments essentiels
        checks = {
            'extends base': 'base_modern_complete.html' in contenu,
            'form method': 'method="POST"' in contenu or "method='POST'" in contenu,
            'submit button': 'type="submit"' in contenu or "type='submit'" in contenu,
            'flash messages': 'get_flashed_messages' in contenu,
        }
        
        # Vérifier les champs obligatoires
        champs_trouves = []
        for champ in info['champs_obligatoires']:
            if f'name="{champ}"' in contenu or f"name='{champ}'" in contenu:
                champs_trouves.append(champ)
        
        print(f"\n   📄 {fichier}")
        print(f"      ✅ Extends base template: {checks['extends base']}")
        print(f"      ✅ Form method POST: {checks['form method']}")
        print(f"      ✅ Submit button: {checks['submit button']}")
        print(f"      ✅ Flash messages: {checks['flash messages']}")
        print(f"      ✅ Champs obligatoires: {len(champs_trouves)}/{len(info['champs_obligatoires'])}")
        
        if len(champs_trouves) < len(info['champs_obligatoires']):
            manquants = set(info['champs_obligatoires']) - set(champs_trouves)
            print(f"      ⚠️  Champs manquants: {', '.join(manquants)}")

print()

# Vérifier les routes associées
print("3️⃣  Vérification des routes associées...")
print("-" * 70)

try:
    from flask import Flask
    from app import app
    
    with app.app_context():
        routes_rh = {}
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('rh.'):
                routes_rh[rule.endpoint] = rule.rule
        
        for fichier, info in formulaires_attendus.items():
            print(f"\n   📄 {fichier}")
            for route_name in info['routes']:
                if route_name in routes_rh:
                    print(f"      ✅ Route {route_name:30} → {routes_rh[route_name]}")
                else:
                    print(f"      ⚠️  Route {route_name:30} - NON TROUVÉE")
                    
except Exception as e:
    print(f"   ⚠️  Impossible de vérifier les routes: {e}")

print()

# Vérifier les templates de liste et détails
print("4️⃣  Vérification des templates complémentaires...")
print("-" * 70)

templates_complementaires = {
    'personnel_list.html': 'Liste du personnel',
    'personnel_detail.html': 'Détails personnel',
    'employees_list.html': 'Liste des employés',
    'employee_detail.html': 'Détails employé',
    'contracts_list.html': 'Liste des contrats',
    'contract_detail.html': 'Détails contrat',
    'trainings_list.html': 'Liste des formations',
    'evaluations_list.html': 'Liste des évaluations',
    'absences_list.html': 'Liste des absences',
    'activites_list.html': 'Liste des activités',
    'statistiques.html': 'Statistiques RH',
}

for template, description in templates_complementaires.items():
    chemin = os.path.join(template_dir, template)
    if os.path.exists(chemin):
        print(f"   ✅ {template:30} - {description}")
    else:
        print(f"   ❌ {template:30} - MANQUANT ({description})")

print()

# Résumé
print("=" * 70)
print("📊 RÉSUMÉ")
print("=" * 70)
print(f"Formulaires attendus: {len(formulaires_attendus)}")
print(f"Formulaires existants: {len(formulaires_existants)}")
print(f"Formulaires manquants: {len(formulaires_manquants)}")
print(f"Templates complémentaires: {len(templates_complementaires)}")
print()

if len(formulaires_manquants) == 0:
    print("✅ Tous les formulaires sont présents !")
else:
    print(f"⚠️  {len(formulaires_manquants)} formulaire(s) manquant(s)")
    for fichier in formulaires_manquants:
        print(f"   - {fichier}")

print("=" * 70)

