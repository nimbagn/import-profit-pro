# Guide de Migration PostgreSQL - Module Chat

## 📋 Description

Ce guide explique comment exécuter la migration PostgreSQL pour créer les tables du module chat sur Render.

## 🎯 Objectif

Créer les tables nécessaires au fonctionnement du module chat interne :
- `chat_rooms` : Conversations (direct, groupe, canal)
- `chat_room_members` : Participants des conversations
- `chat_messages` : Messages dans les conversations
- `chat_attachments` : Pièces jointes des messages
- `chat_message_reads` : Marqueurs de lecture

## 📝 Fichiers concernés

- **Script SQL** : `scripts/create_chat_tables_postgresql.sql`
- **Script Git** : `push_fix_chat_json_error.sh`

## 🚀 Exécution sur Render

### Option 1 : Via le Shell Render (Recommandé)

1. **Connectez-vous au Shell Render** :
   - Allez sur https://dashboard.render.com
   - Sélectionnez votre service PostgreSQL
   - Cliquez sur "Shell" dans le menu latéral

2. **Exécutez le script SQL** :
```bash
# Connectez-vous à la base de données
psql $DATABASE_URL

# Copiez-collez le contenu de scripts/create_chat_tables_postgresql.sql
# Ou exécutez directement :
\i /opt/render/project/src/scripts/create_chat_tables_postgresql.sql
```

### Option 2 : Via psql en ligne de commande

```bash
# Si vous avez accès à psql localement avec les credentials Render
psql -h <host> -U <user> -d <database> -f scripts/create_chat_tables_postgresql.sql
```

### Option 3 : Via Python (si le script SQL n'est pas accessible)

Créez un fichier temporaire `create_chat_tables.py` sur Render :

```python
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Lire le script SQL
with open('/opt/render/project/src/scripts/create_chat_tables_postgresql.sql', 'r') as f:
    sql_script = f.read()

# Connexion à la base de données
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Exécuter le script
cursor.execute(sql_script)

cursor.close()
conn.close()
print("✅ Tables chat créées avec succès")
```

## ✅ Vérification

Après l'exécution, vérifiez que les tables existent :

```sql
-- Dans psql
\dt chat_*

-- Ou avec une requête
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'chat_%'
ORDER BY table_name;
```

Vous devriez voir :
- `chat_rooms`
- `chat_room_members`
- `chat_messages`
- `chat_attachments`
- `chat_message_reads`

## 🔄 Idempotence

Le script est **idempotent** : il peut être exécuté plusieurs fois sans erreur. Il vérifie l'existence des tables avant de les créer.

## 📌 Notes importantes

1. **Types ENUM** : Le script crée automatiquement les types ENUM nécessaires (`room_type`, `member_role`, `message_type`)

2. **Foreign Keys** : Toutes les clés étrangères sont correctement configurées avec les actions `ON DELETE` et `ON UPDATE` appropriées

3. **Index** : Tous les index nécessaires sont créés pour optimiser les performances

4. **Compatibilité** : Ce script est spécifique à PostgreSQL et utilise `BIGSERIAL` au lieu de `BIGINT UNSIGNED AUTO_INCREMENT`

## 🐛 Dépannage

### Erreur : "type already exists"
- **Cause** : Le type ENUM existe déjà
- **Solution** : C'est normal, le script gère cela automatiquement

### Erreur : "relation already exists"
- **Cause** : La table existe déjà
- **Solution** : C'est normal, le script vérifie l'existence avant de créer

### Erreur : "permission denied"
- **Cause** : L'utilisateur n'a pas les permissions nécessaires
- **Solution** : Vérifiez que vous utilisez un utilisateur avec les droits `CREATE TABLE`

## 📚 Ressources

- [Documentation PostgreSQL CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)
- [Documentation PostgreSQL ENUM](https://www.postgresql.org/docs/current/datatype-enum.html)

