# Guide : Vérification et Mise à Jour des Données pour le Filtrage par Région

## 📋 Objectif

Ce guide explique comment vérifier et mettre à jour les données de la base de données PostgreSQL sur Render pour que le filtrage par région fonctionne correctement.

## ⚠️ Important

Avant d'exécuter ce script, **assurez-vous d'avoir créé au moins une région** dans votre base de données. Si vous n'avez pas encore de régions, créez-en d'abord via l'interface web (`/referentiels/regions`).

## 🔧 Méthode 1 : Via l'Éditeur SQL de Render (Recommandé)

### Étape 1 : Accéder à l'Éditeur SQL

1. Connectez-vous à votre compte Render
2. Allez dans votre base de données PostgreSQL
3. Cliquez sur l'onglet **"Connect"** ou **"SQL Editor"**
4. Cliquez sur **"Open SQL Editor"** ou **"New Query"**

### Étape 2 : Exécuter le Script

1. Ouvrez le fichier `scripts/verify_and_update_region_data_postgresql.sql`
2. Copiez tout le contenu du fichier
3. Collez-le dans l'éditeur SQL de Render
4. Cliquez sur **"Run"** ou **"Execute"**

### Étape 3 : Vérifier les Résultats

Le script affichera :
- Les utilisateurs sans région (sauf admins)
- Les dépôts sans région
- Les commandes sans région
- Les employés sans région
- Un rapport final avec les statistiques par région

## 🔧 Méthode 2 : Via la Ligne de Commande (psql)

### Étape 1 : Récupérer l'URL de Connexion

1. Dans Render, allez dans votre base de données PostgreSQL
2. Cliquez sur **"Connect"**
3. Copiez l'**External Connection String** (format : `postgresql://user:password@host:port/database`)

### Étape 2 : Exécuter le Script

```bash
# Définir la variable d'environnement DATABASE_URL
export DATABASE_URL="postgresql://user:password@host:port/database"

# Exécuter le script
psql $DATABASE_URL -f scripts/verify_and_update_region_data_postgresql.sql
```

**Note :** Si `psql` n'est pas installé localement, vous pouvez utiliser l'éditeur SQL de Render (Méthode 1).

## 📊 Ce que fait le Script

### 1. Vérification des Utilisateurs
- Identifie les utilisateurs non-admin sans région
- Met à jour automatiquement les utilisateurs sans région avec la première région disponible
- **⚠️ ATTENTION :** Vous devrez peut-être ajuster manuellement la région assignée selon vos besoins

### 2. Vérification des Dépôts
- Vérifie que tous les dépôts ont une région (obligatoire)
- Met à jour les dépôts sans région avec la première région disponible

### 3. Vérification des Commandes Commerciales
- Identifie les commandes sans région
- Met à jour automatiquement les commandes avec la région du commercial qui les a créées

### 4. Vérification des Véhicules
- Vérifie que les conducteurs ont une région
- Les véhicules sont filtrés via le conducteur, donc si le conducteur n'a pas de région, le véhicule ne sera pas visible

### 5. Vérification des Employés (RH)
- Identifie les employés actifs sans région
- Met à jour automatiquement les employés sans région avec la première région disponible

### 6. Rapport Final
- Affiche les statistiques par région (utilisateurs, dépôts, véhicules, commandes, employés)
- Affiche le nombre d'enregistrements sans région restants

## ✅ Après l'Exécution

1. **Vérifiez les résultats** : Le script affichera un rapport final avec les statistiques
2. **Ajustez manuellement si nécessaire** : Certains utilisateurs ou dépôts peuvent nécessiter une assignation manuelle à la bonne région
3. **Testez le filtrage** : Connectez-vous avec différents utilisateurs et vérifiez qu'ils ne voient que les données de leur région

## 🔍 Vérification Manuelle

Après l'exécution du script, vous pouvez vérifier manuellement :

```sql
-- Vérifier les utilisateurs par région
SELECT r.name, COUNT(u.id) as users_count
FROM regions r
LEFT JOIN users u ON r.id = u.region_id AND u.is_active = true
GROUP BY r.id, r.name
ORDER BY r.name;

-- Vérifier les dépôts par région
SELECT r.name, COUNT(d.id) as depots_count
FROM regions r
LEFT JOIN depots d ON r.id = d.region_id AND d.is_active = true
GROUP BY r.id, r.name
ORDER BY r.name;

-- Vérifier les commandes par région
SELECT r.name, COUNT(co.id) as orders_count
FROM regions r
LEFT JOIN commercial_orders co ON r.id = co.region_id
GROUP BY r.id, r.name
ORDER BY r.name;
```

## ⚠️ Notes Importantes

1. **Région par défaut** : Le script utilise la première région disponible comme région par défaut. Vous devrez peut-être ajuster manuellement certaines assignations.

2. **Administrateurs** : Les utilisateurs avec le rôle `admin` ou `superadmin` peuvent ne pas avoir de région - c'est normal et attendu.

3. **Données existantes** : Si vous avez déjà des données dans votre base, le script mettra à jour les enregistrements sans région. Les enregistrements qui ont déjà une région ne seront pas modifiés.

4. **Sauvegarde** : Avant d'exécuter le script sur des données de production, faites une sauvegarde de votre base de données.

## 🆘 Problèmes Courants

### Erreur : "Aucune région trouvée"
**Solution :** Créez d'abord au moins une région via l'interface web (`/referentiels/regions/new`)

### Certains utilisateurs ont la mauvaise région
**Solution :** Mettez à jour manuellement via l'interface web (`/auth/users/{id}/edit`) ou via SQL :
```sql
UPDATE users SET region_id = <region_id> WHERE id = <user_id>;
```

### Les commandes n'ont toujours pas de région
**Solution :** Vérifiez que le commercial qui a créé la commande a bien une région assignée :
```sql
SELECT co.id, co.reference, u.username, u.region_id
FROM commercial_orders co
JOIN users u ON co.commercial_id = u.id
WHERE co.region_id IS NULL;
```

