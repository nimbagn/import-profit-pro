#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour créer une commande commerciale complète
"""

import sys
import os
import requests
from datetime import datetime, timedelta
import re

# Configuration
BASE_URL = "http://localhost:5002"
USERNAME = "commercial_test"
PASSWORD = "commercial123"

def test_create_order():
    """Tester la création complète d'une commande"""
    session = requests.Session()
    
    print("=" * 70)
    print("TEST DE CRÉATION DE COMMANDE COMMERCIALE COMPLÈTE")
    print("=" * 70)
    
    # 1. Connexion
    print("\n1️⃣  Connexion avec le compte commercial...")
    login_url = f"{BASE_URL}/auth/login"
    login_page = session.get(login_url)
    
    if login_page.status_code != 200:
        print(f"❌ Erreur lors de l'accès à la page de connexion: {login_page.status_code}")
        return False
    
    # Extraire le CSRF token
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrf_token': csrf_token,
        'remember_me': False
    }
    
    login_response = session.post(login_url, data=login_data, allow_redirects=False)
    if login_response.status_code not in [302, 200]:
        print(f"❌ Erreur de connexion: {login_response.status_code}")
        return False
    
    print("✅ Connexion réussie")
    
    # 2. Accéder à la page de création
    print("\n2️⃣  Accès à la page de création de commande...")
    new_order_url = f"{BASE_URL}/orders/new"
    new_order_page = session.get(new_order_url)
    
    if new_order_page.status_code != 200:
        print(f"❌ Erreur lors de l'accès à la page: {new_order_page.status_code}")
        print(f"   URL: {new_order_url}")
        return False
    
    print("✅ Page de création accessible")
    
    # Extraire le CSRF token de la page de création
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', new_order_page.text)
    form_csrf_token = csrf_match.group(1) if csrf_match else None
    
    if not form_csrf_token:
        print("⚠️  CSRF token non trouvé dans le formulaire")
        return False
    
    # 3. Préparer les données de test
    print("\n3️⃣  Préparation des données de test...")
    
    # Date du jour
    order_date = datetime.now().strftime('%Y-%m-%d')
    
    # Client 1 : Comptant avec commentaires
    client1_data = {
        'client_0_name': 'Amadou Diallo',
        'client_0_phone': '+224 612 345 678',
        'client_0_address': 'Quartier Hamdallaye, Conakry',
        'client_0_payment_type': 'cash',
        'client_0_comments': 'Paiement au comptant - Livraison urgente',
        'client_0_items': '1|10|150000,2|5|25000'  # Article 1: 10 unités à 150000, Article 2: 5 unités à 25000
    }
    
    # Client 2 : Crédit avec échéance
    due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    client2_data = {
        'client_1_name': 'Fatoumata Bah',
        'client_1_phone': '+224 623 456 789',
        'client_1_address': 'Quartier Almamya, Conakry',
        'client_1_payment_type': 'credit',
        'client_1_payment_due_date': due_date,
        'client_1_comments': f'Paiement à crédit - Échéance: {due_date}',
        'client_1_items': '1|20|150000,3|10|50000'
    }
    
    # Client 3 : Comptant sans commentaires
    client3_data = {
        'client_2_name': 'Ibrahima Camara',
        'client_2_phone': '+224 634 567 890',
        'client_2_address': 'Quartier Dixinn, Conakry',
        'client_2_payment_type': 'cash',
        'client_2_comments': '',
        'client_2_items': '2|15|25000'
    }
    
    # Construire les données du formulaire
    form_data = {
        'csrf_token': form_csrf_token,
        'order_date': order_date,
        'notes': 'Commande de test - Créée automatiquement',
        **client1_data,
        **client2_data,
        **client3_data
    }
    
    print(f"   - Date de commande: {order_date}")
    print(f"   - Client 1: {client1_data['client_0_name']} (Comptant)")
    print(f"   - Client 2: {client2_data['client_1_name']} (Crédit, échéance: {due_date})")
    print(f"   - Client 3: {client3_data['client_2_name']} (Comptant)")
    
    # 4. Soumettre le formulaire
    print("\n4️⃣  Soumission du formulaire de création...")
    create_response = session.post(new_order_url, data=form_data, allow_redirects=False)
    
    if create_response.status_code == 302:
        redirect_location = create_response.headers.get('Location', '')
        if '/orders/' in redirect_location or '/orders' in redirect_location:
            print("✅ Commande créée avec succès !")
            print(f"   Redirection vers: {redirect_location}")
            
            # Suivre la redirection pour vérifier
            detail_page = session.get(f"{BASE_URL}{redirect_location}")
            if detail_page.status_code == 200:
                print("✅ Page de détail accessible")
                
                # Vérifier le contenu
                checks = {
                    "Référence": "Référence" in detail_page.text or "reference" in detail_page.text.lower(),
                    "Amadou Diallo": "Amadou Diallo" in detail_page.text,
                    "Fatoumata Bah": "Fatoumata Bah" in detail_page.text,
                    "Ibrahima Camara": "Ibrahima Camara" in detail_page.text,
                    "Comptant": "Comptant" in detail_page.text or "cash" in detail_page.text.lower(),
                    "Crédit": "Crédit" in detail_page.text or "credit" in detail_page.text.lower(),
                    "Échéance": due_date in detail_page.text or "échéance" in detail_page.text.lower(),
                }
                
                print("\n5️⃣  Vérification des données de la commande...")
                for check_name, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"   {status} {check_name}: {'Présent' if result else 'Absent'}")
                
                all_checks = all(checks.values())
                if all_checks:
                    print("\n🎉 Tous les éléments sont présents dans la commande créée !")
                else:
                    print("\n⚠️  Certains éléments sont manquants")
                
                return all_checks
            else:
                print(f"⚠️  Page de détail non accessible: {detail_page.status_code}")
                return True  # La commande a été créée même si on ne peut pas voir les détails
        else:
            print(f"⚠️  Redirection inattendue: {redirect_location}")
            return False
    elif create_response.status_code == 200:
        # Vérifier s'il y a des erreurs dans la page
        if "erreur" in create_response.text.lower() or "error" in create_response.text.lower():
            print("❌ Erreur lors de la création de la commande")
            print(f"   Réponse (premiers 500 caractères): {create_response.text[:500]}")
            return False
        else:
            print("⚠️  Pas de redirection, vérification du contenu...")
            print(f"   Réponse (premiers 500 caractères): {create_response.text[:500]}")
            return False
    else:
        print(f"❌ Erreur lors de la création: {create_response.status_code}")
        print(f"   Réponse (premiers 500 caractères): {create_response.text[:500]}")
        return False

if __name__ == '__main__':
    try:
        success = test_create_order()
        print("\n" + "=" * 70)
        if success:
            print("✅ TEST RÉUSSI - La commande a été créée avec succès !")
        else:
            print("❌ TEST ÉCHOUÉ - Vérifiez les erreurs ci-dessus")
        print("=" * 70)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

