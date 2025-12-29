#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script complet pour créer les tables et ajouter la colonne client_phone
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db
from sqlalchemy import text

# Forcer l'utilisation de SQLite (comme l'application en fallback)
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
db_uri = f'sqlite:///{db_path}'
mysql_available = False
print(f"📊 Utilisation de SQLite: {db_path}")

# Créer l'application Flask minimale
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {'charset': 'utf8mb4'} if mysql_available else {}
}

# Initialiser SQLAlchemy
db.init_app(app)

def fix_database():
    """Créer les tables et ajouter la colonne client_phone"""
    with app.app_context():
        try:
            # Créer toutes les tables
            print("🔄 Création des tables...")
            db.create_all()
            print("✅ Tables créées")
            
            # Détecter le type de base de données
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
    success = fix_database()
    print("=" * 60)
    sys.exit(0 if success else 1)

