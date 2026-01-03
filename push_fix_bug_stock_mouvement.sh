#!/bin/bash
# Script pour pousser la correction du bug de vérification du stock

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py CORRECTION_BUG_STOCK_MOUVEMENT.md

echo ""
echo "📝 Création du commit..."
git commit -m "Fix: Correction bug vérification stock disponible dans mouvements

🐛 PROBLÈME
- Le système indiquait 'Stock insuffisant' même quand il y avait du stock
- Erreur: 'Stock insuffisant à la source pour X (disponible: 0, requis: 5)'
- Le magasinier ne pouvait pas créer de mouvement de stock

🔍 CAUSE
- La vérification 'if not source_stock:' était en dehors du bloc 'if from_depot_id:'
- Si from_depot_id n'était pas défini, source_stock n'était jamais initialisé
- Cela créait un nouveau DepotStock avec quantité 0 au lieu de récupérer le stock existant
- Pas de 'elif' entre from_depot_id et from_vehicle_id, causant des conflits

✅ SOLUTION
- Initialisation explicite de source_stock = None au début
- Utilisation de 'elif' pour from_vehicle_id
- Toutes les vérifications sont maintenant dans les blocs appropriés
- Ajout d'un 'else' pour gérer le cas où aucune source n'est définie
- Même correction appliquée pour la destination

📋 FICHIERS MODIFIÉS
- stocks.py (lignes 974-1052)
  * Correction vérification stock source
  * Correction mise à jour stock destination

✅ RÉSULTAT
- Le système détecte correctement le stock disponible
- Les mouvements peuvent être créés sans erreur si le stock est suffisant
- Les erreurs ne s'affichent que lorsque le stock est réellement insuffisant"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Correction poussée avec succès!"
echo ""
echo "📋 Documentation disponible dans: CORRECTION_BUG_STOCK_MOUVEMENT.md"

