# 🔧 Guide : Mise à jour des permissions superviseur sur Render

## 📋 Objectif
Ajouter les permissions `price_lists` (view, create, edit, delete) au rôle superviseur sur votre base PostgreSQL Render.

---

## 🎯 Méthode 1 : Éditeur SQL de Render (RECOMMANDÉ)

### Étapes :

1. **Connectez-vous à votre dashboard Render**
   - Allez sur [https://dashboard.render.com](https://dashboard.render.com)

2. **Accédez à votre base PostgreSQL**
   - Dans la liste des services, cliquez sur votre base de données PostgreSQL
   - Exemple : `import-profit-db` ou `madargn`

3. **Ouvrez l'éditeur SQL**
   - Cliquez sur l'onglet **"Connect"** dans le menu latéral
   - Cliquez sur **"SQL Editor"**

4. **Copiez le script SQL**
   - Ouvrez le fichier : `scripts/add_price_lists_permission_supervisor_postgresql.sql`
   - **Sélectionnez TOUT le contenu** (Ctrl+A / Cmd+A)
   - **Copiez** (Ctrl+C / Cmd+C)

5. **Collez dans l'éditeur SQL**
   - Dans l'éditeur SQL de Render, **collez** le script (Ctrl+V / Cmd+V)
   - Vous devriez voir le script complet avec le bloc `DO $$ ... END $$;`

6. **Exécutez le script**
   - Cliquez sur le bouton **"Run"** ou **"Execute"**
   - Attendez la confirmation d'exécution

7. **Vérifiez le résultat**
   - Vous devriez voir un message de succès
   - La requête de vérification en bas du script affichera les permissions ajoutées

---

## 🖥️ Méthode 2 : Via Terminal (SSH) - Si disponible

Si vous avez accès SSH à votre service Render :

### Étapes :

1. **Connectez-vous via SSH**
```bash
   # Depuis votre terminal local
   ssh render@votre-service-render
   ```

2. **Naviguez vers le projet**
   ```bash
   cd ~/project/src
   ```

3. **Définissez la variable DATABASE_URL**
   ```bash
   # Copiez l'Internal Database URL depuis Render Dashboard
   export DATABASE_URL="postgresql://user:password@host:port/database"
   ```

4. **Exécutez le script**
   ```bash
   psql "$DATABASE_URL" -f scripts/add_price_lists_permission_supervisor_postgresql.sql
   ```

5. **Vérifiez le résultat**
   - Le script affichera un message de succès
   - La requête de vérification affichera les permissions

---

## ✅ Vérification manuelle

Pour vérifier que les permissions ont été ajoutées :

### Via l'éditeur SQL de Render :

```sql
SELECT 
    code, 
    name,
    permissions->'price_lists' as price_lists_permissions 
FROM roles 
WHERE code = 'supervisor';
```

**Résultat attendu :**
```
code       | name        | price_lists_permissions
-----------|-------------|------------------------
supervisor | Superviseur | ["view", "create", "edit", "delete"]
```

---

## 🔍 Dépannage

### Erreur : "Rôle superviseur non trouvé"

**Cause** : Le rôle superviseur n'existe pas encore dans votre base.

**Solution** : 
1. Vérifiez que le script de migration initial a été exécuté
2. Si le rôle n'existe pas, créez-le d'abord :

```sql
INSERT INTO roles (code, name, permissions, is_active) 
VALUES (
    'supervisor', 
    'Superviseur', 
    '{"stocks": ["read"], "inventory": ["read", "validate"], "vehicles": ["read", "update"], "reports": ["read"], "regions": ["read"], "depots": ["read"], "families": ["read"], "stock_items": ["read"], "promotion": ["read", "write"], "orders": ["read", "validate", "update"], "price_lists": ["view", "create", "edit", "delete"]}'::jsonb,
    TRUE
)
ON CONFLICT (code) DO UPDATE 
SET permissions = roles.permissions || '{"price_lists": ["view", "create", "edit", "delete"]}'::jsonb;
```

### Erreur : "permission denied"

**Cause** : Vous n'avez pas les droits d'écriture sur la base.

**Solution** : 
- Vérifiez que vous utilisez le bon utilisateur (celui avec les droits d'écriture)
- Contactez l'administrateur de la base si nécessaire

---

## 📝 Contenu du script

Le script `add_price_lists_permission_supervisor_postgresql.sql` :

1. **Récupère** les permissions actuelles du rôle superviseur
2. **Ajoute** les permissions `price_lists` : `["view", "create", "edit", "delete"]`
3. **Met à jour** le rôle dans la base de données
4. **Affiche** un message de confirmation
5. **Vérifie** le résultat avec une requête SELECT

---

## 🎉 Après la mise à jour

Une fois le script exécuté avec succès :

1. **Les utilisateurs superviseur** peuvent maintenant :
   - ✅ Accéder à `/price-lists/`
   - ✅ Créer de nouvelles listes de prix
   - ✅ Modifier les listes existantes
   - ✅ Supprimer les listes de prix

2. **Testez l'accès** :
   - Connectez-vous avec un compte superviseur
   - Allez sur `http://votre-app-render.onrender.com/price-lists/`
   - Vous devriez pouvoir voir et gérer les listes de prix

---

## 📚 Fichiers concernés

- `scripts/add_price_lists_permission_supervisor_postgresql.sql` - Script PostgreSQL
- `scripts/add_price_lists_permission_supervisor.sql` - Script MySQL (si besoin)
- `app.py` - Définition des rôles (pour nouvelles installations)

---

**💡 Astuce** : La méthode 1 (éditeur SQL) est la plus simple et la plus fiable. Utilisez-la si possible !
