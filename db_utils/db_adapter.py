#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'adaptation automatique MySQL → PostgreSQL
Détecte le type de base de données et adapte les requêtes SQL en conséquence
"""

import re
import logging
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.event import listens_for

# Configuration du logging
logger = logging.getLogger(__name__)

# Cache pour les vérifications (durée: 1 heure)
_column_cache = {}
_table_cache = {}
_cache_timestamps = {}

# =========================================================
# DÉTECTION DU TYPE DE BASE DE DONNÉES
# =========================================================

def get_db_type(db_session=None):
    """
    Détecte le type de base de données (MySQL ou PostgreSQL)
    
    Args:
        db_session: Session SQLAlchemy (optionnel)
    
    Returns:
        str: 'mysql', 'postgresql', ou 'unknown'
    """
    try:
        # Essayer d'obtenir l'URI depuis la session
        if db_session:
            uri = str(db_session.bind.url) if hasattr(db_session, 'bind') else None
        else:
            # Essayer d'importer depuis app
            try:
                from app import app
                uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            except:
                try:
                    from config import SQLALCHEMY_DATABASE_URI
                    uri = SQLALCHEMY_DATABASE_URI
                except:
                    return 'unknown'
        
        if not uri:
            return 'unknown'
        
        uri_lower = uri.lower()
        if uri_lower.startswith('mysql') or uri_lower.startswith('mariadb'):
            return 'mysql'
        elif uri_lower.startswith('postgresql'):
            return 'postgresql'
        else:
            return 'unknown'
    except Exception as e:
        logger.error(f"Erreur lors de la détection du type de base de données: {e}")
        return 'unknown'


def is_postgresql(db_session=None):
    """
    Vérifie si on utilise PostgreSQL
    
    Args:
        db_session: Session SQLAlchemy (optionnel)
    
    Returns:
        bool: True si PostgreSQL, False sinon
    """
    return get_db_type(db_session) == 'postgresql'


def is_mysql(db_session=None):
    """
    Vérifie si on utilise MySQL
    
    Args:
        db_session: Session SQLAlchemy (optionnel)
    
    Returns:
        bool: True si MySQL, False sinon
    """
    return get_db_type(db_session) == 'mysql'


# =========================================================
# VÉRIFICATION D'EXISTENCE (COMPATIBLE)
# =========================================================

def check_column_exists(table_name, column_name, db_session=None, use_cache=True):
    """
    Vérifie si une colonne existe dans une table (compatible MySQL et PostgreSQL)
    
    Args:
        table_name: Nom de la table
        column_name: Nom de la colonne
        db_session: Session SQLAlchemy (optionnel)
        use_cache: Utiliser le cache (défaut: True)
    
    Returns:
        bool: True si la colonne existe, False sinon
    """
    cache_key = f"{table_name}.{column_name}"
    
    # Vérifier le cache (valide pendant 1 heure)
    if use_cache and cache_key in _column_cache:
        import time
        if time.time() - _cache_timestamps.get(cache_key, 0) < 3600:
            return _column_cache[cache_key]
    
        if not db_session:
            try:
                from app import app, db
                db_session = db.session
            except:
                try:
                    from models import db
                    db_session = db.session
                except:
                    logger.error("Impossible d'obtenir la session de base de données")
                    return False
    
    try:
        db_type = get_db_type(db_session)
        
        if db_type == 'postgresql':
            # Syntaxe PostgreSQL
            check_sql = text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name 
                AND column_name = :column_name
            """)
        elif db_type == 'mysql':
            # Syntaxe MySQL
            check_sql = text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = :table_name 
                AND COLUMN_NAME = :column_name
            """)
        else:
            logger.warning(f"Type de base de données inconnu: {db_type}")
            return False
        
        result = db_session.execute(check_sql, {
            'table_name': table_name,
            'column_name': column_name
        }).scalar() > 0
        
        # Mettre en cache
        if use_cache:
            _column_cache[cache_key] = result
            import time
            _cache_timestamps[cache_key] = time.time()
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la colonne {column_name} dans {table_name}: {e}")
        return False


def check_table_exists(table_name, db_session=None, use_cache=True):
    """
    Vérifie si une table existe (compatible MySQL et PostgreSQL)
    
    Args:
        table_name: Nom de la table
        db_session: Session SQLAlchemy (optionnel)
        use_cache: Utiliser le cache (défaut: True)
    
    Returns:
        bool: True si la table existe, False sinon
    """
    cache_key = f"table.{table_name}"
    
    # Vérifier le cache
    if use_cache and cache_key in _table_cache:
        import time
        if time.time() - _cache_timestamps.get(cache_key, 0) < 3600:
            return _table_cache[cache_key]
    
        if not db_session:
            try:
                from app import app, db
                db_session = db.session
            except:
                try:
                    from models import db
                    db_session = db.session
                except:
                    logger.error("Impossible d'obtenir la session de base de données")
                    return False
    
    try:
        db_type = get_db_type(db_session)
        
        if db_type == 'postgresql':
            check_sql = text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            """)
        elif db_type == 'mysql':
            check_sql = text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = :table_name
            """)
        else:
            logger.warning(f"Type de base de données inconnu: {db_type}")
            return False
        
        result = db_session.execute(check_sql, {
            'table_name': table_name
        }).scalar() > 0
        
        # Mettre en cache
        if use_cache:
            _table_cache[cache_key] = result
            import time
            _cache_timestamps[cache_key] = time.time()
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la table {table_name}: {e}")
        return False


def get_table_columns(table_name, db_session=None):
    """
    Liste les colonnes d'une table (compatible MySQL et PostgreSQL)
    
    Args:
        table_name: Nom de la table
        db_session: Session SQLAlchemy (optionnel)
    
    Returns:
        list: Liste des noms de colonnes
    """
    if not db_session:
        try:
            from app import app, db
            db_session = db.session
        except:
            logger.error("Impossible d'obtenir la session de base de données")
            return []
    
    try:
        db_type = get_db_type(db_session)
        
        if db_type == 'postgresql':
            query_sql = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
                ORDER BY ordinal_position
            """)
        elif db_type == 'mysql':
            query_sql = text("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """)
        else:
            logger.warning(f"Type de base de données inconnu: {db_type}")
            return []
        
        result = db_session.execute(query_sql, {'table_name': table_name})
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des colonnes de {table_name}: {e}")
        return []


# =========================================================
# CONVERSION DE REQUÊTES SQL
# =========================================================

def adapt_sql_query(sql_query, db_session=None):
    """
    Adapte une requête SQL MySQL vers PostgreSQL si nécessaire
    
    Args:
        sql_query: Requête SQL à adapter
        db_session: Session SQLAlchemy (optionnel)
    
    Returns:
        str: Requête SQL adaptée
    """
    if not is_postgresql(db_session):
        return sql_query
    
    adapted = sql_query
    
    # Conversion INFORMATION_SCHEMA.COLUMNS avec DATABASE()
    # MySQL: TABLE_SCHEMA = DATABASE()
    # PostgreSQL: table_schema = 'public'
    pattern1 = re.compile(
        r'INFORMATION_SCHEMA\.COLUMNS\s+WHERE\s+TABLE_SCHEMA\s*=\s*DATABASE\(\)',
        re.IGNORECASE
    )
    adapted = pattern1.sub(
        "information_schema.columns WHERE table_schema = 'public'",
        adapted
    )
    
    # Conversion TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME en minuscules
    adapted = re.sub(r'\bTABLE_SCHEMA\b', 'table_schema', adapted, flags=re.IGNORECASE)
    adapted = re.sub(r'\bTABLE_NAME\b', 'table_name', adapted, flags=re.IGNORECASE)
    adapted = re.sub(r'\bCOLUMN_NAME\b', 'column_name', adapted, flags=re.IGNORECASE)
    
    # Conversion IFNULL() → COALESCE()
    adapted = re.sub(r'\bIFNULL\s*\(', 'COALESCE(', adapted, flags=re.IGNORECASE)
    
    # Conversion DATE_FORMAT() → TO_CHAR() (basique)
    # Note: Cette conversion est basique, peut nécessiter des ajustements manuels
    date_format_pattern = re.compile(
        r'DATE_FORMAT\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
        re.IGNORECASE
    )
    def convert_date_format(match):
        expr = match.group(1)
        fmt = match.group(2).strip("'\"")
        # Conversion basique des formats courants
        fmt_map = {
            '%Y-%m-%d': 'YYYY-MM-DD',
            '%d/%m/%Y': 'DD/MM/YYYY',
            '%Y-%m-%d %H:%i:%s': 'YYYY-MM-DD HH24:MI:SS',
        }
        pg_fmt = fmt_map.get(fmt, fmt)
        return f"TO_CHAR({expr}, '{pg_fmt}')"
    
    adapted = date_format_pattern.sub(convert_date_format, adapted)
    
    # Log si une conversion a été effectuée
    if adapted != sql_query:
        logger.debug(f"Requête SQL adaptée:\nOriginal: {sql_query}\nAdapté: {adapted}")
    
    return adapted


# =========================================================
# MIDDLEWARE SQLALCHEMY (ADAPTATION AUTOMATIQUE)
# =========================================================

def setup_sqlalchemy_middleware(engine):
    """
    Configure le middleware SQLAlchemy pour adapter automatiquement les requêtes
    
    Args:
        engine: Moteur SQLAlchemy
    """
    @listens_for(engine, "before_cursor_execute", retval=True)
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """
        Intercepte les requêtes SQL avant exécution et les adapte si nécessaire
        """
        if is_postgresql():
            # Adapter la requête pour PostgreSQL
            adapted_statement = adapt_sql_query(statement)
            if adapted_statement != statement:
                logger.debug(f"Requête adaptée automatiquement: {statement[:100]}...")
                return adapted_statement, parameters
        return statement, parameters


# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================

def clear_cache():
    """Vide le cache des vérifications"""
    global _column_cache, _table_cache, _cache_timestamps
    _column_cache.clear()
    _table_cache.clear()
    _cache_timestamps.clear()
    logger.info("Cache des vérifications vidé")


def get_db_info(db_session=None):
    """
    Retourne des informations sur la base de données
    
    Args:
        db_session: Session SQLAlchemy (optionnel)
    
    Returns:
        dict: Informations sur la base de données
    """
    db_type = get_db_type(db_session)
    return {
        'type': db_type,
        'is_postgresql': db_type == 'postgresql',
        'is_mysql': db_type == 'mysql',
        'is_unknown': db_type == 'unknown'
    }

