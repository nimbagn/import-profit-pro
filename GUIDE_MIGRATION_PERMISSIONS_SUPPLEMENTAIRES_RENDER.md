# 🚀 GUIDE RAPIDE - Migration Permissions Supplémentaires sur Render

**Date :** 2025-01-XX  
**Base de données :** PostgreSQL (Render)

---

## 📋 PRÉREQUIS

- ✅ Service Render avec base de données PostgreSQL
- ✅ Variable `DATABASE_URL` configurée sur Render
- ✅ Accès au Shell Render

---

## 🎯 EXÉCUTION SUR RENDER

### Méthode 1 : Shell Render (Recommandé)

1. **Accéder au Shell Render** :
   - Dashboard Render > Votre Service > Shell
   - Cliquez sur "Open Shell"

2. **Vérifier la connexion** :
   ```bash
   python3 -c "from app import app; from models import db; app.app_context().push(); db.session.execute(db.text('SELECT 1')); print('✅ Connexion OK')"
   ```

3. **Exécuter la migration** :
   ```bash
   python3 execute_migration_additional_permissions_postgresql.py
   ```

4. **Vérifier le résultat** :
   - Le script affichera "✅ Migration terminée avec succès"
   - La colonne `additional_permissions` sera ajoutée à la table `users`

---

## 🔍 VÉRIFICATION

### Vérifier que la colonne existe

```bash
python3 -c "
from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    result = db.session.execute(text('''
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'additional_permissions'
    '''))
    row = result.fetchone()
    if row:
        print(f'✅ Colonne trouvée: {row[0]} ({row[1]})')
    else:
        print('❌ Colonne non trouvée')
"
```

---

## ✅ PROCHAINES ÉTAPES

Après la migration réussie :

1. **Redémarrer l'application** (si nécessaire)
2. **Tester l'interface** :
   - Aller dans `/auth/users`
   - Modifier un utilisateur RH
   - Vérifier que la section "Permissions Supplémentaires" apparaît
3. **Attribuer des permissions** :
   - Cocher des permissions (ex: `stocks.read`)
   - Enregistrer
   - Tester l'accès

---

## ⚠️ DÉPANNAGE

### Erreur : "column already exists"

**Solution** : C'est normal si la colonne existe déjà. La migration est idempotente.

### Erreur : "permission denied"

**Solution** : Vérifiez que l'utilisateur PostgreSQL a les droits :
```sql
GRANT ALL PRIVILEGES ON TABLE users TO your_user;
```

### Erreur : "relation users does not exist"

**Solution** : Vérifiez que la table `users` existe dans votre base de données.

---

## 📝 NOTES

- ✅ La migration est **idempotente** : peut être exécutée plusieurs fois
- ✅ Les données existantes sont **préservées**
- ✅ La colonne utilise le type **JSONB** (optimisé pour PostgreSQL)
- ✅ Compatible avec **PostgreSQL 12+**

---

**Dernière mise à jour :** 2025-01-XX

