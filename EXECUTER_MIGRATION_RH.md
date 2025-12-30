# 🚀 Guide d'Exécution de la Migration RH

## 📋 Instructions

### Option 1 : Exécution directe depuis MySQL

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p madargn < migration_rh_complete.sql
```

Ou en entrant le mot de passe directement (moins sécurisé) :
```bash
mysql -h 127.0.0.1 -P 3306 -u root -p'Z@291721Gn@' madargn < migration_rh_complete.sql
```

### Option 2 : Exécution depuis le client MySQL

1. Connectez-vous à MySQL :
```bash
mysql -h 127.0.0.1 -P 3306 -u root -p madargn
```

2. Une fois connecté, exécutez :
```sql
source /Users/dantawi/Documents/mini_flask_import_profitability/migration_rh_complete.sql;
```

### Option 3 : Copier-coller le contenu

1. Ouvrez le fichier `migration_rh_complete.sql`
2. Copiez tout le contenu
3. Collez-le dans votre client MySQL
4. Exécutez

## ✅ Vérification

Après l'exécution, vérifiez que les tables ont été créées :

```sql
SHOW TABLES LIKE '%employee%';
SHOW TABLES LIKE '%activity%';
```

Vous devriez voir :
- `user_activity_logs`
- `employees`
- `employee_contracts`
- `employee_trainings`
- `employee_evaluations`
- `employee_absences`

## 🔍 Vérifier la structure d'une table

```sql
DESCRIBE employees;
DESCRIBE employee_contracts;
```

## ⚠️ Notes importantes

1. **Si les tables existent déjà** : Le script utilise `CREATE TABLE IF NOT EXISTS`, donc il ne supprimera pas les données existantes
2. **Erreurs de clés étrangères** : Assurez-vous que les tables `users`, `regions`, et `depots` existent déjà
3. **Correction de l'erreur** : Le script corrige l'erreur "cutom" → "custom" dans `evaluation_type`

## 🎯 Après la migration

1. Redémarrez votre application Flask
2. Les nouveaux rôles RH seront automatiquement créés au démarrage
3. Vous pouvez maintenant créer des utilisateurs avec les rôles RH

