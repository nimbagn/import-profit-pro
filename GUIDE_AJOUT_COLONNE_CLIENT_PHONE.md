# 🔧 Guide : Ajout de la colonne client_phone

## Problème
L'erreur `Unknown column 'stock_outgoings.client_phone'` indique que la colonne `client_phone` n'existe pas dans les tables MySQL.

## Solution

### Option 1 : Script SQL automatique (Recommandé)

Exécutez le script SQL directement :

```bash
mysql -u root -p import_profit < scripts/add_client_phone_mysql_simple.sql
```

Vous serez invité à entrer votre mot de passe MySQL.

### Option 2 : Exécution manuelle dans MySQL

1. Connectez-vous à MySQL :
```bash
mysql -u root -p
```

2. Sélectionnez la base de données :
```sql
USE import_profit;
```

3. Ajoutez les colonnes :
```sql
ALTER TABLE stock_outgoings 
ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name;

ALTER TABLE stock_returns 
ADD COLUMN client_phone VARCHAR(20) NULL AFTER client_name;
```

4. Vérifiez que les colonnes ont été ajoutées :
```sql
DESCRIBE stock_outgoings;
DESCRIBE stock_returns;
```

### Option 3 : Script Python (si MySQL est accessible)

```bash
python3 scripts/add_client_phone_mysql.py
```

## Vérification

Après avoir ajouté les colonnes, redémarrez l'application Flask :

```bash
pkill -f "python.*app.py"
python3 app.py
```

L'erreur devrait être résolue et la page `/stocks/outgoings` devrait fonctionner correctement.

## Note

Si vous utilisez SQLite (fallback), les colonnes sont déjà ajoutées automatiquement. Cette procédure est uniquement nécessaire pour MySQL.

