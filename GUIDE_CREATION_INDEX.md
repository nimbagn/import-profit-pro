# 📋 GUIDE DE CRÉATION DES INDEX DE BASE DE DONNÉES

## 🎯 Objectif

Créer les index manquants sur les colonnes fréquemment utilisées pour améliorer les performances de la base de données.

---

## 📝 Méthode 1 : Script SQL Manuel (Recommandé)

### Étape 1 : Identifier votre base de données

Vérifiez quelle base de données vous utilisez :

```bash
# Option A : Vérifier dans .env
cat .env | grep DB_NAME

# Option B : Vérifier dans config.py
grep DB_NAME config.py

# Option C : Vérifier dans les logs de l'application
grep "Configuration MySQL" app.log
```

### Étape 2 : Modifier le script SQL

Éditez `scripts/add_database_indexes.sql` et modifiez la ligne `USE` :

```sql
-- Remplacez "madargn" par votre base de données
USE madargn;
```

### Étape 3 : Exécuter le script

```bash
# Méthode 1 : Spécifier la base dans la commande
mysql -u root -p madargn < scripts/add_database_indexes.sql

# Méthode 2 : Laisser le script utiliser USE
mysql -u root -p < scripts/add_database_indexes.sql
```

---

## 📝 Méthode 2 : Script Python Automatique

Le script Python détecte automatiquement la base de données depuis `config.py` :

```bash
python3 scripts/add_database_indexes_auto.py
```

**Avantages :**
- ✅ Détection automatique de la base de données
- ✅ Gestion des index déjà existants
- ✅ Messages clairs de progression

**Prérequis :**
- Python 3.x
- pymysql installé
- Accès MySQL avec les identifiants de `config.py`

---

## 🔍 Vérification

Après l'exécution, vérifiez que les index ont été créés :

```sql
-- Se connecter à MySQL
mysql -u root -p

-- Utiliser votre base de données
USE madargn;  -- ou votre base

-- Vérifier les index créés
SHOW INDEX FROM promotion_sales;
SHOW INDEX FROM stock_movements;
SHOW INDEX FROM promotion_stock_movements;
```

---

## ⚠️ Notes Importantes

1. **Sauvegarde** : Faites une sauvegarde de votre base de données avant d'exécuter le script :
   ```bash
   mysqldump -u root -p madargn > backup_before_indexes.sql
   ```

2. **Temps d'exécution** : La création des index peut prendre quelques minutes selon la taille de vos tables.

3. **Index existants** : Le script ignore les index déjà existants (pas d'erreur).

4. **Base de données** : Assurez-vous d'utiliser la bonne base de données (`madargn` ou `import_profit`).

---

## 📊 Index Créés

Le script crée environ **50+ index** sur :

- ✅ Tables de promotion (sales, members, teams, stock)
- ✅ Tables de stocks (movements, receptions, outgoings, returns)
- ✅ Tables d'inventaires (sessions, details)
- ✅ Tables de flotte (vehicles, documents, maintenances, odometers)
- ✅ Tables utilisateurs (users, roles)
- ✅ Tables simulations et articles

---

## 🐛 Résolution de Problèmes

### Erreur : "Unknown database"
```bash
# Vérifiez le nom de votre base de données
mysql -u root -p -e "SHOW DATABASES;"

# Modifiez la ligne USE dans le script SQL
```

### Erreur : "Access denied"
```bash
# Vérifiez vos identifiants MySQL dans config.py ou .env
# Ou utilisez directement mysql avec vos identifiants
mysql -u votre_user -p votre_base < scripts/add_database_indexes.sql
```

### Erreur : "Duplicate key name"
```bash
# C'est normal, l'index existe déjà
# Le script Python gère automatiquement cette erreur
```

---

## ✅ Validation

Après l'exécution, vous devriez voir :
- ✅ Messages de succès pour chaque index créé
- ✅ Performance améliorée sur les requêtes fréquentes
- ✅ Temps de réponse réduit sur les pages de listes

---

**Besoin d'aide ?** Vérifiez les logs dans `app.log` ou contactez le support.

