# 🚀 GUIDE D'EXÉCUTION - MIGRATION RH POSTGRESQL

**Date :** 2025-01-XX  
**Base de données :** PostgreSQL (en ligne)

---

## 📋 ÉTAPES D'EXÉCUTION

### Étape 1 : Vérifier la connexion PostgreSQL

Avant d'exécuter la migration, testez la connexion :

```bash
python3 test_connection_postgresql.py
```

**Résultat attendu :**
```
✅ Connexion réussie !
   Type de base: PostgreSQL
   URI: postgresql://user:***@host:port/database
```

---

### Étape 2 : Vérifier DATABASE_URL

Assurez-vous que `DATABASE_URL` est configurée :

#### Sur Render (Production)
- ✅ `DATABASE_URL` est automatiquement configurée
- Vérifiez dans : **Render Dashboard > Environment**

#### En Local
```bash
# Vérifier si DATABASE_URL est définie
echo $DATABASE_URL

# Si elle n'est pas définie, la définir :
export DATABASE_URL="postgresql://user:password@host:port/database"
```

---

### Étape 3 : Exécuter la migration

Une fois la connexion vérifiée :

```bash
python3 execute_migration_rh_postgresql.py
```

**Résultat attendu :**
```
🔄 Exécution de la migration RH sur PostgreSQL...
   Base de données: host:port/database

✅ Migration exécutée avec succès!

📊 Tables créées:
   - user_activity_logs
   - employees
   - employee_contracts
   - employee_trainings
   - employee_evaluations
   - employee_absences

✅ X commande(s) exécutée(s)
```

---

### Étape 4 : Vérifier les tables créées

Vérifiez que les tables ont bien été créées :

```bash
# Option 1 : Via le script Python
python3 -c "
from app import app
from models import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    rh_tables = [t for t in tables if 'employee' in t or 'activity' in t]
    print('Tables RH créées:')
    for t in rh_tables:
        print(f'  ✅ {t}')
"
```

**Résultat attendu :**
```
Tables RH créées:
  ✅ user_activity_logs
  ✅ employees
  ✅ employee_contracts
  ✅ employee_trainings
  ✅ employee_evaluations
  ✅ employee_absences
```

---

## 🔍 VÉRIFICATION DÉTAILLÉE

### Vérifier la structure d'une table

```python
from app import app
from models import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('employees')
    print('Colonnes de la table employees:')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
```

---

## ⚠️ GESTION DES ERREURS

### Erreur : "Can't connect to PostgreSQL"

**Solutions :**
1. Vérifiez que `DATABASE_URL` est correcte
2. Vérifiez que PostgreSQL est accessible
3. Vérifiez les identifiants

### Erreur : "relation already exists"

**C'est normal !** Les tables existent déjà. Le script utilise `CREATE TABLE IF NOT EXISTS`.

### Erreur : "type already exists"

**C'est normal !** Les types ENUM existent déjà.

### Erreur : "permission denied"

**Solution :**
```sql
-- Se connecter en tant qu'administrateur PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE database_name TO user_name;
```

---

## 🎯 EXÉCUTION SUR RENDER

### Méthode 1 : Via le Shell Render

1. Allez sur **Render Dashboard**
2. Sélectionnez votre service
3. Cliquez sur **Shell**
4. Exécutez :
```bash
python3 execute_migration_rh_postgresql.py
```

### Méthode 2 : Via le Build Command

Ajoutez dans votre `render.yaml` ou dans les paramètres du service :

```yaml
buildCommand: |
  pip install -r requirements.txt
  python3 execute_migration_rh_postgresql.py
```

### Méthode 3 : Via un Script de Déploiement

Créez un script `deploy.sh` :

```bash
#!/bin/bash
# Exécuter la migration au démarrage
python3 execute_migration_rh_postgresql.py
# Démarrer l'application
gunicorn app:app
```

---

## ✅ CHECKLIST FINALE

Avant de considérer la migration comme terminée :

- [ ] Connexion PostgreSQL testée et fonctionnelle
- [ ] Migration exécutée sans erreur critique
- [ ] 6 tables RH créées et vérifiées
- [ ] Application Flask redémarrée
- [ ] Test d'accès aux fonctionnalités RH

---

## 🧪 TEST POST-MIGRATION

Après la migration, testez les fonctionnalités :

1. **Créer un utilisateur RH** :
   - Connectez-vous en tant qu'admin
   - Allez dans `/rh/personnel/new`
   - Créez un utilisateur avec un rôle RH

2. **Tester la gestion des employés** :
   - Allez dans `/rh/employees`
   - Créez un nouvel employé
   - Vérifiez que les données sont sauvegardées

3. **Tester les autres modules** :
   - Contrats
   - Formations
   - Évaluations
   - Absences

---

## 🆘 SUPPORT

Si vous rencontrez des problèmes :

1. **Vérifiez les logs** :
   ```bash
   # Logs Render
   render logs
   ```

2. **Vérifiez la connexion** :
   ```bash
   python3 test_connection_postgresql.py
   ```

3. **Vérifiez les tables** :
   ```python
   from app import app
   from models import db
   with app.app_context():
       print(db.engine.table_names())
   ```

---

**Prêt à exécuter ! 🚀**

