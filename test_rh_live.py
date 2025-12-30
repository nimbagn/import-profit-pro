#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test en live du module RH
Teste les routes HTTP réelles (nécessite que l'application soit démarrée)
"""

import requests
import sys
import time

BASE_URL = "http://localhost:5002"

def test_route(url, description, expected_status=200, requires_auth=True):
    """Teste une route et affiche le résultat"""
    try:
        print(f"\n🔍 Test: {description}")
        print(f"   URL: {BASE_URL}{url}")
        
        # Pour les routes qui nécessitent une authentification,
        # on s'attend à une redirection (302) vers /auth/login
        if requires_auth:
            expected_statuses = [expected_status, 302, 401]
        else:
            expected_statuses = [expected_status]
        
        response = requests.get(f"{BASE_URL}{url}", timeout=5, allow_redirects=False)
        status = response.status_code
        
        if status in expected_statuses:
            if status == 302:
                location = response.headers.get('Location', 'N/A')
                print(f"   ✅ Status: {status} (redirection attendue)")
                print(f"   ℹ️  Redirection vers: {location}")
            elif status == 401:
                print(f"   ✅ Status: {status} (authentification requise)")
            else:
                print(f"   ✅ Status: {status}")
            return True
        else:
            print(f"   ⚠️  Status: {status} (attendu: {expected_statuses})")
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
    print("🧪 TEST EN LIVE DU MODULE RESSOURCES HUMAINES")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT: L'application Flask doit être démarrée sur http://localhost:5002")
    print()
    
    # Attendre que le serveur soit prêt
    print("⏳ Vérification de la disponibilité du serveur...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code in [200, 302]:
                print("✅ Serveur accessible !\n")
                break
        except:
            if i < 9:
                time.sleep(1)
            else:
                print("❌ Serveur non accessible. Assurez-vous que l'application est démarrée.")
                print("   Commande: python app.py")
                sys.exit(1)
    
    results = []
    
    print("📋 TEST DES ROUTES PRINCIPALES RH")
    print("-" * 70)
    results.append(test_route("/rh/personnel", "Liste du personnel"))
    results.append(test_route("/rh/personnel/new", "Nouveau personnel"))
    results.append(test_route("/rh/employees", "Liste des employés externes"))
    results.append(test_route("/rh/employees/new", "Nouvel employé externe"))
    results.append(test_route("/rh/activites", "Liste des activités"))
    results.append(test_route("/rh/statistiques", "Statistiques RH"))
    print()
    
    print("📄 TEST DES ROUTES DE DÉTAILS (nécessitent un ID)")
    print("-" * 70)
    results.append(test_route("/rh/personnel/1", "Détails personnel (ID=1)"))
    results.append(test_route("/rh/employees/1", "Détails employé (ID=1)"))
    print()
    
    print("📝 TEST DES ROUTES DE FORMULAIRES")
    print("-" * 70)
    results.append(test_route("/rh/personnel/1/edit", "Modifier personnel (ID=1)"))
    results.append(test_route("/rh/employees/1/edit", "Modifier employé (ID=1)"))
    print()
    
    print("📄 TEST DES ROUTES DE GESTION (Contrats, Formations, etc.)")
    print("-" * 70)
    results.append(test_route("/rh/employees/1/contracts", "Liste des contrats (employé ID=1)"))
    results.append(test_route("/rh/employees/1/contracts/new", "Nouveau contrat (employé ID=1)"))
    results.append(test_route("/rh/employees/1/trainings", "Liste des formations (employé ID=1)"))
    results.append(test_route("/rh/employees/1/trainings/new", "Nouvelle formation (employé ID=1)"))
    results.append(test_route("/rh/employees/1/evaluations", "Liste des évaluations (employé ID=1)"))
    results.append(test_route("/rh/employees/1/evaluations/new", "Nouvelle évaluation (employé ID=1)"))
    results.append(test_route("/rh/employees/1/absences", "Liste des absences (employé ID=1)"))
    results.append(test_route("/rh/employees/1/absences/new", "Nouvelle absence (employé ID=1)"))
    print()
    
    # Résumé
    print("=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total de tests: {total}")
    print(f"✅ Réussis: {passed}")
    print(f"❌ Échoués: {failed}")
    print(f"📈 Taux de réussite: {(passed/total*100):.1f}%")
    print()
    
    if failed == 0:
        print("🎉 Tous les tests sont passés !")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("   Note: Les échecs peuvent être dus à:")
        print("   - Routes nécessitant une authentification (redirection 302)")
        print("   - Routes nécessitant des IDs valides (erreur 404)")
        print("   - Routes nécessitant des permissions spécifiques (erreur 403)")
    print()
    print("💡 Pour tester avec authentification:")
    print("   1. Connectez-vous manuellement sur http://localhost:5002/auth/login")
    print("   2. Utilisez un compte admin ou avec rôle RH")
    print("   3. Testez les routes depuis le navigateur")
    print("=" * 70)

if __name__ == '__main__':
    main()

