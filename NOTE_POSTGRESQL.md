# 📝 Note sur PostgreSQL vs MySQL

## ✅ Votre Application Supporte les Deux !

Votre application Flask a été configurée pour supporter **PostgreSQL** et **MySQL**.

## 🎯 Sur Render

Render propose **PostgreSQL gratuitement**, pas MySQL. C'est pourquoi vous voyez PostgreSQL dans l'interface.

### Ce qui a été fait :

1. ✅ Ajout de `psycopg2-binary` dans `requirements.txt` (driver PostgreSQL)
2. ✅ Mise à jour de `config.py` pour détecter et convertir automatiquement les URLs PostgreSQL
3. ✅ Support des deux types de bases de données (MySQL et PostgreSQL)

## 🔧 Comment ça fonctionne

### Avec PostgreSQL (Render) :
```
DATABASE_URL=postgresql://user:pass@host:port/db
```
L'application convertit automatiquement en `postgresql+psycopg2://` pour SQLAlchemy.

### Avec MySQL (externe) :
```
DB_HOST=host
DB_PORT=3306
DB_NAME=madargn
DB_USER=user
DB_PASSWORD=pass
```
L'application utilise `mysql+pymysql://` pour SQLAlchemy.

## ✅ Migration des Données

Si vous avez déjà des données MySQL et voulez les migrer vers PostgreSQL :

1. **Export MySQL** : Utilisez `mysqldump` pour exporter vos données
2. **Convertir le format** : Certaines commandes SQL peuvent nécessiter des ajustements
3. **Import PostgreSQL** : Utilisez `psql` pour importer

**Note :** Pour un nouveau projet, PostgreSQL sur Render est parfait et gratuit !

## 🚀 Déploiement

Suivez simplement `DEPLOIEMENT_RENDER_RAPIDE.md` et utilisez PostgreSQL - tout fonctionnera automatiquement !

