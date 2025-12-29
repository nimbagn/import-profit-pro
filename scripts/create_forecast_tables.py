#!/usr/bin/env python3
"""
Script pour créer les tables forecasts et forecast_items
Utilise la connexion Flask existante
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Forecast, ForecastItem

def create_forecast_tables():
    """Créer les tables forecasts et forecast_items"""
    with app.app_context():
        try:
            print("🔄 Création des tables forecasts et forecast_items...")
            
            # Créer les tables
            db.create_all()
            
            # Vérifier que les tables existent
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'forecasts' in tables and 'forecast_items' in tables:
                print("✅ Tables créées avec succès!")
                print(f"   - forecasts")
                print(f"   - forecast_items")
                return True
            else:
                print("⚠️  Certaines tables n'ont pas été créées")
                print(f"   Tables existantes: {tables}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_forecast_tables()
    sys.exit(0 if success else 1)

