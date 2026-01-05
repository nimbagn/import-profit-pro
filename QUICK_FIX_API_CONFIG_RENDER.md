# ⚡ Solution Rapide : Exécuter le Script SQL sur Render

## ❌ Erreur Commune

Vous avez essayé d'exécuter du SQL directement dans le shell bash, ce qui ne fonctionne pas. Le SQL doit être exécuté via `psql` ou le SQL Editor.

## ✅ Solution 1 : SQL Editor (LE PLUS SIMPLE)

1. **Allez sur Render Dashboard** : https://dashboard.render.com
2. **Sélectionnez votre base de données PostgreSQL**
3. **Cliquez sur l'onglet "SQL Editor"** (ou "Query" selon la version)
4. **Copiez-collez TOUT le contenu** du fichier `scripts/create_api_configs_table_postgresql.sql`
5. **Cliquez sur "Run"** ou "Execute"

C'est tout ! ✅

## ✅ Solution 2 : Via psql (Ligne de commande)

Si vous êtes dans le shell Render et avez accès à `psql` :

```bash
# D'abord, récupérez la DATABASE_URL depuis Render Dashboard
# Puis exécutez :
psql $DATABASE_URL -f scripts/create_api_configs_table_postgresql.sql
```

**OU** si vous avez le fichier localement :

```bash
# Copiez le contenu du script dans un fichier temporaire
cat > /tmp/create_api_configs.sql << 'EOF'
[COLLER ICI LE CONTENU DU SCRIPT]
EOF

# Puis exécutez :
psql $DATABASE_URL -f /tmp/create_api_configs.sql
```

## ✅ Solution 3 : Exécution Directe avec psql

Si vous voulez exécuter directement depuis le shell :

```bash
# Connectez-vous à psql
psql $DATABASE_URL

# Puis dans psql, exécutez :
\i scripts/create_api_configs_table_postgresql.sql

# OU copiez-collez le contenu du script directement dans psql
```

## 📋 Contenu du Script à Exécuter

Le fichier `scripts/create_api_configs_table_postgresql.sql` contient :

```sql
-- Créer la table api_configs
CREATE TABLE IF NOT EXISTS api_configs (
    id BIGSERIAL PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL UNIQUE,
    api_secret TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    updated_by_id BIGINT
);

-- Créer les index
CREATE INDEX IF NOT EXISTS idx_apiconfig_name ON api_configs(api_name);
CREATE INDEX IF NOT EXISTS idx_apiconfig_active ON api_configs(is_active);

-- Ajouter la contrainte de clé étrangère
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE api_configs 
        ADD CONSTRAINT fk_apiconfig_updated_by 
        FOREIGN KEY (updated_by_id) 
        REFERENCES users(id) 
        ON UPDATE CASCADE 
        ON DELETE SET NULL;
        RAISE NOTICE '✅ Contrainte FK updated_by_id ajoutée';
    ELSE
        RAISE WARNING '⚠️ Table users n''existe pas encore, contrainte FK updated_by_id ignorée';
    END IF;
END $$;

-- Commentaires
COMMENT ON TABLE api_configs IS 'Configuration des APIs externes (Message Pro, etc.)';
COMMENT ON COLUMN api_configs.api_name IS 'Nom de l''API (ex: messagepro)';
COMMENT ON COLUMN api_configs.api_secret IS 'Clé secrète de l''API';
COMMENT ON COLUMN api_configs.is_active IS 'Indique si la configuration est active';
COMMENT ON COLUMN api_configs.updated_by_id IS 'ID de l''utilisateur qui a effectué la dernière mise à jour';
```

## ⚠️ Important

- **NE PAS** copier-coller le SQL directement dans le shell bash
- **UTILISER** le SQL Editor de Render (méthode la plus simple)
- **OU** utiliser `psql` avec l'option `-f` pour exécuter un fichier

## ✅ Vérification

Après l'exécution, vérifiez que la table existe :

```sql
SELECT * FROM api_configs;
```

Ou via psql :

```bash
psql $DATABASE_URL -c "SELECT * FROM api_configs;"
```

