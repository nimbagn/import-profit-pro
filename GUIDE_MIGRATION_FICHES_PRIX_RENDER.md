# Guide : Exécuter la Migration Fiches de Prix sur Render

## 🎯 Problème
Les articles de stock sont importés avec succès, mais ils n'apparaissent pas dans les fiches de prix car la migration de la base de données n'a pas encore été exécutée.

## ✅ Solution : Exécuter la Migration

### Option 1 : Script Python (Recommandé)

1. **Se connecter au Shell Render** :
   - Aller sur https://dashboard.render.com
   - Sélectionner votre service
   - Cliquer sur "Shell"

2. **Exécuter le script de migration** :
```bash
cd /opt/render/project/src
python3 scripts/executer_migration_price_list_items_postgresql.py
```

### Option 2 : SQL Direct

1. **Se connecter au Shell Render**

2. **Se connecter à PostgreSQL** :
```bash
cd /opt/render/project/src
python3
```

3. **Dans Python, exécuter** :
```python
from app import app, db
from sqlalchemy import text

with app.app_context():
    # Lire et exécuter le script SQL
    with open('scripts/migrer_price_list_items_vers_stock_items_postgresql.sql', 'r') as f:
        sql_script = f.read()
    
    # Exécuter chaque commande
    for statement in sql_script.split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                db.session.execute(text(statement))
                db.session.commit()
                print(f"✅ Exécuté: {statement[:50]}...")
            except Exception as e:
                print(f"⚠️  Erreur: {e}")
                db.session.rollback()
```

### Option 3 : Vérification Rapide

Pour vérifier l'état actuel de la table :

```bash
cd /opt/render/project/src
python3
```

```python
from app import app, db
from sqlalchemy import text, inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('price_list_items')
    print("Colonnes actuelles de price_list_items:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
```

## 🔍 Vérification Post-Migration

Après la migration, vérifiez que :
- ✅ La colonne `stock_item_id` existe
- ✅ La colonne `article_id` n'existe plus
- ✅ Les contraintes sont correctes

## ⚠️ Important

**Cette migration supprime toutes les données existantes dans `price_list_items`** car il n'y a pas de correspondance directe entre `Article` et `StockItem`.

Les utilisateurs devront recréer leurs fiches de prix avec les articles de stock.

## 🚀 Après la Migration

1. Tester la création d'une nouvelle fiche de prix
2. Vérifier que les articles de stock s'affichent dans le sélecteur
3. Créer une fiche de prix avec des articles de stock
4. Vérifier que les prix s'affichent correctement

