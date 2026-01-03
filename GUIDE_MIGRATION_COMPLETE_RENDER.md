# 🚀 GUIDE : MIGRATION COMPLÈTE POSTGRESQL SUR RENDER

**Date :** 2 Janvier 2026

---

## 📋 OBJECTIF

Ce guide explique comment exécuter le script de migration complète PostgreSQL sur Render pour mettre à jour la base de données avec toutes les fonctionnalités du projet.

---

## 📦 CONTENU DE LA MIGRATION

Le script `scripts/migration_complete_postgresql_render.sql` inclut :

1. ✅ **Colonne `additional_permissions`** dans `users`
2. ✅ **Migration `price_list_items`** : `article_id` → `stock_item_id`
3. ✅ **Colonne `reference`** dans `stock_movements`
4. ✅ **`unit_price_gnf` nullable** dans `reception_details`
5. ✅ **Retours fournisseurs** : `return_type`, `supplier_name`, `original_reception_id`
6. ✅ **Type de mouvement `reception_return`** dans `movement_type`
7. ✅ **Permissions rôle magasinier** (warehouse)
8. ✅ **Permissions rôle rh_assistant**

---

## 🔧 MÉTHODE 1 : VIA RENDER SHELL (RECOMMANDÉ)

### Étape 1 : Accéder au Shell Render

1. Connectez-vous à votre compte Render
2. Allez dans votre service de base de données PostgreSQL
3. Cliquez sur "Shell" ou "Connect" pour ouvrir un terminal

### Étape 2 : Télécharger le script

```bash
# Créer le fichier de migration
cat > /tmp/migration_complete.sql << 'EOF'
# Copier le contenu de scripts/migration_complete_postgresql_render.sql ici
EOF
```

**OU** copier le fichier depuis votre machine locale :

```bash
# Depuis votre machine locale, copier le fichier vers Render
# (Utilisez scp ou le portail Render pour uploader le fichier)
```

### Étape 3 : Exécuter le script

```bash
# Se connecter à PostgreSQL
psql $DATABASE_URL

# Ou si vous avez les variables d'environnement séparées :
psql -h <host> -U <user> -d <database>

# Exécuter le script
\i /tmp/migration_complete.sql

# Ou copier-coller directement le contenu du script
```

---

## 🔧 MÉTHODE 2 : VIA RENDER DASHBOARD

### Étape 1 : Accéder à la base de données

1. Connectez-vous à Render Dashboard
2. Allez dans votre service PostgreSQL
3. Cliquez sur "Connect" ou "Shell"

### Étape 2 : Exécuter le script

1. Copiez le contenu de `scripts/migration_complete_postgresql_render.sql`
2. Collez-le dans le terminal PostgreSQL
3. Appuyez sur Entrée pour exécuter

---

## 🔧 MÉTHODE 3 : VIA PYTHON SCRIPT (ALTERNATIVE)

Créez un script Python pour exécuter la migration :

```python
import psycopg2
import os

# Récupérer l'URL de la base de données depuis les variables d'environnement
DATABASE_URL = os.getenv('DATABASE_URL')

# Lire le script SQL
with open('scripts/migration_complete_postgresql_render.sql', 'r') as f:
    sql_script = f.read()

# Se connecter et exécuter
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

try:
    cursor.execute(sql_script)
    conn.commit()
    print("✅ Migration réussie!")
except Exception as e:
    conn.rollback()
    print(f"❌ Erreur: {e}")
finally:
    cursor.close()
    conn.close()
```

---

## ✅ VÉRIFICATION

Après l'exécution, vérifiez que toutes les migrations ont été appliquées :

```sql
-- Vérifier additional_permissions
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'additional_permissions';

-- Vérifier stock_item_id
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'price_list_items' AND column_name = 'stock_item_id';

-- Vérifier reference
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'stock_movements' AND column_name = 'reference';

-- Vérifier return_type
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'stock_returns' AND column_name = 'return_type';

-- Vérifier reception_return
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'movement_type')
AND enumlabel = 'reception_return';
```

---

## ⚠️ NOTES IMPORTANTES

1. **Idempotence** : Le script est idempotent et peut être exécuté plusieurs fois sans erreur
2. **Transaction** : Le script utilise `BEGIN` et `COMMIT` pour garantir l'intégrité
3. **Données** : La migration `price_list_items` supprime les données existantes (pas de correspondance Article → StockItem)
4. **Backup** : Faites un backup de votre base de données avant d'exécuter le script

---

## 🐛 EN CAS D'ERREUR

Si une erreur survient :

1. **Vérifier les logs** : Regardez les messages `RAISE NOTICE` dans le script
2. **Rollback automatique** : Le script utilise une transaction, donc en cas d'erreur, tout sera annulé
3. **Vérifier les permissions** : Assurez-vous que l'utilisateur PostgreSQL a les droits nécessaires
4. **Vérifier les dépendances** : Assurez-vous que toutes les tables existent avant d'exécuter

---

## 📞 SUPPORT

Si vous rencontrez des problèmes :

1. Vérifiez les logs PostgreSQL
2. Vérifiez que toutes les tables existent
3. Vérifiez les permissions de l'utilisateur
4. Contactez le support technique si nécessaire

---

## ✅ CHECKLIST

Avant d'exécuter :

- [ ] Backup de la base de données effectué
- [ ] Script de migration téléchargé/copié
- [ ] Accès au shell PostgreSQL sur Render
- [ ] Variables d'environnement configurées

Après l'exécution :

- [ ] Vérification des colonnes ajoutées
- [ ] Vérification des types ENUM
- [ ] Vérification des permissions des rôles
- [ ] Test de l'application

---

**✅ Migration terminée avec succès !**

