#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier les simulations dans la base de données
"""

import sys
import os
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text, inspect

def check_simulations():
    """Vérifier les simulations dans la base de données"""
    
    with app.app_context():
        print("🔍 Vérification des simulations dans la base de données")
        print("=" * 60)
        
        try:
            # Vérifier les colonnes de la table
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('simulations')]
            print(f"📋 Colonnes disponibles dans la table 'simulations':")
            for col in columns:
                print(f"   - {col}")
            print()
            
            # Compter les simulations
            result = db.session.execute(text("SELECT COUNT(*) as count FROM simulations"))
            count = result.fetchone()[0]
            print(f"📊 Nombre total de simulations: {count}")
            print()
            
            if count > 0:
                # Récupérer les simulations
                select_cols = ', '.join(columns)
                result = db.session.execute(text(f"""
                    SELECT {select_cols}
                    FROM simulations 
                    ORDER BY created_at DESC
                    LIMIT 10
                """))
                
                print(f"📋 Dernières {min(count, 10)} simulations:")
                print("-" * 60)
                
                for idx, row in enumerate(result, 1):
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    
                    print(f"\n{idx}. Simulation ID: {row_dict.get('id', 'N/A')}")
                    print(f"   Date: {row_dict.get('created_at', 'N/A')}")
                    print(f"   Taux USD: {row_dict.get('rate_usd', 'N/A')}")
                    print(f"   Taux EUR: {row_dict.get('rate_eur', 'N/A')}")
                    print(f"   Statut: {'Terminée' if row_dict.get('is_completed') else 'En cours'}")
                    
                    # Vérifier les items
                    sim_id = row_dict.get('id')
                    if sim_id:
                        items_result = db.session.execute(text(f"""
                            SELECT COUNT(*) as count 
                            FROM simulation_items 
                            WHERE simulation_id = {sim_id}
                        """))
                        items_count = items_result.fetchone()[0]
                        print(f"   Articles: {items_count}")
            else:
                print("⚠️ Aucune simulation trouvée dans la base de données")
                print()
                print("💡 Pour créer une simulation:")
                print("   1. Allez sur http://localhost:5002/simulations/new")
                print("   2. Remplissez le formulaire")
                print("   3. Ajoutez des articles")
                print("   4. Validez la simulation")
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_simulations()

