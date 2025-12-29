#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter la colonne client_phone aux tables stock_outgoings et stock_returns
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import sys
from sqlalchemy import text

# Configuration de la base de données (même logique que app.py)
try:
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    mysql_available = True
except Exception as e:
    # Fallback vers SQLite
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
    db_uri = f'sqlite:///{db_path}'
    mysql_available = False

# Créer l'application Flask minimale
from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser SQLAlchemy
from models import db
db.init_app(app)

def add_client_phone_column():
    """Ajouter la colonne client_phone si elle n'existe pas"""
    with app.app_context():
        try:
            # Détecter le type de base de données
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            is_mysql = 'mysql' in db_uri.lower()
            is_sqlite = 'sqlite' in db_uri.lower()
            
            print(f"📊 Type de base de données: {'MySQL' if is_mysql else 'SQLite' if is_sqlite else 'Autre'}")
            
            # Pour stock_outgoings
            try:
                # Vérifier si la colonne existe en essayant de la sélectionner
                db.session.execute(text("SELECT client_phone FROM stock_outgoings LIMIT 1"))
                print("✅ La colonne client_phone existe déjà dans stock_outgoings")
            except Exception:
                # La colonne n'existe pas, l'ajouter
                print("🔄 Ajout de la colonne client_phone à stock_outgoings...")
                if is_mysql:
                    db.session.execute(text("""
                        ALTER TABLE stock_outgoings 
                        ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name
                    """))
                else:
                    # SQLite ne supporte pas AFTER, on ajoute juste la colonne
                    db.session.execute(text("""
                        ALTER TABLE stock_outgoings 
                        ADD COLUMN client_phone VARCHAR(20)
                    """))
                db.session.commit()
                print("✅ Colonne client_phone ajoutée à stock_outgoings")
            
            # Pour stock_returns
            try:
                # Vérifier si la colonne existe en essayant de la sélectionner
                db.session.execute(text("SELECT client_phone FROM stock_returns LIMIT 1"))
                print("✅ La colonne client_phone existe déjà dans stock_returns")
            except Exception:
                # La colonne n'existe pas, l'ajouter
                print("🔄 Ajout de la colonne client_phone à stock_returns...")
                if is_mysql:
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name
                    """))
                else:
                    # SQLite ne supporte pas AFTER, on ajoute juste la colonne
                    db.session.execute(text("""
                        ALTER TABLE stock_returns 
                        ADD COLUMN client_phone VARCHAR(20)
                    """))
                db.session.commit()
                print("✅ Colonne client_phone ajoutée à stock_returns")
            
            print("\n✅ Mise à jour de la base de données terminée !")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🚀 Mise à jour de la base de données...")
    print("=" * 60)
    success = add_client_phone_column()
    print("=" * 60)
    sys.exit(0 if success else 1)

