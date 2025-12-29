#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter la colonne client_phone aux tables SQLite
"""

import sqlite3
import os

# Chemin vers la base de données SQLite
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')

if not os.path.exists(db_path):
    print(f"❌ Base de données non trouvée: {db_path}")
    sys.exit(1)

print(f"📊 Base de données: {db_path}")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifier et ajouter client_phone à stock_outgoings
try:
    cursor.execute("SELECT client_phone FROM stock_outgoings LIMIT 1")
    print("✅ La colonne client_phone existe déjà dans stock_outgoings")
except sqlite3.OperationalError:
    print("🔄 Ajout de la colonne client_phone à stock_outgoings...")
    try:
        cursor.execute("ALTER TABLE stock_outgoings ADD COLUMN client_phone VARCHAR(20)")
        conn.commit()
        print("✅ Colonne client_phone ajoutée à stock_outgoings")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()

# Vérifier et ajouter client_phone à stock_returns
try:
    cursor.execute("SELECT client_phone FROM stock_returns LIMIT 1")
    print("✅ La colonne client_phone existe déjà dans stock_returns")
except sqlite3.OperationalError:
    print("🔄 Ajout de la colonne client_phone à stock_returns...")
    try:
        cursor.execute("ALTER TABLE stock_returns ADD COLUMN client_phone VARCHAR(20)")
        conn.commit()
        print("✅ Colonne client_phone ajoutée à stock_returns")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()

conn.close()
print("\n✅ Mise à jour terminée !")

