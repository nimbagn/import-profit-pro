# PROMPT COURT POUR MIGRATION MySQL → PostgreSQL

## Prompt à copier-coller

```
Je possède une application Flask qui utilise MySQL mais doit être compatible avec PostgreSQL (pour déploiement sur Render).

Crée un système de migration automatique qui :

1. **Détecte automatiquement** le type de base de données (MySQL ou PostgreSQL) via l'URI SQLAlchemy

2. **Adapte les requêtes SQL en temps réel** pour les différences suivantes :
   - `INFORMATION_SCHEMA.COLUMNS` avec `TABLE_SCHEMA = DATABASE()` → `table_schema = 'public'` pour PostgreSQL
   - `TINYINT(1)` → `BOOLEAN` ou `SMALLINT`
   - `DATETIME` → `TIMESTAMP`
   - `INT AUTO_INCREMENT` → `SERIAL`
   - `BIGINT UNSIGNED` → `BIGINT`
   - `JSON` → `JSONB`
   - `IFNULL()` → `COALESCE()`
   - `DATE_FORMAT()` → `TO_CHAR()`
   - `SHOW COLUMNS FROM table` → requête `information_schema.columns`

3. **Crée un module `utils/db_adapter.py`** avec :
   - `get_db_type()` : détecte MySQL/PostgreSQL
   - `check_column_exists(table, column)` : vérifie colonne (compatible)
   - `check_table_exists(table)` : vérifie table (compatible)
   - `adapt_sql_query(sql, params)` : adapte requête SQL
   - `get_table_columns(table)` : liste colonnes (compatible)

4. **Crée un middleware SQLAlchemy** qui intercepte les requêtes SQL et les adapte automatiquement avant exécution

5. **Crée un script de conversion** pour les fichiers SQL existants (MySQL → PostgreSQL)

6. **Inclut des tests** pour vérifier la compatibilité sur les deux bases

7. **Documente** toutes les conversions et leur utilisation

Le système doit être :
- Rétrocompatible avec MySQL existant
- Automatique (pas de modification manuelle du code)
- Extensible pour futures différences
- Performant (pas d'impact significatif)
- Loggé pour débogage

Fournis le code complet, les tests, et la documentation.
```

## Version encore plus courte (pour ChatGPT/Claude)

```
Crée un système Python qui adapte automatiquement les requêtes SQL MySQL vers PostgreSQL pour une app Flask.

Fonctionnalités requises :
- Détection auto MySQL/PostgreSQL via SQLAlchemy URI
- Module `db_adapter.py` avec fonctions compatibles (check_column_exists, etc.)
- Middleware SQLAlchemy pour adaptation auto des requêtes
- Conversion des syntaxes : INFORMATION_SCHEMA, DATABASE(), TINYINT→BOOLEAN, AUTO_INCREMENT→SERIAL, etc.
- Script de conversion pour fichiers SQL
- Tests et documentation

Doit être rétrocompatible, automatique, extensible et performant.
```

## Version ultra-courte (pour requêtes rapides)

```
Système Python Flask : adapter automatiquement requêtes SQL MySQL→PostgreSQL. 
Détection auto, module db_adapter.py, middleware SQLAlchemy, conversion syntaxes, tests.
```

