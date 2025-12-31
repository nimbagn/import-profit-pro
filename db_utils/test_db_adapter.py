#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour le module db_adapter
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from db_utils.db_adapter import (
    get_db_type,
    is_postgresql,
    is_mysql,
    check_column_exists,
    check_table_exists,
    get_table_columns,
    adapt_sql_query,
    get_db_info
)

def test_db_detection():
    """Test de détection du type de base de données"""
    print("\n=== Test de détection de base de données ===")
    
    with app.app_context():
        db_type = get_db_type(db.session)
        db_info = get_db_info(db.session)
        
        print(f"Type détecté: {db_type}")
        print(f"Informations: {db_info}")
        
        assert db_type in ['mysql', 'postgresql', 'unknown'], f"Type inattendu: {db_type}"
        print("✅ Test de détection réussi")


def test_check_column_exists():
    """Test de vérification d'existence de colonne"""
    print("\n=== Test de vérification de colonne ===")
    
    with app.app_context():
        # Test avec une colonne qui existe probablement
        exists = check_column_exists('users', 'id', db.session)
        print(f"Colonne 'users.id' existe: {exists}")
        
        # Test avec une colonne qui n'existe probablement pas
        not_exists = check_column_exists('users', 'nonexistent_column_xyz', db.session)
        print(f"Colonne 'users.nonexistent_column_xyz' existe: {not_exists}")
        
        assert isinstance(exists, bool), "check_column_exists doit retourner un booléen"
        assert isinstance(not_exists, bool), "check_column_exists doit retourner un booléen"
        print("✅ Test de vérification de colonne réussi")


def test_check_table_exists():
    """Test de vérification d'existence de table"""
    print("\n=== Test de vérification de table ===")
    
    with app.app_context():
        # Test avec une table qui existe probablement
        exists = check_table_exists('users', db.session)
        print(f"Table 'users' existe: {exists}")
        
        # Test avec une table qui n'existe probablement pas
        not_exists = check_table_exists('nonexistent_table_xyz', db.session)
        print(f"Table 'nonexistent_table_xyz' existe: {not_exists}")
        
        assert isinstance(exists, bool), "check_table_exists doit retourner un booléen"
        assert isinstance(not_exists, bool), "check_table_exists doit retourner un booléen"
        print("✅ Test de vérification de table réussi")


def test_get_table_columns():
    """Test de récupération des colonnes d'une table"""
    print("\n=== Test de récupération des colonnes ===")
    
    with app.app_context():
        columns = get_table_columns('users', db.session)
        print(f"Colonnes de 'users': {columns}")
        
        assert isinstance(columns, list), "get_table_columns doit retourner une liste"
        if columns:
            assert 'id' in columns or 'ID' in columns, "La colonne 'id' devrait exister"
        print("✅ Test de récupération des colonnes réussi")


def test_adapt_sql_query():
    """Test d'adaptation de requête SQL"""
    print("\n=== Test d'adaptation de requête SQL ===")
    
    # Test avec une requête MySQL typique
    mysql_query = """
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'email'
    """
    
    with app.app_context():
        adapted = adapt_sql_query(mysql_query, db.session)
        print(f"Requête originale:\n{mysql_query}")
        print(f"\nRequête adaptée:\n{adapted}")
        
        if is_postgresql(db.session):
            assert 'information_schema.columns' in adapted.lower(), "Doit contenir information_schema.columns"
            assert "table_schema = 'public'" in adapted.lower(), "Doit contenir table_schema = 'public'"
        else:
            # Sur MySQL, la requête ne devrait pas être modifiée
            assert mysql_query.strip() == adapted.strip(), "Sur MySQL, la requête ne devrait pas être modifiée"
        
        print("✅ Test d'adaptation de requête SQL réussi")


def test_ifnull_conversion():
    """Test de conversion IFNULL → COALESCE"""
    print("\n=== Test de conversion IFNULL ===")
    
    mysql_query = "SELECT IFNULL(quantity, 0) FROM stock WHERE id = 1"
    
    with app.app_context():
        adapted = adapt_sql_query(mysql_query, db.session)
        print(f"Requête originale: {mysql_query}")
        print(f"Requête adaptée: {adapted}")
        
        if is_postgresql(db.session):
            assert 'COALESCE' in adapted.upper(), "IFNULL doit être converti en COALESCE sur PostgreSQL"
            assert 'IFNULL' not in adapted.upper(), "IFNULL ne doit plus être présent"
        else:
            assert 'IFNULL' in adapted.upper(), "Sur MySQL, IFNULL doit rester"
        
        print("✅ Test de conversion IFNULL réussi")


def run_all_tests():
    """Exécute tous les tests"""
    print("=" * 70)
    print("TESTS DU MODULE DB_ADAPTER")
    print("=" * 70)
    
    try:
        test_db_detection()
        test_check_column_exists()
        test_check_table_exists()
        test_get_table_columns()
        test_adapt_sql_query()
        test_ifnull_conversion()
        
        print("\n" + "=" * 70)
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("=" * 70)
        return True
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

