#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier que tous les liens dans les templates pointent vers des routes existantes
"""

import os
import re
from pathlib import Path
from flask import Flask

# Créer une instance Flask minimale pour tester url_for
app = Flask(__name__)

# Enregistrer tous les blueprints
from auth import auth_bp
app.register_blueprint(auth_bp)

from referentiels import referentiels_bp
app.register_blueprint(referentiels_bp)

from stocks import stocks_bp
app.register_blueprint(stocks_bp)

from inventaires import inventaires_bp
app.register_blueprint(inventaires_bp)

from flotte import flotte_bp
app.register_blueprint(flotte_bp)

# Routes principales depuis app.py
@app.route('/')
def index():
    pass

@app.route('/simulations')
def simulations_list():
    pass

@app.route('/simulations/<int:id>')
def simulation_detail(id):
    pass

@app.route('/simulations/<int:id>/edit', methods=['GET', 'POST'])
def simulation_edit(id):
    pass

@app.route('/simulations/new')
def simulation_new():
    pass

@app.route('/articles')
def articles_list():
    pass

@app.route('/articles/new')
def article_new():
    pass

@app.route('/forecast')
def forecast_dashboard():
    pass

@app.route('/forecast/new')
def forecast_new():
    pass

@app.route('/forecast/list')
def forecast_list():
    pass

@app.route('/forecast/performance')
def forecast_performance():
    pass

@app.route('/forecast/import')
def forecast_import():
    pass

# Collecter toutes les routes
all_routes = []
with app.app_context():
    for rule in app.url_map.iter_rules():
        all_routes.append(rule.endpoint)

print(f"✅ {len(all_routes)} routes trouvées")
print("\nRoutes disponibles:")
for route in sorted(all_routes):
    print(f"  - {route}")

# Chercher tous les url_for dans les templates
templates_dir = Path('templates')
url_for_pattern = re.compile(r'url_for\([\'"]([^\'"]+)[\'"]')

errors = []
warnings = []

for template_file in templates_dir.rglob('*.html'):
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
        matches = url_for_pattern.findall(content)
        
        for endpoint in matches:
            # Nettoyer l'endpoint (enlever les paramètres)
            clean_endpoint = endpoint.split('(')[0].split(',')[0].strip()
            
            # Vérifier si la route existe
            if clean_endpoint not in all_routes:
                # Certains endpoints peuvent être dynamiques, vérifier avec app
                try:
                    with app.app_context():
                        app.url_for(clean_endpoint)
                except:
                    errors.append({
                        'file': str(template_file),
                        'endpoint': clean_endpoint,
                        'original': endpoint
                    })

print(f"\n{'='*70}")
print(f"VÉRIFICATION DES LIENS")
print(f"{'='*70}")

if errors:
    print(f"\n❌ {len(errors)} erreur(s) trouvée(s):\n")
    for error in errors:
        print(f"  📄 {error['file']}")
        print(f"     Route: {error['endpoint']}")
        print(f"     Original: {error['original']}")
        print()
else:
    print(f"\n✅ Tous les liens sont valides!")

print(f"\n{'='*70}")

