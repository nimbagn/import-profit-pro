#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test de connexion PostgreSQL
Vérifie que la connexion à PostgreSQL fonctionne avant d'exécuter la migration
"""

import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(__file__))

def test_connection():
    """Tester la connexion à PostgreSQL"""
    try:
        from app import app
        from models import db
        
        with app.app_context():
            # Tester la connexion
            db.engine.connect()
            
            # Afficher les informations de connexion
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            
            print("=" * 70)
            print("🔍 TEST DE CONNEXION POSTGRESQL")
            print("=" * 70)
            print()
            
            # Masquer le mot de passe dans l'URI
            if '@' in db_uri:
                parts = db_uri.split('@')
                if ':' in parts[0]:
                    user_pass = parts[0].split('://')[1]
                    if ':' in user_pass:
                        user = user_pass.split(':')[0]
                        masked_uri = db_uri.replace(user_pass, f"{user}:***")
                    else:
                        masked_uri = db_uri
                else:
                    masked_uri = db_uri
            else:
                masked_uri = db_uri
            
            print(f"✅ Connexion réussie !")
            print(f"   Type de base: {'PostgreSQL' if 'postgresql' in db_uri.lower() else 'MySQL' if 'mysql' in db_uri.lower() else 'SQLite'}")
            print(f"   URI: {masked_uri}")
            print()
            
            # Vérifier si les tables RH existent déjà
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            rh_tables = [
                'user_activity_logs',
                'employees',
                'employee_contracts',
                'employee_trainings',
                'employee_evaluations',
                'employee_absences'
            ]
            
            existing_rh_tables = [t for t in rh_tables if t in existing_tables]
            
            if existing_rh_tables:
                print("⚠️  Tables RH déjà existantes:")
                for table in existing_rh_tables:
                    print(f"   - {table}")
                print()
                print("💡 La migration peut être exécutée (CREATE TABLE IF NOT EXISTS)")
            else:
                print("✅ Aucune table RH existante - Migration prête à être exécutée")
            
            print()
            print("=" * 70)
            return True
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Assurez-vous d'être dans le répertoire du projet")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("💡 Vérifiez:")
        print("   - Que DATABASE_URL est correctement configurée")
        print("   - Que PostgreSQL est accessible")
        print("   - Que les identifiants sont corrects")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

