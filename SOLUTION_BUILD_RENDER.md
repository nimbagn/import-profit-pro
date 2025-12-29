# 🔧 Solution Erreur de Build Render

## 🔍 Diagnostic Immédiat

Pour trouver l'erreur exacte :

1. **Dans Render Dashboard** → Votre service → Onglet **"Logs"**
2. **Faites défiler jusqu'au début** du build
3. **Cherchez les lignes en rouge** avec "ERROR" ou "FAILED"
4. **Copiez l'erreur complète**

## 🎯 Solutions Courantes

### Solution 1 : Build Command Amélioré

Dans Render, allez dans **Settings** → **Build Command** et changez pour :

```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

### Solution 2 : Start Command avec Port Explicite

Dans Render, allez dans **Settings** → **Start Command** et changez pour :

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 wsgi:app
```

### Solution 3 : Vérifier psycopg2-binary

Si l'erreur concerne `psycopg2-binary`, essayez de le remplacer dans `requirements.txt` :

**Option A :** Utiliser `psycopg2` au lieu de `psycopg2-binary`
```
psycopg2>=2.9.9
```

**Option B :** Ajouter des dépendances système dans le Build Command :
```bash
apt-get update && apt-get install -y libpq-dev python3-dev && pip install --upgrade pip && pip install -r requirements.txt
```

### Solution 4 : Vérifier la Version Python

Assurez-vous que `runtime.txt` contient une version supportée :
```
python-3.11.0
```

Ou essayez :
```
python-3.10.0
```

### Solution 5 : Erreur d'Import

Si l'erreur est `ModuleNotFoundError` ou `ImportError`, vérifiez que :
- Tous les modules sont dans `requirements.txt`
- Aucun import local ne manque
- Les chemins d'import sont corrects

## 📋 Checklist Rapide

Dans Render Dashboard, vérifiez :

- [ ] **Build Command** : `pip install -r requirements.txt` (ou version améliorée)
- [ ] **Start Command** : `gunicorn wsgi:app` (ou avec $PORT)
- [ ] **Environment** : Python 3
- [ ] **Root Directory** : Vide (ou `/` si nécessaire)
- [ ] Toutes les **variables d'environnement** sont configurées

## 🔍 Erreurs Spécifiques

### "ERROR: Could not find a version that satisfies the requirement"

**Cause :** Version de package non disponible

**Solution :** Assouplir les versions dans `requirements.txt` :
```
Flask>=3.0.3  →  Flask>=3.0.0
pandas==2.2.2  →  pandas>=2.0.0
```

### "ModuleNotFoundError: No module named 'app'"

**Cause :** `wsgi.py` ne trouve pas `app.py`

**Solution :** Vérifiez que `app.py` est à la racine du projet

### "gunicorn: command not found"

**Cause :** Gunicorn non installé

**Solution :** Vérifiez que `gunicorn>=21.2.0` est dans `requirements.txt`

### "Error installing psycopg2-binary"

**Cause :** Problème de compilation

**Solution :** Utilisez `psycopg2` au lieu de `psycopg2-binary`, ou ajoutez :
```bash
apt-get update && apt-get install -y libpq-dev python3-dev
```
dans le Build Command

## 🚀 Solution Rapide Recommandée

1. **Dans Render** → Settings → **Build Command** :
   ```bash
   pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
   ```

2. **Dans Render** → Settings → **Start Command** :
   ```bash
   gunicorn --bind 0.0.0.0:$PORT --workers 2 wsgi:app
   ```

3. **Redéployez** : Render redéploiera automatiquement ou cliquez sur "Manual Deploy"

## 📞 Prochaines Étapes

1. **Consultez les logs** dans Render pour voir l'erreur exacte
2. **Appliquez la solution** correspondante ci-dessus
3. **Redéployez** et vérifiez les nouveaux logs

---

**Important :** Les logs dans Render Dashboard vous donneront l'erreur exacte. Commencez par là !

