# 🐘 GUIDE DE MIGRATION RH - PostgreSQL

**Date :** 2025-01-XX  
**Base de données :** PostgreSQL

---

## 📋 PRÉREQUIS

1. ✅ PostgreSQL installé et accessible
2. ✅ Variable d'environnement `DATABASE_URL` configurée
3. ✅ Application Flask configurée pour PostgreSQL

---

## 🔧 CONFIGURATION

### Option 1 : Utiliser DATABASE_URL (Recommandé)

Si vous utilisez Render ou un autre service cloud, la variable `DATABASE_URL` est généralement déjà configurée :

```bash
# Format PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/database
```

### Option 2 : Configurer manuellement

Si `DATABASE_URL` n'est pas définie, le script utilisera les variables individuelles :

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=madargn
export DB_USER=postgres
export DB_PASSWORD=votre_mot_de_passe
```

---

## 🚀 EXÉCUTION DE LA MIGRATION

### Méthode 1 : Script Python (Recommandé)

```bash
# S'assurer que DATABASE_URL est définie
export DATABASE_URL="postgresql://user:password@host:port/database"

# Exécuter le script
python3 execute_migration_rh_postgresql.py
```

### Méthode 2 : Exécution manuelle avec psql

```bash
# Se connecter à PostgreSQL
psql -h host -U user -d database

# Exécuter le script
\i migration_rh_complete_postgresql.sql
```

### Méthode 3 : Via SQLAlchemy dans Python

```python
from app import app
from models import db

with app.app_context():
    with open('migration_rh_complete_postgresql.sql', 'r') as f:
        sql = f.read()
    
    # Exécuter chaque commande
    for command in sql.split(';'):
        if command.strip():
            db.session.execute(db.text(command))
            db.session.commit()
```

---

## 📊 TABLES CRÉÉES

La migration crée les tables suivantes :

1. **user_activity_logs** - Journal des activités utilisateurs
2. **employees** - Employés externes
3. **employee_contracts** - Contrats des employés
4. **employee_trainings** - Formations des employés
5. **employee_evaluations** - Évaluations des employés
6. **employee_absences** - Absences des employés

---

## ✅ VÉRIFICATION

Après l'exécution, vérifiez que les tables existent :

```sql
-- Se connecter à PostgreSQL
psql -h host -U user -d database

-- Lister les tables RH
\dt *employee*
\dt *activity*

-- Vérifier la structure d'une table
\d employees
```

---

## 🔍 DIFFÉRENCES POSTGRESQL vs MYSQL

### Types de données
- **MySQL** : `BIGINT UNSIGNED AUTO_INCREMENT`
- **PostgreSQL** : `BIGSERIAL` (équivalent)

### ENUM
- **MySQL** : `ENUM('value1', 'value2')`
- **PostgreSQL** : `CREATE TYPE ... AS ENUM(...)`

### JSON
- **MySQL** : `JSON`
- **PostgreSQL** : `JSONB` (recommandé pour de meilleures performances)

### Index
- **MySQL** : `INDEX idx_name (column)`
- **PostgreSQL** : `CREATE INDEX idx_name ON table (column)`

### Commentaires
- **MySQL** : `COMMENT = 'description'`
- **PostgreSQL** : `COMMENT ON TABLE table IS 'description'`

---

## ⚠️ ERREURS COURANTES

### Erreur : "relation already exists"
**Solution :** C'est normal si les tables existent déjà. Le script utilise `CREATE TABLE IF NOT EXISTS`.

### Erreur : "type already exists"
**Solution :** Les types ENUM existent déjà. C'est normal.

### Erreur : "permission denied"
**Solution :** Vérifiez que l'utilisateur PostgreSQL a les droits nécessaires :
```sql
GRANT ALL PRIVILEGES ON DATABASE database_name TO user_name;
```

---

## 🎯 PROCHAINES ÉTAPES

Après la migration réussie :

1. ✅ **Redémarrer l'application Flask**
2. ✅ **Créer un utilisateur avec un rôle RH** (via l'interface ou directement en base)
3. ✅ **Tester les fonctionnalités RH** :
   - Liste du personnel
   - Gestion des employés externes
   - Contrats, formations, évaluations, absences

---

## 📝 NOTES IMPORTANTES

- ✅ Le script est **idempotent** : il peut être exécuté plusieurs fois sans problème
- ✅ Les tables existantes ne seront **pas écrasées**
- ✅ Les données existantes seront **préservées**
- ✅ Les index et contraintes seront créés automatiquement

---

## 🆘 SUPPORT

Si vous rencontrez des problèmes :

1. Vérifiez les logs d'erreur
2. Vérifiez la connexion à PostgreSQL
3. Vérifiez les permissions de l'utilisateur
4. Consultez la documentation PostgreSQL

---

**Migration prête pour PostgreSQL ! 🐘✅**

