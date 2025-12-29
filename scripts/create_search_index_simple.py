#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplifié pour créer la table search_index via SQLAlchemy
Utilise la même configuration que l'application Flask
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, SearchIndex

def create_app():
    """Créer l'application Flask avec la même configuration"""
    app = Flask(__name__)
    
    # Utiliser la même configuration que app.py
    try:
        import pymysql
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
        
        db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    except Exception as e:
        print(f"⚠️  Erreur de configuration MySQL: {e}")
        # Fallback SQLite
        db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'app.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    db.init_app(app)
    return app

def create_table():
    """Créer la table search_index"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Création de la table search_index...")
            print("=" * 60)
            
            # Créer uniquement la table SearchIndex
            SearchIndex.__table__.create(db.engine, checkfirst=True)
            
            print("✅ Table 'search_index' créée avec succès!")
            print("=" * 60)
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'duplicate' in error_msg:
                print("ℹ️  La table 'search_index' existe déjà")
                print("=" * 60)
                return True
            else:
                print(f"❌ Erreur: {e}")
                print("=" * 60)
                import traceback
                traceback.print_exc()
                return False

if __name__ == '__main__':
    success = create_table()
    sys.exit(0 if success else 1)

