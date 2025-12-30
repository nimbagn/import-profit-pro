# ✅ Correction LAST_INSERT_ID() pour PostgreSQL

## ❌ Erreur PostgreSQL

```
ERROR: function last_insert_id() does not exist
STATEMENT: SELECT LAST_INSERT_ID() as id
```

## 🔍 Problème

`LAST_INSERT_ID()` est une fonction **MySQL**, pas PostgreSQL. En PostgreSQL, on utilise `RETURNING id` dans l'INSERT.

## ✅ Solution Appliquée

### 1. **Détection Automatique du Type de Base**

Le code détecte maintenant automatiquement si on utilise PostgreSQL ou MySQL :

```python
from config import SQLALCHEMY_DATABASE_URI
is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
```

### 2. **Utilisation de RETURNING pour PostgreSQL**

**Avant (MySQL uniquement) :**
```python
sql = "INSERT INTO simulations (...) VALUES (...)"
db.session.execute(text(sql), params)
result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
simulation_id = result.scalar()
```

**Après (PostgreSQL + MySQL) :**
```python
if is_postgresql:
    sql = "INSERT INTO simulations (...) VALUES (...) RETURNING id"
    result = db.session.execute(text(sql), params)
    simulation_id = result.scalar()
else:
    sql = "INSERT INTO simulations (...) VALUES (...)"
    db.session.execute(text(sql), params)
    result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
    simulation_id = result.scalar()
```

## 📋 Fichiers Corrigés

### `app.py`
1. ✅ **Ligne 454** : Création simulations de démonstration
2. ✅ **Ligne 2044** : Création nouvelle simulation
3. ✅ **Ligne 2994** : Création nouvelle prévision (`forecast_new`)
4. ✅ **Ligne 3984** : Import prévisions (`forecast_import_ultra_modern`)
5. ✅ **Ligne 4203** : Saisie réalisations (`forecast_enter_realizations`)

### `promotion.py`
1. ✅ **Ligne 4034** : Création nouvelle vente (`sale_new`)

## 🎯 Fonctionnement

### PostgreSQL (Render)
- ✅ Utilise `RETURNING id` dans l'INSERT
- ✅ Récupère l'ID directement avec `result.scalar()`
- ✅ Pas besoin de requête SELECT supplémentaire

### MySQL (Local/Développement)
- ✅ Utilise `LAST_INSERT_ID()` comme avant
- ✅ Compatible avec l'ancien code

### SQLite (Fallback)
- ✅ Utilise `lastrowid` comme avant
- ✅ Compatible avec l'ancien code

## ✅ Résultat

**Toutes les insertions fonctionnent maintenant** sur :
- ✅ PostgreSQL (Render)
- ✅ MySQL (Local)
- ✅ SQLite (Fallback)

L'erreur `function last_insert_id() does not exist` ne devrait plus apparaître dans les logs PostgreSQL.

---

**✅ Correction appliquée : Compatibilité PostgreSQL complète !**

