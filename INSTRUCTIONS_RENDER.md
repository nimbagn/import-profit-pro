# 🚀 Instructions Rapides - Déploiement Render

## ⚠️ IMPORTANT : Exécution du Script SQL

### Méthode Recommandée : Éditeur SQL de Render

1. **Allez dans votre base PostgreSQL sur Render**
2. **Cliquez sur "Connect"** → **"SQL Editor"**
3. **Ouvrez le fichier** : `scripts/migration_postgresql_render_complete.sql`
4. **Copiez TOUT le contenu** du fichier
5. **Collez dans l'éditeur SQL** de Render
6. **Cliquez sur "Run"**

✅ **C'est la méthode la plus simple et la plus fiable !**

---

### Méthode Alternative : Via Terminal (si vous avez accès SSH)

Si vous avez accès SSH à votre service Render :

```bash
# 1. Définir DATABASE_URL (copiez depuis Render Dashboard)
export DATABASE_URL="postgresql://user:password@host:port/database"

# 2. Exécuter le script
psql "$DATABASE_URL" -f scripts/migration_postgresql_render_complete.sql
```

**OU** utilisez le script helper :

```bash
# Rendre le script exécutable
chmod +x scripts/executer_migration_render.sh

# Exécuter
./scripts/executer_migration_render.sh
```

---

## ❌ Erreur à Éviter

**NE PAS utiliser** cette syntaxe (causera une erreur) :
```bash
psql <URL> < script.sql  # ❌ INCORRECT
```

**Utiliser** cette syntaxe :
```bash
psql "$DATABASE_URL" -f script.sql  # ✅ CORRECT
```

---

## 📝 Checklist Rapide

1. [ ] Base PostgreSQL créée sur Render
2. [ ] Script SQL exécuté via l'éditeur SQL de Render
3. [ ] Service web créé et lié à la base de données
4. [ ] Application accessible
5. [ ] Utilisateur admin créé via `/init-db`

---

**Pour plus de détails, consultez `GUIDE_DEPLOIEMENT_RENDER.md`**

