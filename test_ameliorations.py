#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test des améliorations du module Promotion
"""

import requests
import time
from datetime import datetime, date

BASE_URL = "http://localhost:5002"

def test_route(url, description, expected_status=200):
    """Teste une route et affiche le résultat"""
    print(f"\n{'='*60}")
    print(f"🧪 Test: {description}")
    print(f"📍 URL: {url}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        response = requests.get(url, allow_redirects=False, timeout=10)
        elapsed_time = time.time() - start_time
        
        status_emoji = "✅" if response.status_code == expected_status else "❌"
        print(f"{status_emoji} Status: {response.status_code} (attendu: {expected_status})")
        print(f"⏱️  Temps de réponse: {elapsed_time:.3f}s")
        
        if response.status_code == 302:
            print(f"🔄 Redirection vers: {response.headers.get('Location', 'N/A')}")
        
        # Vérifier la taille de la réponse
        content_length = len(response.content)
        print(f"📦 Taille de la réponse: {content_length:,} octets")
        
        # Vérifier si la pagination est présente dans le HTML
        if 'pagination' in response.text.lower() or 'page-item' in response.text:
            print("✅ Pagination détectée dans le HTML")
        
        # Vérifier si les filtres sont présents
        if 'filter' in response.text.lower() or 'filtre' in response.text.lower():
            print("✅ Filtres détectés dans le HTML")
        
        # Vérifier si l'export Excel est présent
        if 'export' in response.text.lower() or 'excel' in response.text.lower():
            print("✅ Bouton Export Excel détecté")
        
        return response.status_code == expected_status, elapsed_time
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur")
        return False, 0
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, 0

def test_pagination(url_base, route_name):
    """Teste la pagination sur une route"""
    print(f"\n{'='*60}")
    print(f"📄 Test Pagination: {route_name}")
    print(f"{'='*60}")
    
    tests = [
        ("Page 1", f"{url_base}?page=1"),
        ("Page 2", f"{url_base}?page=2"),
        ("25 par page", f"{url_base}?per_page=25"),
        ("50 par page", f"{url_base}?per_page=50"),
        ("100 par page", f"{url_base}?per_page=100"),
    ]
    
    results = []
    for desc, url in tests:
        success, elapsed = test_route(url, desc, expected_status=200)
        results.append((desc, success, elapsed))
    
    return results

def test_search(url_base, route_name):
    """Teste la recherche sur une route"""
    print(f"\n{'='*60}")
    print(f"🔍 Test Recherche: {route_name}")
    print(f"{'='*60}")
    
    tests = [
        ("Recherche simple", f"{url_base}?search=test"),
        ("Recherche vide", f"{url_base}?search="),
        ("Recherche avec caractères spéciaux", f"{url_base}?search=test%20test"),
    ]
    
    results = []
    for desc, url in tests:
        success, elapsed = test_route(url, desc, expected_status=200)
        results.append((desc, success, elapsed))
    
    return results

def test_filters(url_base, route_name):
    """Teste les filtres sur une route"""
    print(f"\n{'='*60}")
    print(f"🔧 Test Filtres: {route_name}")
    print(f"{'='*60}")
    
    today = date.today()
    date_from = today.strftime('%Y-%m-%d')
    date_to = today.strftime('%Y-%m-%d')
    
    tests = [
        ("Filtre par date", f"{url_base}?date_from={date_from}&date_to={date_to}"),
        ("Filtre par type", f"{url_base}?transaction_type=enlevement"),
        ("Filtre combiné", f"{url_base}?date_from={date_from}&transaction_type=enlevement&search=test"),
    ]
    
    results = []
    for desc, url in tests:
        success, elapsed = test_route(url, desc, expected_status=200)
        results.append((desc, success, elapsed))
    
    return results

def test_export(url_base, route_name):
    """Teste l'export Excel"""
    print(f"\n{'='*60}")
    print(f"📊 Test Export Excel: {route_name}")
    print(f"{'='*60}")
    
    try:
        url = f"{url_base}/export/excel"
        print(f"📍 URL: {url}")
        
        start_time = time.time()
        response = requests.get(url, allow_redirects=False, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Export réussi!")
            print(f"⏱️  Temps de génération: {elapsed_time:.3f}s")
            print(f"📦 Taille du fichier: {len(response.content):,} octets")
            
            # Vérifier le Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
                print(f"✅ Type de fichier correct: {content_type}")
            
            # Vérifier le Content-Disposition
            disposition = response.headers.get('Content-Disposition', '')
            if 'attachment' in disposition.lower():
                print(f"✅ Fichier en téléchargement: {disposition}")
            
            return True, elapsed_time
        elif response.status_code == 302:
            print(f"⚠️  Redirection (peut nécessiter authentification)")
            print(f"🔄 Redirection vers: {response.headers.get('Location', 'N/A')}")
            return False, elapsed_time
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False, elapsed_time
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, 0

def main():
    """Fonction principale de test"""
    print("\n" + "="*60)
    print("🚀 TESTS DES AMÉLIORATIONS - MODULE PROMOTION")
    print("="*60)
    print(f"⏰ Début des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier que le serveur est accessible
    print("\n🔍 Vérification du serveur...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Serveur accessible sur {BASE_URL}")
    except:
        print(f"❌ Serveur non accessible sur {BASE_URL}")
        print("⚠️  Assurez-vous que le serveur Flask est démarré")
        return
    
    results = {
        'members_list': [],
        'sales_list': [],
        'export': [],
    }
    
    # Test 1: Route members_list
    print("\n" + "="*60)
    print("TEST 1: Route Members List")
    print("="*60)
    members_url = f"{BASE_URL}/promotion/members"
    test_route(members_url, "Page principale members_list")
    results['members_list'].extend(test_pagination(members_url, "members_list"))
    results['members_list'].extend(test_search(members_url, "members_list"))
    
    # Test 2: Route sales_list
    print("\n" + "="*60)
    print("TEST 2: Route Sales List")
    print("="*60)
    sales_url = f"{BASE_URL}/promotion/sales"
    test_route(sales_url, "Page principale sales_list")
    results['sales_list'].extend(test_pagination(sales_url, "sales_list"))
    results['sales_list'].extend(test_search(sales_url, "sales_list"))
    results['sales_list'].extend(test_filters(sales_url, "sales_list"))
    
    # Test 3: Export Excel
    print("\n" + "="*60)
    print("TEST 3: Export Excel")
    print("="*60)
    export_success, export_time = test_export(sales_url, "sales_export")
    results['export'].append(("Export Excel", export_success, export_time))
    
    # Résumé des résultats
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    total_tests = 0
    total_success = 0
    total_time = 0
    
    for category, category_results in results.items():
        if category_results:
            print(f"\n📁 {category.upper()}:")
            for desc, success, elapsed in category_results:
                total_tests += 1
                if success:
                    total_success += 1
                total_time += elapsed
                status = "✅" if success else "❌"
                print(f"  {status} {desc}: {elapsed:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"📈 STATISTIQUES GLOBALES")
    print(f"{'='*60}")
    print(f"Total de tests: {total_tests}")
    print(f"Tests réussis: {total_success} ({total_success/total_tests*100:.1f}%)")
    print(f"Tests échoués: {total_tests - total_success}")
    print(f"Temps total: {total_time:.3f}s")
    print(f"Temps moyen par test: {total_time/total_tests:.3f}s" if total_tests > 0 else "N/A")
    print(f"\n⏰ Fin des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()

