# Diagnostic - Stock d'Équipe Non Visible

## 🔍 Problème Signalé

L'utilisateur a effectué un approvisionnement de 1000 gammes pour l'équipe de promotion (ID: 1), mais le stock n'est pas visible sur la page `/promotion/teams/1`.

## ✅ Modifications Apportées

### 1. Amélioration de la fonction `get_team_stock()`

- ✅ Fonction simplifiée pour retourner `{gamme_id: quantity}`
- ✅ Nouvelle fonction `get_team_stock_details()` pour obtenir les détails (quantity + last_updated)
- ✅ Gestion d'erreurs améliorée avec messages de debug

### 2. Amélioration du template `team_detail.html`

- ✅ Affichage amélioré du stock avec gestion des cas vides
- ✅ Affichage de la date de dernière mise à jour
- ✅ Messages informatifs si aucun stock n'est disponible

### 3. Ajout de messages de debug

- ✅ Messages de debug après chaque approvisionnement pour vérifier l'enregistrement
- ✅ Messages de debug dans `team_detail` pour voir ce qui est récupéré

### 4. Script de vérification

- ✅ Script `scripts/verify_team_stock.py` pour vérifier directement dans la base de données

## 🔧 Diagnostic à Effectuer

### Étape 1: Vérifier les logs du serveur

Après avoir effectué un nouvel approvisionnement, vérifier les logs du serveur Flask. Vous devriez voir :

```
=== DEBUG APPROVISIONNEMENT ÉQUIPE 1 ===
✅ Stock vérifié: Gamme ID X = 1000 unités
=== FIN DEBUG ===
```

### Étape 2: Vérifier dans la base de données

Exécuter le script de vérification :

```bash
python3 scripts/verify_team_stock.py 1
```

Ou directement dans MySQL :

```sql
SELECT 
    pts.id,
    pts.team_id,
    pts.gamme_id,
    pts.quantity,
    pts.last_updated,
    pg.name as gamme_name,
    pt.name as team_name
FROM promotion_team_stock pts
LEFT JOIN promotion_gammes pg ON pts.gamme_id = pg.id
LEFT JOIN promotion_teams pt ON pts.team_id = pt.id
WHERE pts.team_id = 1;
```

### Étape 3: Vérifier la page de détail

Aller sur `/promotion/teams/1` et vérifier :
- Les messages de debug dans la console du serveur
- Si le stock s'affiche dans le tableau
- Si un message "Aucun stock enregistré" apparaît

## 🐛 Causes Possibles

### 1. Problème de commit

Si le commit n'est pas effectué correctement, le stock ne sera pas enregistré. Les messages de debug permettront de le détecter.

### 2. Problème de récupération

Si `get_team_stock()` ne récupère pas correctement les données, vérifier :
- Si la table `promotion_team_stock` existe
- Si les colonnes `team_id` et `gamme_id` sont correctes
- Si les types de données correspondent

### 3. Problème d'affichage dans le template

Si le stock est enregistré mais non affiché, vérifier :
- Si `team_stock` est bien passé au template
- Si la condition `{% if team_stock.get(gamme.id, 0) > 0 %}` est correcte
- Si la gamme existe dans la liste `gammes`

### 4. Problème de cache

Si le problème persiste, essayer :
- Rafraîchir la page (Ctrl+F5)
- Vider le cache du navigateur
- Redémarrer le serveur Flask

## 📝 Actions Correctives

### Si le stock n'est pas enregistré

1. Vérifier les logs d'erreur du serveur
2. Vérifier que la table `promotion_team_stock` existe
3. Vérifier que les contraintes de clé étrangère sont correctes
4. Vérifier que le `supervisor_id` a bien du stock disponible

### Si le stock est enregistré mais non affiché

1. Vérifier les messages de debug dans `team_detail`
2. Vérifier que la gamme existe et est active
3. Vérifier que `team_stock` contient bien les données
4. Vérifier le template pour les erreurs de syntaxe Jinja2

## 🔄 Prochaines Étapes

1. Effectuer un nouvel approvisionnement
2. Vérifier les logs du serveur
3. Vérifier la base de données directement
4. Vérifier l'affichage sur la page de détail
5. Partager les résultats pour un diagnostic plus approfondi

