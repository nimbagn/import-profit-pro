# 🔧 CORRECTION : Relation Employee-User avec plusieurs clés étrangères

**Date :** 2025-01-XX  
**Problème :** `Could not determine join condition between parent/child tables on relationship Employee.user - there are multiple foreign key paths linking the tables.`

---

## ✅ CORRECTION APPLIQUÉE

### Problème
Le modèle `Employee` a **deux clés étrangères** vers la table `users` :
1. `user_id` - Lien vers le compte utilisateur de l'employé (si l'employé a un compte)
2. `created_by_id` - Lien vers l'utilisateur qui a créé l'enregistrement

SQLAlchemy ne pouvait pas déterminer quelle clé étrangère utiliser pour la relation `user` car il y avait deux chemins possibles.

### Solution
Spécification explicite de `foreign_keys=[user_id]` pour la relation `user`.

---

## 📝 FICHIER MODIFIÉ

### `models.py` - Modèle Employee

**AVANT :**
```python
user = db.relationship("User", backref="employee_profile")
created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_employees")
```

**APRÈS :**
```python
user = db.relationship("User", foreign_keys=[user_id], backref="employee_profile")
created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_employees")
```

---

## ✅ VÉRIFICATION

Le modèle se charge maintenant correctement :
```bash
python3 -c "from models import Employee; print('✅ Modèle Employee chargé avec succès')"
```

---

## 📌 EXPLICATION TECHNIQUE

Quand une table a plusieurs clés étrangères vers la même table parente, SQLAlchemy nécessite que vous spécifiez explicitement quelle(s) clé(s) étrangère(s) utiliser pour chaque relation avec l'argument `foreign_keys`.

Dans notre cas :
- `user` → utilise `user_id` (le compte utilisateur de l'employé)
- `created_by` → utilise `created_by_id` (l'utilisateur qui a créé l'enregistrement)

---

**Correction terminée ! ✅**

