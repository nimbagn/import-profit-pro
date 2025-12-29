#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test complet pour vérifier toutes les fonctionnalités de l'application
"""

import requests
import sys
import time

BASE_URL = "http://localhost:5002"

def test_route(url, name, expected_status=200):
    """Teste une route et affiche le résultat"""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5)
        status = "✅" if response.status_code == expected_status else "❌"
        print(f"{status} {name:40} - Status: {response.status_code}")
        return response.status_code == expected_status
    except requests.exceptions.ConnectionError:
        print(f"❌ {name:40} - Erreur: Serveur non accessible")
        return False
    except Exception as e:
        print(f"❌ {name:40} - Erreur: {str(e)}")
        return False

def test_api(url, name):
    """Teste une API et vérifie le format JSON"""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                status = "✅"
                info = f"Données: {len(data) if isinstance(data, list) else 'OK'}"
            except:
                status = "⚠️"
                info = "Format JSON invalide"
        else:
            status = "❌"
            info = f"Status: {response.status_code}"
        print(f"{status} {name:40} - {info}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"❌ {name:40} - Erreur: Serveur non accessible")
        return False
    except Exception as e:
        print(f"❌ {name:40} - Erreur: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🧪 TEST COMPLET DE TOUTES LES FONCTIONNALITÉS")
    print("=" * 70)
    print()
    
    # Attendre que le serveur soit prêt
    print("⏳ Vérification de la disponibilité du serveur...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code == 200:
                print("✅ Serveur accessible !\n")
                break
        except:
            if i < 9:
                time.sleep(1)
            else:
                print("❌ Serveur non accessible. Assurez-vous que l'application est démarrée.")
                sys.exit(1)
    
    results = []
    
    print("📄 TEST DES PAGES PRINCIPALES")
    print("-" * 70)
    results.append(test_route("/", "Page d'accueil"))
    results.append(test_route("/simulations", "Liste des simulations"))
    results.append(test_route("/simulations/new", "Nouvelle simulation"))
    results.append(test_route("/articles", "Liste des articles"))
    results.append(test_route("/articles/new", "Nouvel article"))
    print()
    
    print("📊 TEST DES PAGES FORECAST & VENTES")
    print("-" * 70)
    results.append(test_route("/forecast", "Dashboard prévisions"))
    results.append(test_route("/forecast/new", "Nouvelle prévision"))
    results.append(test_route("/forecast/list", "Liste des prévisions"))
    results.append(test_route("/forecast/performance", "Performance prévisions"))
    results.append(test_route("/forecast/import", "Import de données"))
    print()
    
    print("🔌 TEST DES APIs")
    print("-" * 70)
    results.append(test_api("/api/test", "API Test"))
    results.append(test_api("/api/simulations", "API Simulations"))
    results.append(test_api("/api/articles", "API Articles"))
    print()
    
    print("🛠️ TEST DES PAGES D'ERREUR")
    print("-" * 70)
    results.append(test_route("/page-inexistante", "Page 404", 404))
    print()
    
    # Résumé
    print("=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"✅ Tests réussis: {passed}/{total}")
    print(f"❌ Tests échoués: {failed}/{total}")
    print(f"📈 Taux de réussite: {(passed/total*100):.1f}%")
    print()
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT PASSÉS ! L'application fonctionne parfaitement.")
        return 0
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

