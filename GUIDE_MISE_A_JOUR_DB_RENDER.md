# 🚀 Guide : Mettre à Jour la Base de Données PostgreSQL sur Render

**Date :** 2025-01-XX  
**Base de données :** PostgreSQL (Render)

---

## 📋 Vue d'Ensemble

Ce guide vous explique **3 méthodes** pour mettre à jour votre base de données PostgreSQL en ligne sur Render :

1. ✅ **Via le Shell Render** (Recommandé - le plus simple)
2. ✅ **Via un script de migration Python**
3. ✅ **Via un fichier SQL direct**

---

## 🎯 MÉTHODE 1 : Via le Shell Render (Recommandé)

### Étape 1 : Accéder au Shell Render

1. Allez sur [Render Dashboard](https://dashboard.render.com)
2. Connectez-vous à votre compte
3. Sélectionnez votre **service Web** (celui qui héberge votre application Flask)
4. Dans le menu de gauche, cliquez sur **"Shell"**
5. Un terminal s'ouvre dans votre navigateur

---

### Étape 2 : Vérifier la Connexion PostgreSQL

Dans le Shell Render, testez d'abord la connexion :

```bash
python3 test_connection_postgresql.py
```

**Résultat attendu :**
```
✅ Connexion réussie !
   Type de base: PostgreSQL
   URI: postgresql://user:***@host:port/database
```

Si vous obtenez une erreur, vérifiez que :
- La variable `DATABASE_URL` est bien configurée dans Render Dashboard > Environment
- La base de données PostgreSQL est active

---

### Étape 3 : Exécuter la Migration

Une fois la connexion vérifiée, exécutez le script de migration :

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

### Étape 4 : Vérifier les Tables Créées

Vérifiez que les tables ont bien été créées :

```bash
python3 -c "
from app import app
from models import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    rh_tables = [t for t in tables if 'employee' in t or 'activity' in t]
    print('📊 Tables RH créées:')
    for t in sorted(rh_tables):
        print(f'   ✅ {t}')
"
```

---

## 🔄 MÉTHODE 2 : Via un Script de Migration Personnalisé

Si vous avez un script SQL personnalisé à exécuter :

### Étape 1 : Créer un Script Python de Migration

Créez un fichier `execute_custom_migration.py` :

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from app import app
from models import db

def execute_custom_migration():
    """Exécuter une migration SQL personnalisée"""
    script_path = 'votre_migration.sql'  # Remplacez par votre fichier SQL
    
    if not os.path.exists(script_path):
        print(f"❌ Erreur: Le fichier {script_path} n'existe pas")
        return False
    
    try:
        with app.app_context():
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            print("🔄 Exécution de la migration...")
            
            # Diviser par ';' et exécuter chaque commande
            commands = [cmd.strip() for cmd in sql_script.split(';') 
                       if cmd.strip() and not cmd.strip().startswith('--')]
            
            executed = 0
            for command in commands:
                if command:
                    try:
                        db.session.execute(db.text(command))
                        db.session.commit()
                        executed += 1
                    except Exception as e:
                        error_msg = str(e)
                        # Ignorer les erreurs "already exists"
                        if 'already exists' not in error_msg.lower():
                            print(f"⚠️  Erreur: {error_msg}")
                            db.session.rollback()
            
            print(f"✅ {executed} commande(s) exécutée(s)")
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    execute_custom_migration()
```

### Étape 2 : Exécuter le Script dans le Shell Render

```bash
python3 execute_custom_migration.py
```

---

## 📝 MÉTHODE 3 : Exécuter un Fichier SQL Directement

### Étape 1 : Se Connecter à PostgreSQL via psql

Dans le Shell Render, connectez-vous à PostgreSQL :

```bash
# Récupérer les informations de connexion depuis DATABASE_URL
python3 -c "
import os
from urllib.parse import urlparse
url = urlparse(os.environ['DATABASE_URL'])
print(f'psql -h {url.hostname} -p {url.port} -U {url.username} -d {url.path[1:]}')
"
```

### Étape 2 : Exécuter le Fichier SQL

```bash
# Exécuter un fichier SQL
psql $DATABASE_URL -f migration_rh_complete_postgresql.sql
```

**Note :** Cette méthode nécessite que `psql` soit disponible dans le Shell Render.

---

## 🔧 MÉTHODE ALTERNATIVE : Migration Automatique au Déploiement

Si vous voulez que la migration s'exécute automatiquement à chaque déploiement :

### Option 1 : Modifier le Build Command

Dans **Render Dashboard > Settings > Build Command**, modifiez :

```bash
pip install -r requirements.txt && python3 execute_migration_rh_postgresql.py
```

**⚠️ Attention :** Cette méthode exécute la migration à chaque déploiement. Assurez-vous que vos migrations sont idempotentes (utilisent `IF NOT EXISTS`).

### Option 2 : Créer un Script de Déploiement

Créez un fichier `deploy.sh` :

```bash
#!/bin/bash
set -e

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "🔄 Exécution de la migration..."
python3 execute_migration_rh_postgresql.py || echo "⚠️  Migration déjà exécutée"

echo "✅ Déploiement terminé !"
```

Puis dans **Render Dashboard > Settings > Build Command** :

```bash
chmod +x deploy.sh && ./deploy.sh
```

---

## ✅ Vérification Post-Migration

### Vérifier les Tables Créées

```bash
python3 -c "
from app import app
from models import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('📊 Toutes les tables:')
    for t in sorted(tables):
        print(f'   - {t}')
"
```

### Vérifier la Structure d'une Table

```bash
python3 -c "
from app import app
from models import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('employees')  # Remplacez 'employees' par votre table
    print('📋 Colonnes de la table employees:')
    for col in columns:
        print(f'   - {col[\"name\"]}: {col[\"type\"]}')
"
```

### Vérifier les Données

```bash
python3 -c "
from app import app
from models import db

with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM employees'))
    count = result.scalar()
    print(f'📊 Nombre d\'employés: {count}')
"
```

---

## ⚠️ Gestion des Erreurs

### Erreur : "Can't connect to PostgreSQL"

**Solutions :**
1. Vérifiez que `DATABASE_URL` est correcte dans Render Dashboard > Environment
2. Vérifiez que la base de données PostgreSQL est active (pas en veille)
3. Vérifiez les identifiants de connexion

### Erreur : "relation already exists"

**C'est normal !** Les tables existent déjà. Le script utilise `CREATE TABLE IF NOT EXISTS`.

**Solution :** Ignorez cette erreur, la migration continue.

### Erreur : "type already exists"

**C'est normal !** Les types ENUM existent déjà.

**Solution :** Ignorez cette erreur.

### Erreur : "permission denied"

**Solution :** Vérifiez que l'utilisateur PostgreSQL a les droits nécessaires. Sur Render, c'est généralement automatique.

### Erreur : "Module not found"

**Solution :** Assurez-vous que toutes les dépendances sont installées :

```bash
pip install -r requirements.txt
```

---

## 📊 Exemples de Migrations Courantes

### Ajouter une Colonne

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
```

### Créer une Table

```sql
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Créer un Index

```sql
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
```

---

## 🎯 Checklist de Mise à Jour

Avant de mettre à jour la base de données :

- [ ] Vérifier que la connexion PostgreSQL fonctionne
- [ ] Sauvegarder la base de données (si possible)
- [ ] Tester la migration en local d'abord
- [ ] Vérifier que le script SQL est correct
- [ ] S'assurer que les migrations sont idempotentes (`IF NOT EXISTS`)

Après la mise à jour :

- [ ] Vérifier que les tables/colonnes ont été créées
- [ ] Tester les fonctionnalités de l'application
- [ ] Vérifier les logs pour les erreurs
- [ ] Redémarrer l'application si nécessaire

---

## 🆘 Support et Ressources

### Logs Render

Pour voir les logs en temps réel :
- Render Dashboard > Service > Logs

### Documentation Render

- [Render Documentation](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/databases)

### Scripts Disponibles dans le Projet

- `execute_migration_rh_postgresql.py` - Migration RH complète
- `test_connection_postgresql.py` - Test de connexion
- `migration_rh_complete_postgresql.sql` - Script SQL de migration

---

## 📝 Notes Importantes

- ✅ Les migrations sont **idempotentes** : elles peuvent être exécutées plusieurs fois sans problème
- ✅ Les tables existantes ne seront **pas écrasées**
- ✅ Les données existantes seront **préservées**
- ✅ Les index et contraintes seront créés automatiquement
- ⚠️ Toujours tester en local avant de mettre à jour en production
- ⚠️ Faire une sauvegarde si possible avant les migrations importantes

---

**🎉 Votre base de données PostgreSQL est maintenant à jour sur Render !**

