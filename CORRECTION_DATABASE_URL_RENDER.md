# 🔧 Correction - Erreur Connexion Base de Données

## ❌ Erreur

```
Can't connect to MySQL server on '127.0.0.1' (Connection refused)
```

## 🔍 Problème

L'application essaie de se connecter à **MySQL local** (`127.0.0.1`) au lieu d'utiliser **PostgreSQL via DATABASE_URL** sur Render.

## ✅ Solution : Vérifier DATABASE_URL dans Render

### Étape 1 : Vérifier dans Render Dashboard

1. Allez dans **Render Dashboard** → Votre service → **Environment**
2. Vérifiez que **`DATABASE_URL`** est bien configurée
3. L'URL doit commencer par : `postgresql://...`

### Étape 2 : Vérifier le Format de DATABASE_URL

L'URL doit ressembler à :
```
postgresql://user:password@host:port/database
```

**Exemple :**
```
postgresql://madargn_user:MZLbNLbtHYJcsSaBlz3loO99ZlGIAor9@dpg-d59ao91r0fns73fmi85g-a.virginia-postgres.render.com/madargn
```

### Étape 3 : Vérifier que DATABASE_URL est Prioritaire

Dans `config.py`, l'ordre de priorité est :
1. `DATABASE_URL` (si défini) ← **Doit être utilisé**
2. Variables `DB_*` (MySQL)
3. SQLite (fallback)

## 🔧 Actions à Faire

### Dans Render Dashboard :

1. **Allez dans** votre service → **Environment**
2. **Vérifiez** que `DATABASE_URL` existe et est correcte
3. **Si elle n'existe pas**, ajoutez-la :
   - **Key** : `DATABASE_URL`
   - **Value** : L'**Internal Database URL** de votre base PostgreSQL Render
4. **Redéployez** le service

### Vérifier l'URL de la Base de Données

1. Dans Render Dashboard → Votre base PostgreSQL
2. Copiez l'**Internal Database URL**
3. Assurez-vous qu'elle commence par `postgresql://`

## 🆘 Si DATABASE_URL est Déjà Configurée

Si `DATABASE_URL` est déjà configurée mais que l'erreur persiste :

1. **Vérifiez les logs** pour voir quelle URL est utilisée
2. **Vérifiez** que l'URL ne contient pas d'espaces
3. **Vérifiez** que le mot de passe dans l'URL est correctement encodé
4. **Redéployez** après modification

## ✅ Vérification

Après correction, dans les logs vous devriez voir :
```
✅ Configuration PostgreSQL: dpg-xxxxx.render.com/madargn
```

Au lieu de :
```
✅ Configuration MySQL: 127.0.0.1:3306/madargn
```

---

**Vérifiez que DATABASE_URL est bien configurée dans Render avec l'Internal Database URL de PostgreSQL !**

