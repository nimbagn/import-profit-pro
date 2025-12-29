#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test en live des routes de gestion des stocks
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5002"

def test_route(url, description, expected_status=200):
    """Teste une route et affiche le résultat"""
    try:
        print(f"\n🔍 Test: {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=5, allow_redirects=False)
        status = response.status_code
        
        if status == expected_status or (expected_status == 200 and status in [200, 302, 401]):
            print(f"   ✅ Status: {status} (attendu: {expected_status})")
            if status == 302:
                print(f"   ℹ️  Redirection vers: {response.headers.get('Location', 'N/A')}")
            return True
        else:
            print(f"   ⚠️  Status: {status} (attendu: {expected_status})")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Impossible de se connecter au serveur")
        print(f"   ℹ️  Vérifiez que le serveur Flask est démarré sur {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        print(f"   ⚠️  Timeout - Le serveur met trop de temps à répondre")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    print("=" * 70)
    print("🧪 TESTS EN LIVE - GESTION DES STOCKS")
    print("=" * 70)
    print(f"\n🌐 Serveur: {BASE_URL}")
    print("⏳ Vérification de la disponibilité du serveur...\n")
    
    # Test de base - Page d'accueil
    if not test_route(f"{BASE_URL}/", "Page d'accueil"):
        print("\n❌ Le serveur ne répond pas. Vérifiez qu'il est démarré.")
        sys.exit(1)
    
    # Routes de stocks (nécessitent authentification, donc 302 ou 401 attendu)
    routes_to_test = [
        ("/stocks/movements", "Liste des mouvements", 302),
        ("/stocks/receptions", "Liste des réceptions", 302),
        ("/stocks/outgoings", "Liste des sorties", 302),
        ("/stocks/returns", "Liste des retours", 302),
        ("/stocks/summary", "Récapitulatif du stock", 302),
        ("/stocks/movements/new", "Formulaire nouveau mouvement", 302),
        ("/stocks/receptions/new", "Formulaire nouvelle réception", 302),
        ("/stocks/outgoings/new", "Formulaire nouvelle sortie", 302),
        ("/stocks/returns/new", "Formulaire nouveau retour", 302),
    ]
    
    print("\n" + "=" * 70)
    print("📋 TEST DES ROUTES DE GESTION DES STOCKS")
    print("=" * 70)
    
    results = []
    for route, description, expected in routes_to_test:
        result = test_route(f"{BASE_URL}{route}", description, expected)
        results.append(result)
        time.sleep(0.5)  # Petite pause entre les requêtes
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n✅ Routes fonctionnelles: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 Toutes les routes répondent correctement!")
        print("\n💡 Pour tester les fonctionnalités complètes:")
        print("   1. Ouvrez http://localhost:5002 dans votre navigateur")
        print("   2. Connectez-vous avec un compte (admin/admin123)")
        print("   3. Testez les fonctionnalités de gestion des stocks")
    else:
        print(f"\n⚠️  {total_count - success_count} route(s) ont des problèmes")
        print("   Vérifiez les logs du serveur pour plus de détails")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

