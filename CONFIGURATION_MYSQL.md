# 🔧 Configuration MySQL - Guide de résolution

## 📋 Problème identifié

L'application ne peut pas se connecter à MySQL avec l'erreur :
```
Access denied for user 'root'@'localhost' (using password: YES)
```

## 🔍 Configuration actuelle

- **Host:** 127.0.0.1
- **Port:** 3306
- **Database:** madargn
- **User:** root
- **Password:** password (par défaut, probablement incorrect)

## ✅ Solutions

### Option 1 : Créer un fichier .env (Recommandé)

Créez un fichier `.env` à la racine du projet avec vos identifiants MySQL :

```bash
# Fichier .env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=madargn
DB_USER=root
DB_PASSWORD=votre_mot_de_passe_mysql_ici
```

**Important :** Remplacez `votre_mot_de_passe_mysql_ici` par votre vrai mot de passe MySQL.

### Option 2 : Vérifier que MySQL est démarré

**Sur macOS :**
```bash
brew services start mysql
# ou
mysql.server start
```

**Sur Linux :**
```bash
sudo service mysql start
# ou
sudo systemctl start mysql
```

### Option 3 : Vérifier les identifiants MySQL

Connectez-vous à MySQL pour vérifier vos identifiants :

```bash
mysql -u root -p
```

Ensuite, vérifiez que la base de données existe :

```sql
SHOW DATABASES;
USE madargn;
SHOW TABLES;
SELECT COUNT(*) FROM commercial_orders;
```

### Option 4 : Tester avec un mot de passe vide

Si votre MySQL root n'a pas de mot de passe :

```bash
DB_PASSWORD= python3 test_mysql_connection.py
```

Ou créez un fichier `.env` avec :
```
DB_PASSWORD=
```

### Option 5 : Réinitialiser le mot de passe MySQL root

Si vous avez oublié le mot de passe :

**Sur macOS :**
```bash
# Arrêter MySQL
brew services stop mysql

# Démarrer MySQL en mode safe
mysqld_safe --skip-grant-tables &

# Se connecter sans mot de passe
mysql -u root

# Dans MySQL, exécuter :
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'nouveau_mot_de_passe';
FLUSH PRIVILEGES;
exit;

# Redémarrer MySQL normalement
brew services restart mysql
```

## 🧪 Tester la connexion

Après avoir configuré MySQL, testez la connexion :

```bash
python3 test_mysql_connection.py
```

Si la connexion réussit, vous verrez :
```
✅ Connexion réussie!
   Version MySQL: 8.0.x
   Nombre de commandes: X
```

## 🚀 Redémarrer le serveur Flask

Une fois MySQL configuré correctement, redémarrez le serveur Flask :

```bash
bash start_server.sh
```

Ou manuellement :

```bash
lsof -ti:5002 | xargs kill -9 2>/dev/null
python3 app.py
```

## 📝 Notes importantes

1. **Sécurité :** Ne commitez jamais le fichier `.env` dans Git. Il devrait être dans `.gitignore`.

2. **Permissions :** Si vous avez des problèmes de permissions avec le fichier `.env`, vous pouvez :
   ```bash
   chmod 600 .env
   ```

3. **Variables d'environnement :** Les variables dans `.env` ont la priorité sur les valeurs par défaut dans `config.py`.

## 🔗 Fichiers concernés

- `config.py` - Configuration par défaut
- `.env` - Variables d'environnement (à créer)
- `test_mysql_connection.py` - Script de test de connexion

