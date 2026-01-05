# ⚡ Exécution Migration Messaging sur Render

## ❌ Erreur
Vous avez essayé d'exécuter le script SQL directement dans bash, mais c'est du code PostgreSQL qui doit être exécuté via `psql`.

## ✅ Solution : Utiliser psql

### Option 1 : Exécuter le fichier SQL avec psql (RECOMMANDÉ)

```bash
# 1. Vérifiez que vous êtes dans le bon répertoire
cd ~/project/src

# 2. Vérifiez que DATABASE_URL est définie
echo $DATABASE_URL

# 3. Si DATABASE_URL n'est pas définie, définissez-la
# (Copiez l'Internal Database URL depuis Render Dashboard → Connect)
export DATABASE_URL="postgresql://user:password@host:port/database"

# 4. Exécutez le script avec psql
psql "$DATABASE_URL" -f scripts/add_messaging_permission_supervisor_postgresql.sql
```

### Option 2 : Copier-coller dans psql interactif

```bash
# 1. Connectez-vous à la base avec psql
psql "$DATABASE_URL"

# 2. Une fois dans psql (vous verrez "madargn=>"), copiez-collez le contenu du script
# (Tout le bloc DO $$ ... END $$; et la requête SELECT)

# 3. Appuyez sur Entrée pour exécuter

# 4. Pour quitter psql, tapez :
\q
```

### Option 3 : Utiliser l'éditeur SQL de Render (LE PLUS SIMPLE)

1. Allez sur [https://dashboard.render.com](https://dashboard.render.com)
2. Cliquez sur votre base PostgreSQL
3. Cliquez sur **"Connect"** → **"SQL Editor"**
4. Ouvrez le fichier : `scripts/add_messaging_permission_supervisor_postgresql.sql`
5. **Copiez TOUT le contenu** du fichier
6. **Collez dans l'éditeur SQL** de Render
7. Cliquez sur **"Run"**

✅ **C'est la méthode la plus simple et la plus fiable !**

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
cat scripts/add_messaging_permission_supervisor_postgresql.sql

# Tester la connexion à la base
psql "$DATABASE_URL" -c "SELECT version();"

# Vérifier les permissions actuelles du superviseur
psql "$DATABASE_URL" -c "SELECT code, name, permissions->'messaging' FROM roles WHERE code = 'supervisor';"
```

---

## ✅ Vérification après exécution

Après avoir exécuté le script, vérifiez que les permissions ont été ajoutées :

```bash
psql "$DATABASE_URL" -c "SELECT code, name, permissions->'messaging' as messaging_perms FROM roles WHERE code = 'supervisor';"
```

Vous devriez voir :
```
code       | name        | messaging_perms
-----------|-------------|----------------------------------------------------
supervisor | Superviseur | ["read", "send_sms", "send_whatsapp", "send_otp", "manage_contacts"]
```

---

## 🎯 Résumé des commandes

**Pour exécuter le script :**
```bash
psql "$DATABASE_URL" -f scripts/add_messaging_permission_supervisor_postgresql.sql
```

**Pour vérifier :**
```bash
psql "$DATABASE_URL" -c "SELECT permissions->'messaging' FROM roles WHERE code = 'supervisor';"
```

---

**💡 Astuce** : Utilisez l'éditeur SQL de Render (Option 3) - c'est le plus simple et évite tous les problèmes de terminal !

