#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer la table search_index en utilisant la configuration du projet
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW

def create_app():
    """Créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration de la base de données
    try:
        import pymysql
        db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return None
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'charset': 'utf8mb4'}
    }
    
    db.init_app(app)
    return app

def create_search_index_table():
    """Créer la table search_index"""
    app = create_app()
    if not app:
        return False
    
    with app.app_context():
        try:
            # Lire le script SQL
            sql_file = os.path.join(os.path.dirname(__file__), 'create_search_index_table.sql')
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Exécuter le script SQL
            # Remplacer FULLTEXT INDEX si MySQL ne le supporte pas
            sql_content = sql_content.replace(
                'FULLTEXT INDEX idx_search_fulltext (title, content, keywords)',
                '-- FULLTEXT INDEX idx_search_fulltext (title, content, keywords) -- Désactivé pour compatibilité'
            )
            
            # Exécuter chaque commande SQL
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            
            for command in commands:
                if command:
                    try:
                        db.session.execute(db.text(command))
                        db.session.commit()
                    except Exception as e:
                        # Si la table existe déjà, ce n'est pas grave
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            print(f"⚠️  Table déjà existante (ignoré)")
                        else:
                            print(f"⚠️  Erreur lors de l'exécution: {e}")
            
            # Vérifier que la table existe
            result = db.session.execute(db.text("SHOW TABLES LIKE 'search_index'"))
            if result.fetchone():
                print("✅ Table 'search_index' créée avec succès!")
                return True
            else:
                print("❌ La table 'search_index' n'a pas été créée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la création de la table: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🔄 Création de la table search_index...")
    print("=" * 60)
    success = create_search_index_table()
    print("=" * 60)
    if success:
        print("✅ Terminé avec succès!")
    else:
        print("❌ Échec de la création")
    sys.exit(0 if success else 1)

