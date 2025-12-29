# Guide de Recalcul des Écarts d'Inventaire

## Problème
La formule de calcul de l'écart a été corrigée :
- **Ancienne formule** : `ÉCART = QUANTITÉ COMPTÉE - STOCK ACTUEL`
- **Nouvelle formule** : `ÉCART = STOCK ACTUEL - (QUANTITÉ COMPTÉE + PILE)`

## Solution

### Option 1 : Script SQL (Recommandé)

Exécutez le script SQL directement dans MySQL :

```bash
mysql -u root -p madargn < scripts/recalculate_inventory_variances.sql
```

Ou connectez-vous à MySQL et exécutez le script :

```bash
mysql -u root -p
```

Puis dans MySQL :

```sql
USE madargn;
SOURCE scripts/recalculate_inventory_variances.sql;
```

### Option 2 : Script Python

Si vous avez les bonnes credentials MySQL configurées, vous pouvez utiliser le script Python :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
DB_NAME=madargn python3 scripts/recalculate_inventory_variances.py
```

**Note** : Le script Python nécessite que les variables d'environnement `DB_USER` et `DB_PASSWORD` soient correctement configurées, ou que le fichier `config.py` contienne les bonnes credentials.

### Option 3 : Exécution manuelle SQL

Si vous préférez exécuter manuellement, voici la commande SQL :

```sql
USE madargn;

-- Mettre à jour tous les écarts avec la nouvelle formule
UPDATE inventory_details
SET variance = system_quantity - counted_quantity;
```

## Vérification

Après l'exécution, vérifiez les résultats sur la page `/inventory/sessions/1` pour confirmer que les écarts sont correctement calculés.

## Notes

- Les nouveaux détails d'inventaire créés après cette correction utiliseront automatiquement la nouvelle formule.
- Ce script ne modifie que les écarts existants qui ont été calculés avec l'ancienne formule.
- La quantité comptée inclut déjà la pile si elle a été calculée à partir des dimensions de pile.

