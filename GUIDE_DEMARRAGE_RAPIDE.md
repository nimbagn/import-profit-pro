# 🚀 GUIDE DE DÉMARRAGE RAPIDE - IMPORT PROFIT PRO

## ⚡ Installation en 5 Minutes

### Prérequis
- ✅ Python 3.8 ou supérieur
- ✅ MySQL 5.7 ou supérieur
- ✅ pip (gestionnaire de packages Python)

### Étape 1 : Cloner/Accéder au Projet
```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
```

### Étape 2 : Installer les Dépendances
```bash
pip install -r requirements.txt
```

**Packages principaux installés** :
- Flask>=3.0.3
- Flask-SQLAlchemy==3.1.1
- Flask-Login==0.6.3
- SQLAlchemy==2.0.43
- PyMySQL==1.1.1
- pandas==2.2.2
- openpyxl==3.1.2

### Étape 3 : Configurer la Base de Données

#### Option A : Base de données existante
Vérifiez que MySQL est en cours d'exécution et que la base `madargn` existe :
```bash
mysql -u root -p
CREATE DATABASE IF NOT EXISTS madargn;
```

#### Option B : Créer les tables automatiquement
Les tables seront créées automatiquement au premier lancement via `db.create_all()`.

### Étape 4 : Configurer les Paramètres

Vérifiez/modifiez `config.py` si nécessaire :
```python
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'votre_mot_de_passe'
MYSQL_DATABASE = 'madargn'
```

### Étape 5 : Lancer l'Application
```bash
python3 app.py
```

Vous devriez voir :
```
✅ Configuration MySQL: 127.0.0.1:3306/madargn
✅ Connexion à la base de données réussie
✅ Tables créées avec succès
🚀 IMPORT PROFIT PRO - VERSION NETTOYÉE ET MODERNE
🌐 Serveur démarré sur http://localhost:5002
```

### Étape 6 : Accéder à l'Application

Ouvrez votre navigateur et allez sur :
```
http://localhost:5002
```

---

## 🔑 Identifiants par Défaut

### Administrateur
- **Nom d'utilisateur** : `admin`
- **Mot de passe** : `admin123`
- **Permissions** : Accès complet à toutes les fonctionnalités

### Manager
- **Nom d'utilisateur** : `manager`
- **Mot de passe** : `manager123`
- **Permissions** : Accès à la plupart des fonctionnalités (sauf gestion utilisateurs)

---

## 📋 Premiers Pas

### 1. Se Connecter
1. Allez sur http://localhost:5002
2. Utilisez les identifiants admin
3. Vous arrivez sur le tableau de bord

### 2. Explorer les Modules

#### 💬 Chat Interne
- Cliquez sur "Messages" dans le menu latéral
- Créez une nouvelle conversation
- Testez l'envoi de messages en temps réel

#### 📈 Simulations
- Cliquez sur "Simulations" dans le menu
- Créez une nouvelle simulation
- Ajoutez des articles et calculez la rentabilité

#### 📊 Prévisions
- Cliquez sur "Prévisions & Ventes"
- Créez une prévision
- Saisissez des réalisations

#### 📦 Stocks
- Cliquez sur "Stocks"
- Consultez le récapitulatif
- Créez une réception de stock

#### 🚛 Flotte
- Cliquez sur "Flotte"
- Consultez les véhicules
- Ajoutez un véhicule

---

## 🔧 Résolution de Problèmes Courants

### Erreur : "Connection refused"
**Solution** : Vérifiez que MySQL est en cours d'exécution
```bash
# macOS
brew services start mysql
# ou
sudo /usr/local/mysql/support-files/mysql.server start
```

### Erreur : "Access denied for user"
**Solution** : Vérifiez les identifiants dans `config.py`

### Erreur : "Unknown column"
**Solution** : Les tables sont créées automatiquement. Si l'erreur persiste :
```bash
# Supprimez et recréez les tables
python3 -c "from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"
```

### Erreur : "Module not found"
**Solution** : Réinstallez les dépendances
```bash
pip install -r requirements.txt --upgrade
```

### Port 5002 déjà utilisé
**Solution** : Changez le port dans `app.py` :
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)  # Changez 5002 en 5003
```

---

## 📚 Commandes Utiles

### Lancer l'application
```bash
python3 app.py
```

### Vérifier la connexion MySQL
```bash
mysql -u root -p -e "USE madargn; SHOW TABLES;"
```

### Créer un utilisateur admin
```bash
python3 scripts/create_admin_user.py
```

### Vérifier les logs
```bash
tail -f flask_debug.log
```

### Arrêter l'application
Appuyez sur `Ctrl+C` dans le terminal

---

## 🎯 Workflows Essentiels

### Workflow 1 : Créer une Simulation
1. **Simulations** → **Nouvelle Simulation**
2. Définir les taux de change (USD, EUR)
3. Ajouter les coûts (douane, transport, etc.)
4. Ajouter des articles
5. Calculer la rentabilité
6. Valider la simulation

### Workflow 2 : Gérer le Stock
1. **Stocks** → **Réceptions**
2. Créer une réception
3. Ajouter les articles reçus
4. Valider la réception
5. Consulter le récapitulatif

### Workflow 3 : Communiquer
1. **Messages** → **Nouvelle Conversation**
2. Sélectionner un utilisateur
3. Envoyer un message
4. Partager un fichier (optionnel)

### Workflow 4 : Créer une Prévision
1. **Prévisions & Ventes** → **Nouvelle Prévision**
2. Sélectionner la période
3. Ajouter les articles et objectifs
4. Enregistrer
5. Saisir les réalisations plus tard

---

## 🔐 Sécurité

### Changer les Mots de Passe par Défaut
1. Connectez-vous en tant qu'admin
2. Allez dans **Utilisateurs** → **Gérer les Utilisateurs**
3. Modifiez les mots de passe

### Créer de Nouveaux Rôles
1. **Utilisateurs** → **Rôles**
2. Créez un nouveau rôle
3. Assignez les permissions

---

## 📊 Structure des Données

### Tables Principales
- `users` : Utilisateurs
- `roles` : Rôles
- `simulations` : Simulations
- `forecasts` : Prévisions
- `stock_items` : Articles en stock
- `vehicles` : Véhicules
- `chat_rooms` : Conversations
- `chat_messages` : Messages

### Relations Clés
- Un utilisateur a un rôle
- Un rôle a plusieurs permissions
- Une simulation contient plusieurs articles
- Un stock_item appartient à un dépôt
- Un véhicule a plusieurs documents

---

## 🎨 Personnalisation

### Modifier les Couleurs
Éditez `static/css/hapag_lloyd_style.css` :
```css
:root {
  --color-primary: #003d82;  /* Bleu principal */
  --color-accent: #ff6348;   /* Orange accent */
}
```

### Ajouter un Logo
Remplacez le logo dans `templates/base_modern_complete.html`

### Modifier le Menu
Éditez `templates/base_modern_complete.html` (section menu)

---

## 📞 Support

### Documentation
- `SYNTHESE_COMPLETE_PROJET.md` : Documentation complète
- `CHAT_COMPLETE_FINAL.md` : Documentation du chat
- `GUIDE_DEMARRAGE_RAPIDE.md` : Ce guide

### Logs
- `flask_debug.log` : Logs de l'application
- Console du terminal : Logs en temps réel

### Scripts Utiles
- `scripts/setup_database.sh` : Configuration base
- `scripts/create_admin_user.py` : Créer admin
- `scripts/update_database.py` : Mise à jour

---

## ✅ Checklist de Vérification

Avant de commencer, vérifiez :
- [ ] Python 3.8+ installé
- [ ] MySQL en cours d'exécution
- [ ] Base de données `madargn` créée
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Configuration MySQL correcte dans `config.py`
- [ ] Port 5002 disponible
- [ ] Application lancée sans erreur

Après connexion, vérifiez :
- [ ] Tableau de bord s'affiche
- [ ] Menu latéral visible
- [ ] Tous les modules accessibles
- [ ] Chat fonctionne
- [ ] Pas d'erreurs dans la console

---

## 🎉 Prêt à Commencer !

Votre application est maintenant prête. Explorez les différents modules et commencez à utiliser **Import Profit Pro** !

**Bon travail ! 🚀**








