# ⚡ Correction Rapide : Exécution du Script SQL sur Render

## ❌ Erreur
Vous avez essayé d'exécuter le script SQL directement dans bash, mais c'est du code PostgreSQL qui doit être exécuté via `psql`.

## ✅ Solution : Utiliser psql

### Option 1 : Exécuter le fichier SQL avec psql

```bash
# 1. Vérifiez que vous êtes dans le bon répertoire
cd ~/project/src

# 2. Vérifiez que DATABASE_URL est définie
echo $DATABASE_URL

# 3. Si DATABASE_URL n'est pas définie, définissez-la
# (Copiez l'Internal Database URL depuis Render Dashboard)
export DATABASE_URL="postgresql://user:password@host:port/database"

# 4. Exécutez le script avec psql
psql "$DATABASE_URL" -f scripts/add_price_lists_permission_supervisor_postgresql.sql
```

### Option 2 : Copier-coller dans psql interactif

```bash
# 1. Connectez-vous à la base avec psql
psql "$DATABASE_URL"

# 2. Une fois dans psql, copiez-collez le contenu du script
# (Tout le bloc DO $$ ... END $$; et la requête SELECT)

# 3. Appuyez sur Entrée pour exécuter

# 4. Pour quitter psql, tapez :
\q
```

### Option 3 : Utiliser l'éditeur SQL de Render (RECOMMANDÉ)

1. Allez sur [https://dashboard.render.com](https://dashboard.render.com)
2. Cliquez sur votre base PostgreSQL
3. Cliquez sur **"Connect"** → **"SQL Editor"**
4. Copiez-collez le contenu de `scripts/add_price_lists_permission_supervisor_postgresql.sql`
5. Cliquez sur **"Run"**

✅ **C'est la méthode la plus simple !**

---

## 🔍 Vérifier DATABASE_URL

```bash
# Vérifier si DATABASE_URL est définie
echo $DATABASE_URL

# Si vide, la définir (copiez depuis Render Dashboard)
export DATABASE_URL="postgresql://user:password@host:port/database"
```

---

## 📝 Commandes utiles

```bash
# Voir les fichiers SQL disponibles
ls -la scripts/*.sql

# Vérifier le contenu du script
cat scripts/add_price_lists_permission_supervisor_postgresql.sql

# Tester la connexion à la base
psql "$DATABASE_URL" -c "SELECT version();"
```

