# 🔧 CORRECTION : Colonne 'metadata' réservée par SQLAlchemy

**Date :** 2025-01-XX  
**Problème :** `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.`

---

## ✅ CORRECTION APPLIQUÉE

### Problème
SQLAlchemy réserve le nom `metadata` pour ses propres besoins dans l'API Declarative. Il ne peut pas être utilisé comme nom de colonne.

### Solution
Renommage de la colonne `metadata` en `activity_metadata` dans :
- ✅ `models.py` - Modèle `UserActivityLog`
- ✅ `rh.py` - Fonction `log_activity()`
- ✅ `migration_rh_complete.sql` - Script de migration
- ✅ `migration_add_user_activity_logs.sql` - Script de migration initial

---

## 📝 FICHIERS MODIFIÉS

### 1. `models.py`
```python
# AVANT
metadata = db.Column(db.JSON, nullable=True)

# APRÈS
activity_metadata = db.Column(db.JSON, nullable=True)  # renommé de 'metadata' car réservé par SQLAlchemy
```

### 2. `rh.py`
```python
# AVANT
metadata=metadata if metadata else {},

# APRÈS
activity_metadata=metadata if metadata else {},
```

### 3. Scripts SQL
- `migration_rh_complete.sql` : `metadata` → `activity_metadata`
- `migration_add_user_activity_logs.sql` : `metadata` → `activity_metadata`

---

## 🔄 MISE À JOUR DE LA BASE DE DONNÉES

### Si la table existe déjà avec l'ancien nom

Si vous avez déjà exécuté la migration et que la table `user_activity_logs` existe avec la colonne `metadata`, exécutez :

```sql
ALTER TABLE `user_activity_logs` 
CHANGE COLUMN `metadata` `activity_metadata` JSON NULL;
```

Ou utilisez le script :
```bash
mysql -h 127.0.0.1 -P 3306 -u root -p madargn < fix_metadata_column.sql
```

### Si la table n'existe pas encore

Exécutez simplement la migration mise à jour :
```bash
mysql -h 127.0.0.1 -P 3306 -u root -p madargn < migration_rh_complete.sql
```

---

## ✅ VÉRIFICATION

Le modèle se charge maintenant correctement :
```bash
python3 -c "from models import UserActivityLog; print('OK')"
```

---

## 📌 NOTE IMPORTANTE

- Le paramètre `metadata` dans la fonction `log_activity()` reste inchangé (c'est juste un paramètre Python)
- Seule la colonne de la base de données a été renommée en `activity_metadata`
- Tous les appels à `log_activity()` fonctionnent toujours de la même manière

---

**Correction terminée ! ✅**

