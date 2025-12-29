# 🚀 Initialisation Complète de la Base de Données

## 📋 Vue d'ensemble

Ce script crée **toutes les tables** nécessaires pour toutes les fonctionnalités du projet et initialise l'utilisateur admin.

## ⚠️ ATTENTION

**Ce script supprime toutes les données existantes** et recrée la base de données de zéro.

## 🎯 Méthode Recommandée : Script Automatique

```bash
./executer_initialisation.sh
```

Le script va :
- ✅ Détecter automatiquement le nom de la base depuis `config.py`
- ✅ Vérifier MySQL
- ✅ Demander vos identifiants
- ✅ Créer la base si nécessaire
- ✅ Exécuter l'initialisation
- ✅ Afficher un résumé

## 📦 Bases de données supportées

Le script détecte automatiquement :
- `import_profit` (défaut dans `config.py`)
- `madargn` (si utilisé dans vos scripts)

Vous pouvez aussi spécifier manuellement le nom de la base.

## 🔧 Méthode Alternative : Commande Manuelle

### Si votre base s'appelle `madargn` :

```bash
mysql -u root -p madargn < INITIALISATION_COMPLETE.sql
```

### Si votre base s'appelle `import_profit` :

Modifiez d'abord le script SQL :
```bash
sed 's/USE madargn;/USE import_profit;/' INITIALISATION_COMPLETE.sql > INIT_import_profit.sql
mysql -u root -p import_profit < INIT_import_profit.sql
```

Ou modifiez directement la ligne 8 du fichier SQL :
```sql
USE import_profit;  -- au lieu de USE madargn;
```

## ✅ Après l'exécution

1. **Redémarrez Flask** :
   ```bash
   pkill -f "python.*app.py"
   python3 app.py
   ```

2. **Connectez-vous** :
   - URL : http://localhost:5002/auth/login
   - Username : `admin`
   - Password : `admin123`

## 📊 Ce qui est créé

- ✅ **21 tables** avec toutes les fonctionnalités
- ✅ **4 rôles** (Admin, Magasinier, Commercial, Superviseur)
- ✅ **1 utilisateur admin** (admin/admin123)
- ✅ **8 catégories** de base
- ✅ **4 articles** de démonstration

## 🔍 Vérification

Le script affiche automatiquement un résumé avec :
- Nombre de rôles créés
- Nombre d'utilisateurs créés
- Nombre de catégories créées
- Nombre d'articles créés
- Détails de l'utilisateur admin

## 🛠️ Dépannage

### Erreur : "Access denied"
Vérifiez vos identifiants MySQL dans `config.py` ou utilisez les bons identifiants lors de l'exécution.

### Erreur : "Database doesn't exist"
Le script peut créer la base automatiquement si vous utilisez `./executer_initialisation.sh`

### Erreur : "Table already exists"
Le script supprime d'abord toutes les tables. Si l'erreur persiste, supprimez manuellement la base :
```sql
DROP DATABASE madargn;
CREATE DATABASE madargn;
```

## 📚 Documentation complète

- `GUIDE_INITIALISATION.md` - Guide détaillé
- `INSTRUCTIONS_RAPIDES.md` - Instructions rapides

---

**Prêt ?** Exécutez : `./executer_initialisation.sh`

