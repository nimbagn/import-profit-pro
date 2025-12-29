# Guide Rapide - Résoudre le problème de connexion

## Problème
On vous dit que l'utilisateur est créé mais vous ne pouvez pas vous connecter.

## Solution en 2 étapes

### Étape 1 : Vérifier et corriger dans MySQL

```bash
mysql -u root -p madargn < VERIFIER_ET_CORRIGER.sql
```

Ce script va :
1. Vérifier l'état actuel
2. Corriger automatiquement les problèmes
3. Créer l'utilisateur admin avec le bon hash

### Étape 2 : Redémarrer Flask

```bash
# Arrêter Flask
pkill -f "python.*app.py"

# Relancer Flask
cd /Users/dantawi/Documents/mini_flask_import_profitability
python3 app.py
```

### Étape 3 : Tester la connexion

1. Allez sur http://localhost:5002/auth/login
2. Utilisez :
   - **Username** : `admin`
   - **Password** : `admin123`

## Vérifier les logs Flask

Quand vous essayez de vous connecter, regardez le terminal Flask. Vous devriez voir :

- `❌ DEBUG: Utilisateur 'admin' non trouvé` → L'utilisateur n'existe pas
- `❌ DEBUG: Hash du mot de passe invalide` → Le hash est incorrect  
- `✅ DEBUG: Utilisateur 'admin' trouvé et mot de passe valide` → Tout est OK

## Si cela ne fonctionne toujours pas

Exécutez cette requête SQL pour voir exactement ce qui est dans la base :

```sql
USE madargn;
SELECT * FROM users WHERE username = 'admin';
SELECT * FROM roles WHERE code = 'admin';
```

Et partagez le résultat avec moi.








