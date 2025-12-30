# 🚀 EXÉCUTER LA MIGRATION RH SUR RENDER

**Base de données :** PostgreSQL (Render)  
**Date :** 2025-01-XX

---

## 📋 MÉTHODE RECOMMANDÉE : Via Shell Render

### Étape 1 : Accéder au Shell Render

1. Allez sur [Render Dashboard](https://dashboard.render.com)
2. Sélectionnez votre **service Web** (celui qui héberge votre application Flask)
3. Cliquez sur **"Shell"** dans le menu de gauche
4. Un terminal s'ouvre

---

### Étape 2 : Vérifier la connexion PostgreSQL

Dans le Shell Render, exécutez :

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

## 🔄 MÉTHODE ALTERNATIVE : Via Build Command

Si vous préférez exécuter la migration automatiquement au déploiement :

### Option 1 : Modifier le Build Command

Dans **Render Dashboard > Settings > Build Command** :

```bash
pip install -r requirements.txt && python3 execute_migration_rh_postgresql.py
```

### Option 2 : Créer un script de déploiement

Créez un fichier `deploy.sh` :

```bash
#!/bin/bash
set -e

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "🔄 Exécution de la migration RH..."
python3 execute_migration_rh_postgresql.py

echo "✅ Migration terminée !"
```

Puis dans **Render Dashboard > Settings > Start Command** :

```bash
gunicorn app:app
```

---

## ✅ VÉRIFICATION POST-MIGRATION

### Vérifier les tables créées

Dans le Shell Render :

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

**Résultat attendu :**
```
📊 Tables RH créées:
   ✅ employee_absences
   ✅ employee_contracts
   ✅ employee_evaluations
   ✅ employee_trainings
   ✅ employees
   ✅ user_activity_logs
```

---

## 🧪 TEST DES FONCTIONNALITÉS

Après la migration, testez l'application :

1. **Redémarrez le service** (si nécessaire)
2. **Connectez-vous** à l'application
3. **Accédez au module RH** : `/rh/personnel`
4. **Créez un utilisateur RH** : `/rh/personnel/new`
5. **Testez les fonctionnalités** :
   - Liste du personnel
   - Gestion des employés externes
   - Contrats, formations, évaluations, absences

---

## ⚠️ GESTION DES ERREURS

### Erreur : "relation already exists"

**C'est normal !** Les tables existent déjà. Le script utilise `CREATE TABLE IF NOT EXISTS`.

**Solution :** Ignorez cette erreur, la migration continue.

### Erreur : "type already exists"

**C'est normal !** Les types ENUM existent déjà.

**Solution :** Ignorez cette erreur.

### Erreur : "permission denied"

**Solution :** Vérifiez que l'utilisateur PostgreSQL a les droits nécessaires. Sur Render, c'est généralement automatique.

---

## 📝 NOTES IMPORTANTES

- ✅ La migration est **idempotente** : elle peut être exécutée plusieurs fois sans problème
- ✅ Les tables existantes ne seront **pas écrasées**
- ✅ Les données existantes seront **préservées**
- ✅ Les index et contraintes seront créés automatiquement

---

## 🎯 CHECKLIST FINALE

- [ ] Connexion PostgreSQL testée
- [ ] Migration exécutée sans erreur critique
- [ ] 6 tables RH vérifiées
- [ ] Application redémarrée
- [ ] Fonctionnalités RH testées

---

## 🆘 SUPPORT

Si vous rencontrez des problèmes :

1. **Vérifiez les logs Render** :
   - Dashboard > Logs
   - Cherchez les erreurs liées à PostgreSQL

2. **Vérifiez DATABASE_URL** :
   - Dashboard > Environment
   - Vérifiez que `DATABASE_URL` est définie

3. **Contactez le support** si nécessaire

---

**Prêt à exécuter sur Render ! 🚀**

