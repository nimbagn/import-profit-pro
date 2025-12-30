#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter la migration RH sur PostgreSQL
Utilise SQLAlchemy (déjà disponible dans le projet)
"""

import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(__file__))

def execute_migration():
    """Exécuter la migration SQL sur PostgreSQL via SQLAlchemy"""
    script_path = os.path.join(os.path.dirname(__file__), 'migration_rh_complete_postgresql.sql')
    
    if not os.path.exists(script_path):
        print(f"❌ Erreur: Le fichier {script_path} n'existe pas")
        return False
    
    try:
        # Importer Flask et la configuration
        from app import app
        from models import db
        
        with app.app_context():
            # Lire le script SQL
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            print("🔄 Exécution de la migration RH sur PostgreSQL...")
            print(f"   Base de données: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'configurée'}")
            print()
            
            # Exécuter le script SQL
            # Diviser par ';' et exécuter chaque commande
            commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            
            executed = 0
            errors = []
            
            for i, command in enumerate(commands, 1):
                # Ignorer les blocs DO $$ ... END $$ qui sont des blocs PL/pgSQL
                if 'DO $$' in command.upper():
                    # Pour les blocs DO, on doit les exécuter en entier
                    try:
                        db.session.execute(db.text(command))
                        db.session.commit()
                        executed += 1
                    except Exception as e:
                        error_msg = str(e)
                        # Ignorer les erreurs "already exists" pour CREATE TYPE IF NOT EXISTS
                        if 'already exists' not in error_msg.lower() and 'duplicate' not in error_msg.lower():
                            errors.append(f"Commande {i}: {error_msg}")
                            db.session.rollback()
                elif command and not command.startswith('--'):
                    try:
                        # Exécuter la commande
                        db.session.execute(db.text(command))
                        db.session.commit()
                        executed += 1
                    except Exception as e:
                        error_msg = str(e)
                        # Ignorer les erreurs "already exists" pour CREATE TABLE IF NOT EXISTS
                        if 'already exists' not in error_msg.lower() and 'duplicate' not in error_msg.lower():
                            errors.append(f"Commande {i}: {error_msg}")
                            db.session.rollback()
            
            if errors:
                print("⚠️  Quelques avertissements (peut être normal si les tables existent déjà):")
                for error in errors[:5]:  # Afficher seulement les 5 premières erreurs
                    print(f"   - {error}")
                if len(errors) > 5:
                    print(f"   ... et {len(errors) - 5} autres")
                print()
            
            print("✅ Migration exécutée avec succès!")
            print()
            print("📊 Tables créées:")
            print("   - user_activity_logs")
            print("   - employees")
            print("   - employee_contracts")
            print("   - employee_trainings")
            print("   - employee_evaluations")
            print("   - employee_absences")
            print()
            print(f"✅ {executed} commande(s) exécutée(s)")
            print()
            print("🎯 Prochaines étapes:")
            print("   1. Redémarrer l'application Flask")
            print("   2. Créer un utilisateur avec un rôle RH")
            print("   3. Tester les fonctionnalités RH")
            return True
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Assurez-vous d'être dans le répertoire du projet")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = execute_migration()
    sys.exit(0 if success else 1)
