# ✅ Utiliser la Route /init

## 🌐 URL Correcte

Oui, l'URL est **correcte** :

```
https://import-profit-pro.onrender.com/init
```

## 📋 Ce que Fait Cette Route

Quand vous accédez à cette URL, elle :

1. ✅ **Crée toutes les tables** dans PostgreSQL
2. ✅ **Crée le rôle admin** (si n'existe pas)
3. ✅ **Crée l'utilisateur admin** (si n'existe pas)
4. ✅ **Affiche un message de confirmation** avec les identifiants

## 🚀 Étapes

### 1. Accéder à l'URL

Ouvrez dans votre navigateur :
```
https://import-profit-pro.onrender.com/init
```

### 2. Attendre la Réponse

Vous verrez soit :

**Si c'est la première fois :**
```
✅ Base de données initialisée!

Identifiants de connexion:
- Username: admin
- Password: admin123

⚠️ IMPORTANT: Changez le mot de passe après la première connexion!
[Se connecter]
```

**Si déjà initialisé :**
```
ℹ️ Base de données déjà initialisée
L'utilisateur admin existe déjà.
[Se connecter]
```

### 3. Se Connecter

Cliquez sur **"Se connecter"** ou allez sur :
```
https://import-profit-pro.onrender.com/auth/login
```

Utilisez :
- **Username** : `admin`
- **Password** : `admin123`

## ⚠️ Important

1. **Exécutez `/init` UNE SEULE FOIS** après le déploiement
2. **Changez le mot de passe** après la première connexion
3. **Assurez-vous** que `DATABASE_URL` est bien configurée dans Render

## 🆘 Si Ça Ne Fonctionne Pas

### Erreur 500 ou Erreur de Connexion

1. **Vérifiez les logs** dans Render Dashboard
2. **Vérifiez** que `DATABASE_URL` est configurée
3. **Vérifiez** que la base PostgreSQL est active

### Erreur "Table already exists"

C'est normal si vous avez déjà exécuté `/init`. L'utilisateur admin devrait déjà exister.

### Erreur de Connexion à la Base

Vérifiez que :
- `DATABASE_URL` est bien configurée dans Render
- La base PostgreSQL est active
- L'URL commence par `postgresql://`

---

**Oui, l'URL est correcte ! Accédez-y pour initialiser la base de données ! 🚀**

