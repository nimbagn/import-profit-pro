#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Python pour créer automatiquement les index de base de données
Détecte automatiquement la base de données depuis la configuration
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD_RAW
    import pymysql
    
    print(f"🔍 Connexion à la base de données: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # Connexion à MySQL
    connection = pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD_RAW,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    print(f"✅ Connexion réussie à la base de données '{DB_NAME}'")
    
    cursor = connection.cursor()
    
    # Lire le script SQL
    # Essayer d'abord le script intelligent, puis sécurisé, puis normal
    sql_file = Path(__file__).parent / 'add_database_indexes_smart.sql'
    if not sql_file.exists():
        sql_file = Path(__file__).parent / 'add_database_indexes_safe.sql'
    if not sql_file.exists():
        sql_file = Path(__file__).parent / 'add_database_indexes.sql'
    
    if not sql_file.exists():
        print(f"❌ Fichier SQL non trouvé: {sql_file}")
        sys.exit(1)
    
    # Lire et exécuter le script SQL (sans la ligne USE)
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Supprimer la ligne USE et les commentaires de début
    lines = sql_content.split('\n')
    sql_statements = []
    skip_use = True
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        if skip_use and line.upper().startswith('USE '):
            skip_use = False
            continue
        skip_use = False
        sql_statements.append(line)
    
    # Exécuter chaque instruction SQL
    full_sql = '\n'.join(sql_statements)
    
    # Séparer les instructions par ';'
    statements = [s.strip() + ';' for s in full_sql.split(';') if s.strip()]
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for statement in statements:
        if not statement or statement == ';' or statement.startswith('SET '):
            continue
        
        try:
            # Extraire le nom de l'index et de la table
            import re
            match = re.search(r'CREATE INDEX (\w+) ON (\w+)\(([^)]+)\)', statement)
            if match:
                index_name = match.group(1)
                table_name = match.group(2)
                columns = [col.strip() for col in match.group(3).split(',')]
                
                # Vérifier si la table existe
                check_table_sql = f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = '{DB_NAME}' 
                    AND table_name = '{table_name}'
                """
                cursor.execute(check_table_sql)
                table_exists = cursor.fetchone()[0] > 0
                
                if not table_exists:
                    print(f"⏭️  Table {table_name} n'existe pas (ignoré)")
                    skipped_count += 1
                    continue
                
                # Vérifier si toutes les colonnes existent
                all_columns_exist = True
                for col in columns:
                    check_col_sql = f"""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_schema = '{DB_NAME}' 
                        AND table_name = '{table_name}' 
                        AND column_name = '{col}'
                    """
                    cursor.execute(check_col_sql)
                    col_exists = cursor.fetchone()[0] > 0
                    if not col_exists:
                        print(f"⏭️  Colonne {col} n'existe pas dans {table_name} (ignoré)")
                        all_columns_exist = False
                        break
                
                if not all_columns_exist:
                    skipped_count += 1
                    continue
                
                # Vérifier si l'index existe déjà
                check_index_sql = f"""
                    SELECT COUNT(*) 
                    FROM information_schema.statistics 
                    WHERE table_schema = '{DB_NAME}' 
                    AND table_name = '{table_name}' 
                    AND index_name = '{index_name}'
                """
                cursor.execute(check_index_sql)
                index_exists = cursor.fetchone()[0] > 0
                
                if index_exists:
                    print(f"⏭️  Index {index_name} existe déjà sur {table_name}")
                    skipped_count += 1
                    continue
                
                # Créer l'index
                cursor.execute(statement)
                print(f"✅ Index {index_name} créé sur {table_name}")
                success_count += 1
            else:
                # Autres instructions SQL (SET, SELECT, etc.)
                if not statement.startswith('CREATE INDEX'):
                    continue
                cursor.execute(statement)
                if 'CREATE INDEX' in statement:
                    print(f"✅ Index créé")
                    success_count += 1
            
            connection.commit()
        except Exception as e:
            error_msg = str(e)
            # Ignorer les erreurs "Duplicate key name" (index existe déjà)
            if 'Duplicate key name' in error_msg or 'already exists' in error_msg.lower():
                print(f"⏭️  Index existe déjà (ignoré)")
                skipped_count += 1
                continue
            # Ignorer les erreurs "doesn't exist" (colonne n'existe pas)
            elif "doesn't exist" in error_msg.lower() or "Unknown column" in error_msg:
                print(f"⏭️  Colonne inexistante (ignoré)")
                skipped_count += 1
                continue
            else:
                print(f"⚠️  Erreur: {error_msg}")
                print(f"   Instruction: {statement[:100]}...")
                error_count += 1
    
    cursor.close()
    connection.close()
    
    print(f"\n✅ Script terminé!")
    print(f"   ✅ {success_count} index créés avec succès")
    if skipped_count > 0:
        print(f"   ⏭️  {skipped_count} index déjà existants (ignorés)")
    if error_count > 0:
        print(f"   ⚠️  {error_count} erreurs")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("   Assurez-vous d'être dans le répertoire du projet")
    sys.exit(1)
except pymysql.Error as e:
    print(f"❌ Erreur MySQL: {e}")
    print(f"   Vérifiez vos paramètres de connexion dans config.py ou .env")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

