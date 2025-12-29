#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter les colonnes manquantes à la table simulations
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db
from sqlalchemy import text

app = Flask(__name__)

# Configuration de la base de données
try:
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    mysql_available = True
    print(f"✅ Configuration MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
except Exception as e:
    # Fallback vers SQLite
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print(f"⚠️ Fallback vers SQLite: {e}")
    mysql_available = False

db.init_app(app)

def add_missing_columns():
    """Ajouter les colonnes manquantes à la table simulations"""
    with app.app_context():
        try:
            # Vérifier si on est en MySQL
            if mysql_available:
                print("🔄 Ajout des colonnes manquantes dans MySQL...")
                
                # Liste des colonnes à ajouter avec leurs définitions
                columns_to_add = [
                    ("rate_xof", "DECIMAL(18,4) NOT NULL DEFAULT 0.0000", "rate_eur"),
                    ("customs_gnf", "DECIMAL(18,2) NOT NULL DEFAULT 0.00", "rate_xof"),
                    ("handling_gnf", "DECIMAL(18,2) NOT NULL DEFAULT 0.00", "customs_gnf"),
                    ("others_gnf", "DECIMAL(18,2) NOT NULL DEFAULT 0.00", "handling_gnf"),
                    ("transport_fixed_gnf", "DECIMAL(18,2) NOT NULL DEFAULT 0.00", "others_gnf"),
                    ("transport_per_kg_gnf", "DECIMAL(18,4) NOT NULL DEFAULT 0.0000", "transport_fixed_gnf"),
                    ("basis", "ENUM('value', 'weight') NOT NULL DEFAULT 'value'", "transport_per_kg_gnf"),
                    ("truck_capacity_tons", "DECIMAL(18,4) NOT NULL DEFAULT 0.0000", "basis"),
                    ("target_mode", "ENUM('none', 'price', 'purchase', 'global') NOT NULL DEFAULT 'none'", "truck_capacity_tons"),
                    ("target_margin_pct", "DECIMAL(18,4) NOT NULL DEFAULT 0.0000", "target_mode"),
                ]
                
                # Vérifier quelles colonnes existent déjà
                result = db.session.execute(text("SHOW COLUMNS FROM simulations"))
                existing_columns = [row[0] for row in result]
                
                for column_name, column_def, after_column in columns_to_add:
                    if column_name not in existing_columns:
                        try:
                            sql = f"ALTER TABLE simulations ADD COLUMN {column_name} {column_def} AFTER {after_column}"
                            db.session.execute(text(sql))
                            print(f"✅ Colonne '{column_name}' ajoutée")
                        except Exception as e:
                            print(f"⚠️ Erreur lors de l'ajout de '{column_name}': {e}")
                    else:
                        print(f"ℹ️ Colonne '{column_name}' existe déjà")
                
                db.session.commit()
                print("✅ Colonnes ajoutées avec succès")
                
            else:
                print("ℹ️ SQLite détecté - Les colonnes seront créées automatiquement avec db.create_all()")
                db.create_all()
                print("✅ Tables créées/mises à jour")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    add_missing_columns()

