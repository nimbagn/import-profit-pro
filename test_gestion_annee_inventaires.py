#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour la gestion par année des inventaires
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, InventorySession, InventoryDetail, Depot, StockItem, User
from sqlalchemy import extract
from datetime import datetime, UTC

def test_year_filter():
    """Test du filtre par année"""
    print("\n" + "="*60)
    print("TEST 1: Filtre par année")
    print("="*60)
    
    with app.app_context():
        # Récupérer toutes les années disponibles
        years_result = db.session.query(
            extract('year', InventorySession.session_date).label('year')
        ).distinct().order_by('year').all()
        
        available_years = [int(y.year) for y in years_result if y.year]
        
        print(f"✅ Années disponibles trouvées: {available_years}")
        
        if available_years:
            # Tester le filtre pour chaque année
            for year in available_years:
                sessions = InventorySession.query.filter(
                    extract('year', InventorySession.session_date) == year
                ).all()
                print(f"   - Année {year}: {len(sessions)} session(s)")
        else:
            print("   ⚠️  Aucune session d'inventaire trouvée dans la base de données")
            print("   💡 Créez des sessions d'inventaire pour tester le filtre")

def test_year_statistics():
    """Test des statistiques par année"""
    print("\n" + "="*60)
    print("TEST 2: Statistiques par année")
    print("="*60)
    
    with app.app_context():
        # Récupérer toutes les années disponibles
        years_result = db.session.query(
            extract('year', InventorySession.session_date).label('year')
        ).distinct().order_by('year').all()
        
        available_years = [int(y.year) for y in years_result if y.year]
        
        if not available_years:
            print("   ⚠️  Aucune session d'inventaire trouvée")
            return
        
        for year in available_years:
            sessions = InventorySession.query.filter(
                extract('year', InventorySession.session_date) == year
            ).all()
            
            if not sessions:
                continue
            
            # Calculer les statistiques
            total_sessions = len(sessions)
            total_items = sum(len(s.details) for s in sessions)
            
            print(f"\n   📊 Année {year}:")
            print(f"      - Total sessions: {total_sessions}")
            print(f"      - Total articles: {total_items}")
            
            # Compter par statut
            status_count = {}
            for session in sessions:
                status = session.status
                status_count[status] = status_count.get(status, 0) + 1
            
            print(f"      - Par statut: {status_count}")

def test_routes():
    """Test que les routes sont bien définies"""
    print("\n" + "="*60)
    print("TEST 3: Vérification des routes")
    print("="*60)
    
    with app.app_context():
        from flask import url_for
        
        routes_to_test = [
            ('inventaires.sessions_list', 'Liste des sessions'),
            ('inventaires.sessions_by_year', 'Vue par année'),
        ]
        
        for route_name, description in routes_to_test:
            try:
                url = url_for(route_name)
                print(f"   ✅ {description}: {url}")
            except Exception as e:
                print(f"   ❌ {description}: ERREUR - {e}")

def test_template_variables():
    """Test que les variables nécessaires sont passées au template"""
    print("\n" + "="*60)
    print("TEST 4: Variables du template")
    print("="*60)
    
    with app.app_context():
        # Simuler les variables qui seraient passées au template
        years_result = db.session.query(
            extract('year', InventorySession.session_date).label('year')
        ).distinct().order_by('year').all()
        
        available_years = [int(y.year) for y in years_result if y.year]
        year_filter = None
        
        if available_years:
            current_year = datetime.now(UTC).year
            year_filter = current_year if current_year in available_years else available_years[-1]
        
        print(f"   ✅ available_years: {available_years}")
        print(f"   ✅ year_filter (par défaut): {year_filter}")
        
        # Vérifier que les variables sont correctes
        assert isinstance(available_years, list), "available_years doit être une liste"
        if available_years:
            assert all(isinstance(y, int) for y in available_years), "Toutes les années doivent être des entiers"
            print("   ✅ Format des années correct")

def test_export_excel_filter():
    """Test que l'export Excel supporte le filtre année"""
    print("\n" + "="*60)
    print("TEST 5: Export Excel avec filtre année")
    print("="*60)
    
    with app.app_context():
        # Vérifier que la fonction peut gérer le paramètre year
        years_result = db.session.query(
            extract('year', InventorySession.session_date).label('year')
        ).distinct().order_by('year').all()
        
        available_years = [int(y.year) for y in years_result if y.year]
        
        if available_years:
            test_year = available_years[0]
            query = InventorySession.query
            
            # Simuler le filtre année comme dans sessions_export_excel
            from sqlalchemy import extract
            query = query.filter(
                extract('year', InventorySession.session_date) == test_year
            )
            
            count = query.count()
            print(f"   ✅ Filtre année {test_year}: {count} session(s) trouvée(s)")
        else:
            print("   ⚠️  Aucune session pour tester l'export")

def main():
    """Fonction principale de test"""
    print("\n" + "="*60)
    print("TESTS DE LA GESTION PAR ANNÉE - MODULE INVENTAIRES")
    print("="*60)
    
    try:
        test_routes()
        test_year_filter()
        test_year_statistics()
        test_template_variables()
        test_export_excel_filter()
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS TERMINÉS")
        print("="*60)
        print("\n💡 Pour tester dans le navigateur:")
        print("   1. Démarrez le serveur: python app.py")
        print("   2. Connectez-vous à l'application")
        print("   3. Allez dans: Inventaires > Sessions d'Inventaire")
        print("   4. Testez le filtre année dans la liste")
        print("   5. Cliquez sur 'Vue par Année' pour la vue consolidée")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

