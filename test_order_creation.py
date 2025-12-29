#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour créer une commande commerciale
"""

import sys
import os
import requests
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5002"
USERNAME = "commercial_test"
PASSWORD = "commercial123"

def test_order_creation():
    """Tester la création d'une commande commerciale"""
    session = requests.Session()
    
    print("=" * 60)
    print("TEST DE CRÉATION DE COMMANDE COMMERCIALE")
    print("=" * 60)
    
    # 1. Connexion
    print("\n1. Connexion avec le compte commercial...")
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrf_token': None  # Sera rempli après récupération de la page
    }
    
    # Récupérer la page de connexion pour obtenir le CSRF token
    login_page = session.get(login_url)
    if login_page.status_code != 200:
        print(f"❌ Erreur lors de l'accès à la page de connexion: {login_page.status_code}")
        return False
    
    # Extraire le CSRF token (simplifié - dans un vrai test, utiliser BeautifulSoup)
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
    if csrf_match:
        login_data['csrf_token'] = csrf_match.group(1)
    
    # Se connecter
    login_response = session.post(login_url, data=login_data, allow_redirects=False)
    if login_response.status_code in [302, 200]:
        print("✅ Connexion réussie")
    else:
        print(f"❌ Erreur de connexion: {login_response.status_code}")
        print(f"   Réponse: {login_response.text[:200]}")
        return False
    
    # 2. Accéder à la page de création de commande
    print("\n2. Accès à la page de création de commande...")
    new_order_url = f"{BASE_URL}/orders/new"
    new_order_page = session.get(new_order_url)
    
    if new_order_page.status_code == 302:
        print(f"⚠️  Redirection détectée (code {new_order_page.status_code})")
        print(f"   Location: {new_order_page.headers.get('Location', 'N/A')}")
        print("   Cela peut indiquer un problème de permissions ou de session")
        return False
    elif new_order_page.status_code == 200:
        print("✅ Page de création de commande accessible")
        
        # Vérifier le contenu de la page
        if "Nouvelle Commande" in new_order_page.text or "Créer une commande" in new_order_page.text:
            print("✅ Formulaire de création présent dans la page")
        else:
            print("⚠️  Formulaire de création non trouvé dans la page")
            print(f"   Contenu (premiers 500 caractères): {new_order_page.text[:500]}")
    else:
        print(f"❌ Erreur lors de l'accès à la page: {new_order_page.status_code}")
        return False
    
    # 3. Vérifier les éléments du formulaire
    print("\n3. Vérification des éléments du formulaire...")
    checks = {
        "clients-table": "Tableau des clients" in new_order_page.text or "clients-table" in new_order_page.text,
        "payment_type": "payment_type" in new_order_page.text or "Type de paiement" in new_order_page.text,
        "payment_due_date": "payment_due_date" in new_order_page.text or "Échéance" in new_order_page.text,
        "comments": "comments" in new_order_page.text or "Commentaires" in new_order_page.text,
        "add-client": "Ajouter un client" in new_order_page.text or "add-client" in new_order_page.text,
    }
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}: {'Présent' if result else 'Absent'}")
    
    # 4. Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DU TEST")
    print("=" * 60)
    print(f"✅ Connexion: {'Réussie' if login_response.status_code in [302, 200] else 'Échouée'}")
    print(f"✅ Page /orders/new: {'Accessible' if new_order_page.status_code == 200 else 'Non accessible'}")
    print(f"✅ Formulaire: {'Présent' if any(checks.values()) else 'Absent'}")
    
    all_checks_passed = all(checks.values())
    if all_checks_passed:
        print("\n🎉 Tous les tests sont passés avec succès !")
    else:
        print("\n⚠️  Certains éléments du formulaire sont manquants")
    
    return all_checks_passed

if __name__ == '__main__':
    try:
        success = test_order_creation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

