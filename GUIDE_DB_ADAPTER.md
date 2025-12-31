# Guide d'utilisation du module db_adapter

## Vue d'ensemble

Le module `utils/db_adapter.py` fournit un système d'adaptation automatique pour rendre votre application Flask compatible avec MySQL et PostgreSQL. Il détecte automatiquement le type de base de données et adapte les requêtes SQL en conséquence.

## Fonctionnalités

### 1. Détection automatique de la base de données

```python
from utils.db_adapter import get_db_type, is_postgresql, is_mysql

# Détecter le type de base de données
db_type = get_db_type(db.session)  # 'mysql', 'postgresql', ou 'unknown'

# Vérifications rapides
if is_postgresql(db.session):
    print("Utilisation de PostgreSQL")
elif is_mysql(db.session):
    print("Utilisation de MySQL")
```

### 2. Vérification d'existence de colonnes (compatible)

```python
from utils.db_adapter import check_column_exists

# Vérifier si une colonne existe (fonctionne sur MySQL et PostgreSQL)
exists = check_column_exists('users', 'email', db.session)
if exists:
    print("La colonne email existe")
```

**Avant (MySQL uniquement) :**
```python
check_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_SCHEMA = DATABASE() 
               AND TABLE_NAME = 'users' 
               AND COLUMN_NAME = 'email'"""
result = db.session.execute(text(check_sql)).scalar() > 0
```

**Après (compatible) :**
```python
result = check_column_exists('users', 'email', db.session)
```

### 3. Vérification d'existence de tables

```python
from utils.db_adapter import check_table_exists

# Vérifier si une table existe
exists = check_table_exists('users', db.session)
```

### 4. Liste des colonnes d'une table

```python
from utils.db_adapter import get_table_columns

# Obtenir la liste des colonnes
columns = get_table_columns('users', db.session)
print(columns)  # ['id', 'username', 'email', ...]
```

### 5. Adaptation automatique de requêtes SQL

```python
from utils.db_adapter import adapt_sql_query

# Adapter une requête SQL (automatique selon la base de données)
mysql_query = """
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users'
"""
adapted = adapt_sql_query(mysql_query, db.session)
# Sur PostgreSQL, devient automatiquement:
# SELECT COUNT(*) FROM information_schema.columns 
# WHERE table_schema = 'public' 
# AND table_name = 'users'
```

## Conversions automatiques

Le système convertit automatiquement :

| MySQL | PostgreSQL |
|-------|------------|
| `INFORMATION_SCHEMA.COLUMNS` avec `TABLE_SCHEMA = DATABASE()` | `information_schema.columns` avec `table_schema = 'public'` |
| `IFNULL(expr, default)` | `COALESCE(expr, default)` |
| `DATE_FORMAT(date, format)` | `TO_CHAR(date, format)` (basique) |
| `TINYINT(1)` | `BOOLEAN` ou `SMALLINT` |
| `DATETIME` | `TIMESTAMP` |
| `INT AUTO_INCREMENT` | `SERIAL` |
| `BIGINT UNSIGNED` | `BIGINT` |

## Middleware SQLAlchemy

Le middleware est automatiquement configuré dans `app.py` et intercepte toutes les requêtes SQL avant leur exécution pour les adapter si nécessaire.

**Aucune action requise de votre part** - cela fonctionne automatiquement !

## Exemples d'utilisation

### Exemple 1 : Vérifier une colonne avant de l'utiliser

```python
from utils.db_adapter import check_column_exists

def my_function():
    # Vérifier si la colonne transaction_type existe
    if check_column_exists('promotion_sales', 'transaction_type', db.session):
        # Utiliser la colonne
        query = db.session.query(PromotionSale).filter(
            PromotionSale.transaction_type == 'enlevement'
        )
    else:
        # Fallback sans la colonne
        query = db.session.query(PromotionSale)
    
    return query.all()
```

### Exemple 2 : Adapter une requête manuelle

```python
from utils.db_adapter import adapt_sql_query, is_postgresql

def get_custom_data():
    sql = """
        SELECT IFNULL(quantity, 0) as qty 
        FROM stock 
        WHERE id = :id
    """
    
    # Adapter la requête si nécessaire
    adapted_sql = adapt_sql_query(sql, db.session)
    
    result = db.session.execute(text(adapted_sql), {'id': 1})
    return result.fetchone()
```

### Exemple 3 : Créer une table compatible

```python
from utils.db_adapter import is_postgresql

def create_table():
    if is_postgresql(db.session):
        # PostgreSQL
        sql = """
            CREATE TABLE IF NOT EXISTS my_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        # MySQL
        sql = """
            CREATE TABLE IF NOT EXISTS my_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
    
    db.session.execute(text(sql))
    db.session.commit()
```

## Cache

Les vérifications d'existence de colonnes et de tables sont mises en cache pendant 1 heure pour améliorer les performances. Vous pouvez vider le cache manuellement :

```python
from utils.db_adapter import clear_cache

clear_cache()  # Vide tout le cache
```

## Informations sur la base de données

```python
from utils.db_adapter import get_db_info

info = get_db_info(db.session)
print(info)
# {
#     'type': 'postgresql',
#     'is_postgresql': True,
#     'is_mysql': False,
#     'is_unknown': False
# }
```

## Migration depuis le code existant

### Étape 1 : Remplacer les vérifications de colonnes

**Avant :**
```python
check_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_SCHEMA = DATABASE() 
               AND TABLE_NAME = 'table' 
               AND COLUMN_NAME = 'column'"""
has_column = db.session.execute(text(check_sql)).scalar() > 0
```

**Après :**
```python
from utils.db_adapter import check_column_exists
has_column = check_column_exists('table', 'column', db.session)
```

### Étape 2 : Utiliser les fonctions compatibles

Remplacez toutes les occurrences de :
- `INFORMATION_SCHEMA.COLUMNS` avec `DATABASE()` → `check_column_exists()`
- `INFORMATION_SCHEMA.TABLES` avec `DATABASE()` → `check_table_exists()`
- `SHOW COLUMNS FROM table` → `get_table_columns()`

### Étape 3 : Adapter les requêtes manuelles

Pour les requêtes SQL écrites manuellement, utilisez `adapt_sql_query()` ou laissez le middleware les adapter automatiquement.

## Tests

Exécutez les tests pour vérifier que tout fonctionne :

```bash
python3 utils/test_db_adapter.py
```

## Dépannage

### Le middleware ne fonctionne pas

Vérifiez que le middleware est bien initialisé dans `app.py` :
```python
from utils.db_adapter import setup_sqlalchemy_middleware
setup_sqlalchemy_middleware(db.engine)
```

### Les conversions ne fonctionnent pas

Le middleware intercepte uniquement les requêtes SQL exécutées via SQLAlchemy. Pour les requêtes écrites manuellement avec `text()`, utilisez `adapt_sql_query()`.

### Cache obsolète

Si vous avez modifié le schéma de la base de données, videz le cache :
```python
from utils.db_adapter import clear_cache
clear_cache()
```

## Limitations

1. **Conversions basiques** : Certaines conversions (comme `DATE_FORMAT`) sont basiques et peuvent nécessiter des ajustements manuels pour des cas complexes.

2. **Requêtes complexes** : Les requêtes SQL très complexes peuvent nécessiter une adaptation manuelle.

3. **Types de données** : Les conversions de types de données dans les CREATE TABLE doivent être faites manuellement dans les scripts de migration.

## Support

Pour toute question ou problème, consultez :
- Le code source : `utils/db_adapter.py`
- Les tests : `utils/test_db_adapter.py`
- Ce guide : `GUIDE_DB_ADAPTER.md`

