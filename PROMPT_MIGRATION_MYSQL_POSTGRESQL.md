# PROMPT POUR CRÉER UN SYSTÈME DE MIGRATION AUTOMATIQUE MySQL → PostgreSQL

## Contexte
Je possède une application Flask qui utilise actuellement MySQL mais doit être compatible avec PostgreSQL (notamment pour le déploiement sur Render). Mon code contient des requêtes SQL spécifiques à MySQL qui doivent être automatiquement adaptées à PostgreSQL.

## Objectif
Créer un système de migration automatique qui :
1. **Détecte automatiquement** le type de base de données (MySQL ou PostgreSQL)
2. **Adapte les requêtes SQL** en temps réel selon la base de données utilisée
3. **Fonctionne de manière transparente** sans modifier la logique métier
4. **S'adapte automatiquement** aux futures mises à jour du code

## Exigences techniques

### 1. Détection automatique de la base de données
- Détecter si on utilise MySQL (`mysql+pymysql://`) ou PostgreSQL (`postgresql://` ou `postgresql+psycopg2://`)
- Utiliser l'URI de connexion SQLAlchemy pour la détection
- Fonction réutilisable dans tout le projet

### 2. Conversion des requêtes SQL courantes

#### A. Vérification d'existence de colonnes
**MySQL :**
```sql
SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'table_name' 
AND COLUMN_NAME = 'column_name'
```

**PostgreSQL :**
```sql
SELECT COUNT(*) FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'table_name' 
AND column_name = 'column_name'
```

#### B. Types de données
- `TINYINT(1)` → `BOOLEAN` ou `SMALLINT`
- `DATETIME` → `TIMESTAMP`
- `TEXT` → `TEXT` (identique)
- `VARCHAR(n)` → `VARCHAR(n)` (identique)
- `INT AUTO_INCREMENT` → `SERIAL` ou `BIGSERIAL`
- `BIGINT UNSIGNED` → `BIGINT`
- `JSON` → `JSONB` (recommandé pour PostgreSQL)

#### C. Fonctions SQL
- `DATABASE()` → `current_database()` ou `current_schema()`
- `NOW()` → `NOW()` (identique)
- `DATE_FORMAT()` → `TO_CHAR()`
- `IFNULL()` → `COALESCE()`
- `LIMIT n OFFSET m` → `LIMIT n OFFSET m` (identique)

#### D. Syntaxe des requêtes
- `SHOW COLUMNS FROM table` → `SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'table'`
- `DESCRIBE table` → `\d table` (psql) ou requête information_schema
- `AUTO_INCREMENT` → `SERIAL` ou `GENERATED ALWAYS AS IDENTITY`

### 3. Architecture proposée

#### A. Module utilitaire `db_adapter.py`
Créer un module qui contient :
- Fonction `get_db_type()` : détecte MySQL ou PostgreSQL
- Fonction `adapt_sql_query(sql_query, params=None)` : adapte une requête SQL
- Fonction `check_column_exists(table_name, column_name)` : vérifie l'existence d'une colonne (compatible)
- Fonction `check_table_exists(table_name)` : vérifie l'existence d'une table (compatible)
- Fonction `get_table_columns(table_name)` : liste les colonnes d'une table (compatible)

#### B. Décorateur pour les routes Flask
Créer un décorateur qui intercepte les requêtes SQL et les adapte automatiquement :
```python
@db_aware
def my_route():
    # Code normal, les requêtes SQL sont adaptées automatiquement
    pass
```

#### C. Middleware SQLAlchemy
Créer un event listener SQLAlchemy qui intercepte les requêtes SQL avant exécution et les adapte :
```python
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if is_postgresql():
        statement = adapt_sql_for_postgresql(statement)
```

### 4. Gestion des migrations de schéma

#### A. Script de migration initiale
Créer un script qui :
- Lit les fichiers SQL MySQL existants
- Les convertit en PostgreSQL
- Génère des fichiers SQL PostgreSQL équivalents
- Crée un mapping des conversions effectuées

#### B. Système de migration incrémentale
Créer un système qui :
- Détecte les nouvelles requêtes SQL dans le code
- Les adapte automatiquement lors de l'exécution
- Log les conversions effectuées pour le débogage

### 5. Exemples de conversions nécessaires

#### Exemple 1 : Vérification de colonne
```python
# Avant (MySQL uniquement)
check_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_SCHEMA = DATABASE() 
               AND TABLE_NAME = 'users' 
               AND COLUMN_NAME = 'email'"""
result = db.session.execute(text(check_sql)).scalar() > 0

# Après (compatible)
result = check_column_exists('users', 'email')
```

#### Exemple 2 : Création de table
```python
# Avant (MySQL)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

# Après (PostgreSQL)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Exemple 3 : Requête avec fonctions
```python
# Avant (MySQL)
SELECT IFNULL(quantity, 0) FROM stock WHERE id = 1;

# Après (PostgreSQL)
SELECT COALESCE(quantity, 0) FROM stock WHERE id = 1;
```

### 6. Tests et validation

Créer des tests qui :
- Vérifient que les requêtes fonctionnent sur MySQL
- Vérifient que les requêtes fonctionnent sur PostgreSQL
- Vérifient que les résultats sont identiques
- Testent les cas limites (colonnes manquantes, tables inexistantes, etc.)

### 7. Documentation

Créer une documentation qui :
- Liste toutes les conversions effectuées
- Explique comment utiliser le système
- Fournit des exemples d'utilisation
- Documente les limitations éventuelles

## Structure de fichiers proposée

```
project/
├── utils/
│   ├── db_adapter.py          # Module principal d'adaptation
│   ├── sql_converter.py       # Convertisseur SQL MySQL → PostgreSQL
│   └── db_detector.py         # Détecteur de type de base de données
├── migrations/
│   ├── mysql/                 # Scripts SQL MySQL originaux
│   ├── postgresql/            # Scripts SQL PostgreSQL convertis
│   └── converter.py           # Script de conversion batch
├── tests/
│   ├── test_db_adapter.py     # Tests du module d'adaptation
│   └── test_sql_conversion.py  # Tests de conversion SQL
└── docs/
    └── MIGRATION_GUIDE.md     # Guide de migration
```

## Contraintes

1. **Rétrocompatibilité** : Le système doit fonctionner avec MySQL existant sans casser le code
2. **Performance** : Les conversions ne doivent pas impacter significativement les performances
3. **Maintenabilité** : Le code doit être facile à maintenir et à étendre
4. **Logging** : Toutes les conversions doivent être loggées pour le débogage
5. **Sécurité** : Les conversions ne doivent pas introduire de vulnérabilités SQL injection

## Livrables attendus

1. **Module `db_adapter.py`** complet avec toutes les fonctions nécessaires
2. **Script de conversion** pour les fichiers SQL existants
3. **Middleware SQLAlchemy** pour l'adaptation automatique
4. **Tests unitaires** complets
5. **Documentation** détaillée
6. **Exemples d'utilisation** dans le code existant

## Priorités

1. **Haute priorité** : Vérification d'existence de colonnes/tables
2. **Haute priorité** : Conversion des types de données dans les CREATE TABLE
3. **Moyenne priorité** : Conversion des fonctions SQL (IFNULL, DATE_FORMAT, etc.)
4. **Basse priorité** : Optimisations et cas avancés

---

**Note** : Ce système doit être extensible pour gérer de futures différences entre MySQL et PostgreSQL qui pourraient être découvertes au fil du temps.

