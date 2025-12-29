#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de connexion pour vérifier l'utilisateur admin
"""

import requests
import sys

BASE_URL = "http://localhost:5002"

print("=" * 70)
print("TEST DE CONNEXION ADMIN")
print("=" * 70)

# Test 1: Vérifier que l'application répond
print("\n1. Vérification que l'application répond...")
try:
    response = requests.get(f"{BASE_URL}/auth/login", timeout=5)
    if response.status_code == 200:
        print("   ✅ Application accessible")
    else:
        print(f"   ⚠️ Code de statut: {response.status_code}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    print("   💡 Assurez-vous que Flask est démarré")
    sys.exit(1)

# Test 2: Tentative de connexion
print("\n2. Tentative de connexion avec admin/admin123...")
try:
    session = requests.Session()
    
    # D'abord, récupérer la page de login pour avoir le CSRF token si nécessaire
    login_page = session.get(f"{BASE_URL}/auth/login")
    
    # Tenter la connexion
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
    
    print(f"   Code de statut: {response.status_code}")
    
    if response.status_code == 302:
        # Redirection = succès
        location = response.headers.get('Location', '')
        print(f"   ✅ Redirection vers: {location}")
        if '/auth/login' not in location:
            print("   ✅ CONNEXION RÉUSSIE!")
        else:
            print("   ⚠️ Redirection vers login = échec de connexion")
    elif response.status_code == 200:
        # Pas de redirection = échec
        print("   ❌ Pas de redirection = connexion échouée")
        if 'incorrect' in response.text.lower() or 'error' in response.text.lower():
            print("   ❌ Message d'erreur détecté dans la page")
    else:
        print(f"   ⚠️ Code inattendu: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("💡 Vérifiez aussi les logs Flask dans le terminal")
print("   Vous devriez voir des messages commençant par '🔐 TENTATIVE DE CONNEXION'")
print("=" * 70)

