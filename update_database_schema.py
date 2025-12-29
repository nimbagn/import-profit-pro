#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de mise à jour du schéma de base de données
Vérifie et ajoute les colonnes manquantes pour correspondre aux modèles
"""

import sys
from sqlalchemy import text, inspect
from app import app, db
from models import User, Role

def check_and_add_column(table_name, column_name, column_type, nullable=True, default=None):
    """Vérifie si une colonne existe et l'ajoute si nécessaire"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name not in columns:
        print(f"  ➕ Ajout de la colonne '{column_name}' à la table '{table_name}'...")
        nullable_str = "NULL" if nullable else "NOT NULL"
        default_str = f" DEFAULT {default}" if default else ""
        
        if column_type.startswith("VARCHAR"):
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {nullable_str}{default_str}"
        elif column_type.startswith("INT"):
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {nullable_str}{default_str}"
        elif column_type.startswith("TEXT"):
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        elif column_type.startswith("BOOLEAN") or column_type.startswith("TINYINT"):
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} TINYINT(1) {nullable_str}{default_str}"
        elif column_type.startswith("DATETIME"):
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} DATETIME {nullable_str}{default_str}"
        elif column_type.startswith("DATE"):
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} DATE {nullable_str}{default_str}"
        else:
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {nullable_str}{default_str}"
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text(alter_sql))
                conn.commit()
            print(f"  ✅ Colonne '{column_name}' ajoutée avec succès")
            return True
        except Exception as e:
            print(f"  ⚠️ Erreur lors de l'ajout de '{column_name}': {e}")
            return False
    else:
        print(f"  ✓ Colonne '{column_name}' existe déjà")
        return True

def update_database_schema():
    """Met à jour le schéma de la base de données"""
    print("🔄 Mise à jour du schéma de la base de données...")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Vérifier et mettre à jour la table 'roles'
            print("\n📋 Table 'roles':")
            check_and_add_column('roles', 'code', 'VARCHAR(50)', nullable=True)
            check_and_add_column('roles', 'permissions', 'TEXT', nullable=True)
            check_and_add_column('roles', 'description', 'TEXT', nullable=True)
            check_and_add_column('roles', 'created_at', 'DATETIME', nullable=False, default='CURRENT_TIMESTAMP')
            check_and_add_column('roles', 'updated_at', 'DATETIME', nullable=True)
            
            # Vérifier et mettre à jour la table 'users'
            print("\n📋 Table 'users':")
            check_and_add_column('users', 'username', 'VARCHAR(80)', nullable=False)
            check_and_add_column('users', 'email', 'VARCHAR(120)', nullable=True)
            check_and_add_column('users', 'password_hash', 'VARCHAR(255)', nullable=False)
            check_and_add_column('users', 'full_name', 'VARCHAR(120)', nullable=True)
            check_and_add_column('users', 'phone', 'VARCHAR(20)', nullable=True)
            check_and_add_column('users', 'role_id', 'BIGINT UNSIGNED', nullable=True)
            check_and_add_column('users', 'is_active', 'TINYINT(1)', nullable=False, default='1')
            check_and_add_column('users', 'last_login', 'DATETIME', nullable=True)
            check_and_add_column('users', 'created_at', 'DATETIME', nullable=False, default='CURRENT_TIMESTAMP')
            check_and_add_column('users', 'updated_at', 'DATETIME', nullable=True)
            
            # Ajouter index unique sur username si nécessaire
            print("\n📋 Index et contraintes:")
            try:
                with db.engine.connect() as conn:
                    # Vérifier si l'index existe
                    result = conn.execute(text("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.statistics 
                        WHERE table_schema = DATABASE() 
                        AND table_name = 'users' 
                        AND index_name = 'idx_user_username'
                    """))
                    if result.fetchone()[0] == 0:
                        print("  ➕ Ajout de l'index unique sur users.username...")
                        conn.execute(text("CREATE UNIQUE INDEX idx_user_username ON users(username)"))
                        conn.commit()
                        print("  ✅ Index ajouté")
                    else:
                        print("  ✓ Index idx_user_username existe déjà")
            except Exception as e:
                print(f"  ⚠️ Erreur lors de l'ajout de l'index: {e}")
            
            print("\n" + "=" * 60)
            print("✅ Mise à jour du schéma terminée")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la mise à jour: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = update_database_schema()
    sys.exit(0 if success else 1)

