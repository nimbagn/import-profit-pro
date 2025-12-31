#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter la migration PostgreSQL : Ajout de la colonne additional_permissions
Permet d'attribuer des permissions supplémentaires aux utilisateurs RH
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db
from sqlalchemy import text

def execute_migration():
    """Exécuter la migration SQL sur PostgreSQL via SQLAlchemy"""
    print("=" * 70)
    print("🔧 MIGRATION POSTGRESQL : Permissions Supplémentaires")
    print("=" * 70)
    print()
    
    # Vérifier la connexion à la base de données
    try:
        with app.app_context():
            # Test de connexion
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            print("✅ Connexion à la base de données PostgreSQL réussie")
            print()
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        print()
        print("💡 Vérifiez que:")
        print("   - La variable DATABASE_URL est configurée")
        print("   - La base de données PostgreSQL est accessible")
        print("   - Les identifiants sont corrects")
        return False
    
    # Lire et exécuter le script SQL
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'add_additional_permissions_column_postgresql.sql')
    
    if not os.path.exists(script_path):
        print(f"❌ Fichier de migration introuvable: {script_path}")
        return False
    
    try:
        with app.app_context():
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            print("📄 Lecture du script de migration...")
            print()
            
            # Exécuter le script SQL
            # PostgreSQL utilise des blocs DO $$ ... END $$ pour les scripts conditionnels
            # On exécute le script en entier
            try:
                db.session.execute(text(sql_content))
                db.session.commit()
                print("✅ Migration exécutée avec succès!")
                print()
            except Exception as e:
                error_msg = str(e)
                # Ignorer les erreurs "already exists" qui sont normales
                if 'already exists' not in error_msg.lower() and 'duplicate' not in error_msg.lower():
                    print(f"⚠️  Avertissement: {error_msg}")
                    print("   (C'est peut-être normal si la colonne existe déjà)")
                    db.session.rollback()
                else:
                    print("✅ Migration exécutée (colonne peut-être déjà existante)")
                    db.session.commit()
            
            # Vérifier que la colonne existe
            print("🔍 Vérification de la colonne...")
            check_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users' 
                AND column_name = 'additional_permissions'
            """)
            
            result = db.session.execute(check_query)
            row = result.fetchone()
            
            if row:
                print(f"✅ Colonne vérifiée: {row[0]} ({row[1]})")
                print()
                print("=" * 70)
                print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
                print("=" * 70)
                print()
                print("📋 Prochaines étapes:")
                print("   1. Redémarrer l'application Flask")
                print("   2. Aller dans /auth/users pour modifier un utilisateur RH")
                print("   3. Vérifier la section 'Permissions Supplémentaires'")
                print()
                return True
            else:
                print("⚠️  La colonne n'a pas été trouvée après la migration")
                print("   Vérifiez les logs ci-dessus pour plus de détails")
                return False
                
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de la migration: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

if __name__ == '__main__':
    success = execute_migration()
    sys.exit(0 if success else 1)

