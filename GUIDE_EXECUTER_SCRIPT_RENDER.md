# Guide : Exécuter le Script SQL sur Render

## 🎯 Objectif

Exécuter le script `ajouter_permissions_magasinier_postgresql.sql` sur Render pour mettre à jour les permissions du rôle magasinier dans la base de données PostgreSQL.

## 📋 Prérequis

1. ✅ Accès à votre compte Render
2. ✅ Base de données PostgreSQL créée sur Render
3. ✅ Connexion à la base de données configurée

## 🚀 Méthode 1 : Via l'Interface Web Render (RECOMMANDÉ)

### Étape 1 : Accéder à votre Base de Données

1. **Connectez-vous à Render** : https://dashboard.render.com
2. **Allez dans votre projet** (Import Profit Pro)
3. **Cliquez sur votre base de données PostgreSQL**
   - Elle devrait s'appeler quelque chose comme `import-profit-pro-db` ou similaire

### Étape 2 : Ouvrir le SQL Editor

1. Dans la page de votre base de données, cherchez l'onglet **"SQL Editor"** ou **"Query"**
2. Cliquez dessus pour ouvrir l'éditeur SQL

### Étape 3 : Copier-Coller le Script

1. **Ouvrez le fichier** `scripts/ajouter_permissions_magasinier_postgresql.sql` dans votre éditeur local
2. **Copiez tout le contenu** du fichier (Ctrl+A, Ctrl+C ou Cmd+A, Cmd+C)
3. **Collez le contenu** dans l'éditeur SQL de Render

### Étape 4 : Exécuter le Script

1. **Vérifiez** que le script est bien collé dans l'éditeur
2. **Cliquez sur le bouton "Run"** ou "Execute" (ou appuyez sur Ctrl+Enter)
3. **Attendez** que l'exécution se termine

### Étape 5 : Vérifier le Résultat

Vous devriez voir un message de succès :
```
NOTICE: Permissions du rôle magasinier mises à jour avec succès
NOTICE: Nouvelles permissions: {...}
```

## 🔧 Méthode 2 : Via psql en Ligne de Commande

### Étape 1 : Récupérer les Informations de Connexion

1. Dans Render, allez dans votre base de données PostgreSQL
2. **Copiez la chaîne de connexion** (Connection String)
   - Format : `postgresql://user:password@host:port/database`
   - Ou récupérez les informations séparément :
     - **Host** : `xxxxx.render.com`
     - **Port** : `5432` (généralement)
     - **Database** : nom de votre base
     - **User** : nom d'utilisateur
     - **Password** : mot de passe

### Étape 2 : Exécuter le Script

**Option A : Via psql avec redirection**

```bash
# Si vous avez psql installé localement
psql "postgresql://user:password@host:port/database" -f scripts/ajouter_permissions_magasinier_postgresql.sql
```

**Option B : Via psql interactif**

```bash
# Se connecter à la base de données
psql "postgresql://user:password@host:port/database"

# Une fois connecté, copier-coller le contenu du script
# Ou utiliser \i pour exécuter un fichier
\i scripts/ajouter_permissions_magasinier_postgresql.sql
```

**Option C : Via Python (si psql n'est pas disponible)**

```bash
# Créer un script temporaire
cat > execute_script_render.py << 'EOF'
import psycopg2
import os

# Récupérer la chaîne de connexion depuis la variable d'environnement
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL non définie")
    print("   Définissez-la avec: export DATABASE_URL='postgresql://...'")
    exit(1)

# Lire le script SQL
with open('scripts/ajouter_permissions_magasinier_postgresql.sql', 'r') as f:
    script = f.read()

# Se connecter et exécuter
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("🔄 Exécution du script...")
    cursor.execute(script)
    
    print("✅ Script exécuté avec succès!")
    
    # Vérifier les permissions
    cursor.execute("SELECT permissions FROM roles WHERE code = 'warehouse'")
    result = cursor.fetchone()
    if result:
        print(f"📋 Permissions mises à jour: {result[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    exit(1)
EOF

# Exécuter le script
export DATABASE_URL="postgresql://user:password@host:port/database"
python3 execute_script_render.py
```

## 🐍 Méthode 3 : Via Python avec Flask (Depuis le Serveur Render)

Si vous avez accès au serveur Render via SSH ou si vous pouvez exécuter des commandes :

### Étape 1 : Créer un Script d'Exécution

```python
# execute_permissions_render.py
from app import app, db
from models import Role
import sys

def update_permissions():
    with app.app_context():
        warehouse_role = Role.query.filter_by(code='warehouse').first()
        
        if not warehouse_role:
            print("❌ Rôle magasinier non trouvé")
            return False
        
        # Lire et exécuter le script SQL
        with open('scripts/ajouter_permissions_magasinier_postgresql.sql', 'r') as f:
            script = f.read()
        
        # Exécuter le script
        db.session.execute(script)
        db.session.commit()
        
        # Vérifier
        db.session.refresh(warehouse_role)
        print(f"✅ Permissions mises à jour: {warehouse_role.permissions}")
        return True

if __name__ == '__main__':
    try:
        success = update_permissions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### Étape 2 : Exécuter sur Render

```bash
# Via SSH ou console Render
python3 execute_permissions_render.py
```

## ✅ Méthode 4 : Utiliser le Script Python de Mise à Jour

Le script `mettre_a_jour_permissions_magasinier.py` peut être exécuté directement :

### Sur Render (via SSH ou Console)

```bash
# Se connecter au serveur Render (si SSH activé)
# Ou utiliser la console web de Render

# Exécuter le script
python3 mettre_a_jour_permissions_magasinier.py
```

### Via l'Interface Render (Shell)

1. Dans Render, allez dans votre service web (Flask)
2. Cliquez sur **"Shell"** ou **"Console"**
3. Exécutez :
   ```bash
   python3 mettre_a_jour_permissions_magasinier.py
   ```

## 🔍 Vérification Après Exécution

### Via SQL Editor Render

```sql
-- Vérifier les permissions du rôle magasinier
SELECT id, name, code, permissions 
FROM roles 
WHERE code = 'warehouse';

-- Vérifier qu'un utilisateur magasinier existe
SELECT u.id, u.username, u.email, r.name as role_name
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE r.code = 'warehouse';
```

### Via Python

```python
from app import app, db
from models import Role

with app.app_context():
    role = Role.query.filter_by(code='warehouse').first()
    if role:
        print(f"Permissions: {role.permissions}")
        # Vérifier les permissions spécifiques
        perms = role.permissions or {}
        print(f"receptions: {perms.get('receptions', [])}")
        print(f"outgoings: {perms.get('outgoings', [])}")
        print(f"returns: {perms.get('returns', [])}")
        print(f"orders: {perms.get('orders', [])}")
        print(f"stock_loading: {perms.get('stock_loading', [])}")
```

## 🐛 Dépannage

### Problème : "Le rôle magasinier n'existe pas"

**Solution :**
1. Vérifiez que le rôle existe :
   ```sql
   SELECT * FROM roles WHERE code = 'warehouse';
   ```
2. Si le rôle n'existe pas, créez-le d'abord via l'interface d'administration de l'application

### Problème : "Permission denied" ou Erreur de Syntaxe

**Solution :**
1. Vérifiez que vous utilisez bien le script PostgreSQL (pas MySQL)
2. Vérifiez que la syntaxe SQL est correcte
3. Essayez d'exécuter le script section par section

### Problème : Les Permissions ne se Mettent pas à Jour

**Solution :**
1. Vérifiez que la transaction est bien commitée
2. Rechargez la page de l'application
3. Vérifiez les logs de l'application pour des erreurs

## 📝 Notes Importantes

1. **Sauvegarde** : Avant d'exécuter le script, assurez-vous d'avoir une sauvegarde de votre base de données
2. **Idempotence** : Le script est idempotent, vous pouvez l'exécuter plusieurs fois sans problème
3. **Permissions** : Le script ajoute uniquement les permissions manquantes, il ne supprime pas les permissions existantes
4. **Redémarrage** : Après la mise à jour, redémarrez l'application si nécessaire

## 🚀 Étapes Recommandées

1. ✅ **Sauvegarder** la base de données (via Render Dashboard)
2. ✅ **Exécuter** le script via SQL Editor (Méthode 1 - la plus simple)
3. ✅ **Vérifier** les permissions avec une requête SQL
4. ✅ **Tester** dans l'application avec un compte magasinier
5. ✅ **Redémarrer** l'application si nécessaire

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs de l'application sur Render
2. Vérifiez les logs de la base de données
3. Testez d'abord sur un environnement de développement si possible

