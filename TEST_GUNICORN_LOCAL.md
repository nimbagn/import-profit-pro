# 🧪 Tester avec Gunicorn Localement

Pour tester que votre application fonctionne avec Gunicorn avant de déployer sur Render.

## Installation de Gunicorn

```bash
# Si vous êtes dans votre environnement virtuel
pip install gunicorn

# OU si vous avez des problèmes de permissions
python3 -m pip install gunicorn
```

## Test Simple

```bash
# Depuis le répertoire du projet
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

Ouvrez http://localhost:5000 dans votre navigateur.

## Test avec Configuration Production

```bash
# Avec plusieurs workers (comme en production)
gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app

# Avec timeout augmenté (pour les requêtes longues)
gunicorn --workers 3 --timeout 120 --bind 0.0.0.0:5000 wsgi:app
```

## Arrêter Gunicorn

Appuyez sur `Ctrl+C` dans le terminal.

---

**Note :** Si vous ne pouvez pas installer Gunicorn localement, ce n'est pas grave ! Render l'installera automatiquement depuis `requirements.txt` lors du déploiement.

