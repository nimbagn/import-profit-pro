# 📋 Guide : Ajouter la colonne 'reason' à stock_returns sur Render

## 🎯 Objectif

Ce script ajoute la colonne `reason` (TEXT NULL) à la table `stock_returns` pour permettre l'enregistrement de la raison du retour.

## 📁 Fichiers

- **MySQL** : `scripts/add_reason_column_stock_returns_mysql.sql`
- **PostgreSQL** : `scripts/add_reason_column_stock_returns_postgresql.sql`

## 🚀 Méthode 1 : Via le Terminal Render (Recommandé)

### Étape 1 : Se connecter au service Render

```bash
# Via SSH (si activé)
render ssh <service-name>

# Ou via le shell du service
# Dans le dashboard Render, allez dans votre service web
# Cliquez sur "Shell" dans le menu latéral
```

### Étape 2 : Naviguer vers le répertoire du projet

```bash
cd ~/project/src
```

### Étape 3 : Exécuter le script SQL

**Pour PostgreSQL (Render)** :
```bash
psql $DATABASE_URL -f scripts/add_reason_column_stock_returns_postgresql.sql
```

**Pour MySQL (si vous utilisez MySQL)** :
```bash
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < scripts/add_reason_column_stock_returns_mysql.sql
```

## 🖥️ Méthode 2 : Via le SQL Editor de Render

### Étape 1 : Accéder au SQL Editor

1. Connectez-vous à votre dashboard Render
2. Allez dans votre base de données PostgreSQL
3. Cliquez sur "Connect" ou "SQL Editor"

### Étape 2 : Copier le contenu du script

Ouvrez le fichier `scripts/add_reason_column_stock_returns_postgresql.sql` et copiez tout son contenu.

### Étape 3 : Coller et exécuter

1. Collez le contenu dans l'éditeur SQL
2. Cliquez sur "Run" ou "Execute"
3. Vérifiez les résultats dans la console

## 📊 Résultats Attendus

### ✅ Succès

Le script devrait afficher :

```
✅ Colonne reason ajoutée à stock_returns
```

Ou si la colonne existe déjà :

```
ℹ️  Colonne reason existe déjà
```

### 📋 Vérification

Après exécution, vérifiez que la colonne existe :

```sql
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public'
    AND table_name = 'stock_returns'
    AND column_name = 'reason';
```

Résultat attendu :
```
column_name | data_type | is_nullable
------------+-----------+-------------
reason      | text      | YES
```

## 🔍 Vérification Manuelle (Optionnel)

### Vérifier la structure de la table

```sql
\d stock_returns
```

Ou :

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'stock_returns'
ORDER BY ordinal_position;
```

## 🎯 Après l'Exécution

Une fois le script exécuté avec succès :

1. ✅ La colonne `reason` est disponible dans `stock_returns`
2. ✅ Les retours peuvent maintenant enregistrer une raison
3. ✅ Le code Python fonctionne correctement
4. ✅ Plus d'erreur `Unknown column 'reason'`

## 🐛 Dépannage

### Erreur : "column reason already exists"

Cela signifie que la colonne existe déjà. C'est normal, le script gère ce cas.

### Erreur : "permission denied"

Assurez-vous d'être connecté avec un utilisateur ayant les droits `ALTER TABLE` sur la base de données.

### Erreur : "relation stock_returns does not exist"

Vérifiez que la table `stock_returns` existe. Si elle n'existe pas, exécutez d'abord les migrations de base.

## 📝 Notes

- Ce script est **idempotent** : il peut être exécuté plusieurs fois sans erreur
- Il ne modifie **pas** les données existantes
- La colonne est **nullable** (peut être NULL)

## ✅ Validation

Après exécution, testez dans l'application :
1. Allez sur `/stocks/returns/new`
2. Créez un nouveau retour
3. Vérifiez que le champ "Raison" fonctionne
4. Vérifiez qu'il n'y a plus d'erreur SQL

---

**Date de création** : 8 Janvier 2026  
**Dernière mise à jour** : 8 Janvier 2026

