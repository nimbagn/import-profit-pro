# 🔍 Vérifier DATABASE_URL dans Render

## ❌ Erreur Actuelle

```
Can't connect to MySQL server on '127.0.0.1'
```

Cela signifie que `DATABASE_URL` n'est **PAS configurée** dans Render, ou que le code n'a pas été redéployé.

## ✅ Solution : Vérifier et Configurer DATABASE_URL

### Étape 1 : Vérifier dans Render Dashboard

1. Allez dans **Render Dashboard** → Votre service `import-profit-pro`
2. Cliquez sur **"Environment"** (ou **"Settings"** → **"Environment Variables"**)
3. **Vérifiez** si `DATABASE_URL` existe

### Étape 2 : Si DATABASE_URL N'Existe Pas

1. **Allez dans** votre base PostgreSQL sur Render
2. **Copiez l'Internal Database URL**
   - Elle ressemble à : `postgresql://user:password@host:port/database`
3. **Dans votre service**, ajoutez la variable :
   - **Key** : `DATABASE_URL`
   - **Value** : Collez l'Internal Database URL
4. **Sauvegardez**

### Étape 3 : Vérifier le Format

L'URL doit :
- ✅ Commencer par `postgresql://`
- ✅ Contenir le user, password, host, port et database
- ✅ Ne pas avoir d'espaces

**Exemple correct :**
```
postgresql://madargn_user:MZLbNLbtHYJcsSaBlz3loO99ZlGIAor9@dpg-d59ao91r0fns73fmi85g-a.virginia-postgres.render.com/madargn
```

### Étape 4 : Redéployer

Après avoir ajouté/modifié `DATABASE_URL` :

1. **Render redéploiera automatiquement**
2. **OU** cliquez sur **"Manual Deploy"** pour forcer le redéploiement

### Étape 5 : Vérifier les Logs

Dans les logs de démarrage, vous devriez voir :
```
✅ Configuration PostgreSQL: dpg-xxxxx.render.com/madargn
```

Au lieu de :
```
✅ Configuration MySQL: 127.0.0.1:3306/madargn
```

## 🆘 Si DATABASE_URL Est Déjà Configurée

Si `DATABASE_URL` est déjà configurée mais que l'erreur persiste :

1. **Vérifiez** que le code a été poussé sur GitHub
2. **Vérifiez** que Render a redéployé (dernier commit visible)
3. **Vérifiez** les logs pour voir quelle URL est utilisée
4. **Redéployez manuellement** si nécessaire

## 📋 Checklist

- [ ] `DATABASE_URL` existe dans Render Environment
- [ ] `DATABASE_URL` commence par `postgresql://`
- [ ] `DATABASE_URL` contient l'Internal Database URL (pas l'externe)
- [ ] Le code a été poussé sur GitHub (commit `e36b447`)
- [ ] Render a redéployé avec le nouveau code
- [ ] Les logs montrent "Configuration PostgreSQL"

---

**Vérifiez que DATABASE_URL est bien configurée dans Render avec l'Internal Database URL !**

