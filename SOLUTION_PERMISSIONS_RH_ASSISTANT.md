# Solution : Assistante RH ne peut pas créer d'employé externe

## 🔍 Diagnostic

Le problème vient probablement des **permissions du rôle `rh_assistant` dans la base de données** qui ne correspondent pas à celles définies dans le code.

La route `/rh/employees/new` vérifie la permission `employees.create` via :
```python
if not has_rh_permission(current_user, 'employees.create'):
    flash('Accès refusé', 'error')
    return redirect(url_for('rh.employees_list'))
```

## ✅ Solution Rapide (PostgreSQL sur Render)

### Étape 1 : Connectez-vous à votre base PostgreSQL

1. Allez sur votre dashboard Render
2. Ouvrez votre base de données PostgreSQL
3. Cliquez sur "Connect" ou utilisez psql

### Étape 2 : Exécutez cette commande SQL

```sql
UPDATE roles 
SET permissions = '{
    "users": ["read", "create", "update"],
    "employees": ["read", "create", "update"],
    "contracts": ["read", "create", "update"],
    "trainings": ["read", "create", "update"],
    "evaluations": ["read", "create"],
    "absences": ["read", "create", "update"],
    "reports": ["read"]
}'::jsonb
WHERE code = 'rh_assistant';
```

### Étape 3 : Vérifiez

```sql
SELECT id, name, code, permissions->'employees' as employees_perms
FROM roles 
WHERE code = 'rh_assistant';
```

Vous devriez voir : `["read", "create", "update"]`

### Étape 4 : Redémarrez l'application

L'assistante RH devrait maintenant pouvoir créer des employés externes.

## 📋 Permissions Requises

Le rôle `rh_assistant` doit avoir ces permissions :

```json
{
    "users": ["read", "create", "update"],
    "employees": ["read", "create", "update"],  ← IMPORTANT : "create" doit être présent
    "contracts": ["read", "create", "update"],
    "trainings": ["read", "create", "update"],
    "evaluations": ["read", "create"],
    "absences": ["read", "create", "update"],
    "reports": ["read"]
}
```

## 🔍 Vérifications Supplémentaires

### 1. Vérifier que l'utilisateur a bien le rôle rh_assistant

```sql
SELECT u.username, u.full_name, r.name, r.code
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.username = 'nom_utilisateur_assistante';
```

### 2. Vérifier les permissions supplémentaires

Si l'utilisateur a des `additional_permissions`, elles peuvent interférer. Vérifiez :

```sql
SELECT username, additional_permissions
FROM users
WHERE username = 'nom_utilisateur_assistante';
```

### 3. Tester l'accès

Après la correction, l'assistante RH devrait pouvoir :
- ✅ Accéder à `/rh/employees` (liste des employés)
- ✅ Accéder à `/rh/employees/new` (créer un employé)
- ✅ Voir le bouton "Nouvel Employé" sur la page de liste

## 📝 Fichiers Créés

J'ai créé ces fichiers pour vous aider :

1. **`scripts/corriger_permissions_rh_assistant_postgresql.sql`** - Script SQL pour PostgreSQL
2. **`scripts/corriger_permissions_rh_assistant.sql`** - Script SQL pour MySQL
3. **`GUIDE_CORRIGER_PERMISSIONS_RH_ASSISTANT.md`** - Guide détaillé
4. **`verifier_permissions_rh_assistant.py`** - Script Python de vérification

## ⚠️ Si le problème persiste

1. Vérifiez les logs de l'application pour voir le message d'erreur exact
2. Vérifiez que l'utilisateur est bien connecté avec le bon rôle
3. Videz le cache du navigateur et reconnectez-vous
4. Vérifiez qu'il n'y a pas de permissions supplémentaires qui bloquent

## 🎯 Résultat Attendu

Après la correction, l'assistante RH pourra :
- ✅ Créer des employés externes
- ✅ Modifier des employés existants
- ✅ Voir la liste des employés
- ✅ Accéder à tous les modules RH autorisés

