#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter automatiquement les colonnes manquantes à la table simulations
Gère les erreurs si les colonnes existent déjà
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db
from sqlalchemy import text, inspect

app = Flask(__name__)

# Configuration de la base de données (utiliser la même logique que app.py)
try:
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    mysql_available = True
    print(f"✅ Configuration MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
except Exception as e:
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print(f"⚠️ Fallback vers SQLite: {e}")
    mysql_available = False

db.init_app(app)

def fix_simulations_table():
    """Ajouter les colonnes manquantes à la table simulations"""
    with app.app_context():
        if not mysql_available:
            print("ℹ️ SQLite détecté - Création automatique des tables et colonnes...")
            try:
                db.create_all()
                print("✅ Tables et colonnes créées/vérifiées avec succès")
            except Exception as e:
                print(f"⚠️ Erreur lors de la création: {e}")
            return
        
        print("🔄 Vérification et ajout des colonnes manquantes (MySQL)...")
        
        # Colonnes à ajouter
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
        
        # Vérifier quelles colonnes existent
        try:
            result = db.session.execute(text("SHOW COLUMNS FROM simulations"))
            existing_columns = [row[0] for row in result]
            print(f"✅ Colonnes existantes: {', '.join(existing_columns)}")
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des colonnes: {e}")
            print("\n💡 SOLUTION: Exécutez manuellement le script SQL:")
            print("   mysql -u root -p madargn < scripts/add_rate_xof_simple.sql")
            print("   mysql -u root -p madargn < scripts/create_price_lists_tables.sql")
            return
        
        # Ajouter les colonnes manquantes
        added_count = 0
        for column_name, column_def, after_column in columns_to_add:
            if column_name not in existing_columns:
                try:
                    # Vérifier que la colonne AFTER existe
                    if after_column not in existing_columns and after_column != "rate_eur":
                        # Si la colonne AFTER n'existe pas, utiliser la dernière colonne existante
                        after_column = existing_columns[-1] if existing_columns else "rate_eur"
                    
                    sql = f"ALTER TABLE simulations ADD COLUMN {column_name} {column_def} AFTER {after_column}"
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"✅ Colonne '{column_name}' ajoutée")
                    added_count += 1
                    existing_columns.append(column_name)  # Mettre à jour la liste
                except Exception as e:
                    error_msg = str(e)
                    if "Duplicate column name" in error_msg or "already exists" in error_msg.lower():
                        print(f"ℹ️ Colonne '{column_name}' existe déjà")
                    else:
                        print(f"⚠️ Erreur lors de l'ajout de '{column_name}': {e}")
                        db.session.rollback()
            else:
                print(f"ℹ️ Colonne '{column_name}' existe déjà")
        
        if added_count > 0:
            print(f"✅ {added_count} colonne(s) ajoutée(s) avec succès")
        else:
            print("ℹ️ Toutes les colonnes existent déjà")
        
        # Créer aussi les tables des fiches de prix
        print("\n🔄 Vérification des tables des Fiches de Prix...")
        try:
            db.create_all()
            print("✅ Tables créées/vérifiées")
        except Exception as e:
            print(f"⚠️ Erreur lors de la création des tables: {e}")

if __name__ == '__main__':
    fix_simulations_table()

