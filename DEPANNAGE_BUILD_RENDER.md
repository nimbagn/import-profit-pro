# 🔧 Dépannage - Erreur de Build sur Render

## ❌ Erreur Rencontrée

```
Exited with status 1 while building your code.
```

## 🔍 Causes Possibles et Solutions

### 1. Vérifier les Logs de Build

**Dans Render Dashboard :**
1. Allez dans votre service
2. Cliquez sur l'onglet **"Logs"**
3. Faites défiler jusqu'au début du build
4. Cherchez les erreurs en rouge

Les erreurs courantes sont affichées dans les logs.

---

### 2. Problème avec requirements.txt

**Erreur possible :** `ERROR: Could not find a version that satisfies the requirement...`

**Solution :**
- Vérifiez que toutes les dépendances sont correctes
- Certaines versions peuvent ne pas être disponibles

**Test local :**
```bash
pip install -r requirements.txt
```

---

### 3. Problème avec le Build Command

**Vérifiez dans Render :**
- **Build Command** doit être : `pip install -r requirements.txt`

**Si vous avez besoin d'une commande différente :**
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

---

### 4. Problème avec le Start Command

**Vérifiez dans Render :**
- **Start Command** doit être : `gunicorn wsgi:app`

**Alternatives si problème :**
```bash
gunicorn --bind 0.0.0.0:$PORT wsgi:app
```

---

### 5. Problème avec psycopg2-binary

**Erreur possible :** `Error installing psycopg2-binary`

**Solution :**
Si `psycopg2-binary` pose problème, essayez `psycopg2` à la place :

Dans `requirements.txt`, remplacez :
```
psycopg2-binary>=2.9.9
```

Par :
```
psycopg2>=2.9.9
```

**OU** ajoutez des dépendances système dans le Build Command :
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

---

### 6. Problème avec la Version Python

**Vérifiez `runtime.txt` :**
- Doit contenir : `python-3.11.0` (ou une version supportée)

**Versions supportées par Render :**
- `python-3.11.0`
- `python-3.10.0`
- `python-3.9.0`

---

### 7. Problème avec wsgi.py

**Vérifiez que `wsgi.py` existe et contient :**
```python
from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

### 8. Erreur d'Import dans app.py

**Erreur possible :** `ModuleNotFoundError` ou `ImportError`

**Solution :**
- Vérifiez que tous les imports sont corrects
- Vérifiez que tous les modules sont dans `requirements.txt`

---

## 🔧 Solutions Rapides

### Solution 1 : Build Command Amélioré

Dans Render, changez le **Build Command** pour :
```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

### Solution 2 : Vérifier les Dépendances

Assurez-vous que `requirements.txt` contient bien :
- `gunicorn>=21.2.0`
- `psycopg2-binary>=2.9.9` (ou `psycopg2`)
- Toutes les autres dépendances

### Solution 3 : Start Command avec Port

Dans Render, changez le **Start Command** pour :
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 wsgi:app
```

---

## 📋 Checklist de Vérification

- [ ] `requirements.txt` existe et est valide
- [ ] `wsgi.py` existe et importe correctement `app`
- [ ] `Procfile` existe (optionnel, Render utilise Start Command)
- [ ] `runtime.txt` existe avec une version Python valide
- [ ] Build Command : `pip install -r requirements.txt`
- [ ] Start Command : `gunicorn wsgi:app`
- [ ] Toutes les variables d'environnement sont configurées

---

## 🆘 Si Rien ne Fonctionne

1. **Consultez les logs détaillés** dans Render
2. **Testez localement** :
   ```bash
   pip install -r requirements.txt
   gunicorn wsgi:app
   ```
3. **Vérifiez la documentation Render** : https://render.com/docs

---

## 📝 Informations à Fournir pour Aide

Si vous avez toujours des problèmes, fournissez :
1. Les **logs complets** du build (copier-coller)
2. Le contenu de `requirements.txt`
3. Le contenu de `wsgi.py`
4. Les commandes Build et Start configurées dans Render

---

**Consultez les logs dans Render Dashboard pour voir l'erreur exacte !**

