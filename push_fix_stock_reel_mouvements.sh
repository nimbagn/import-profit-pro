#!/bin/bash
# Script pour pousser la correction du calcul du stock réel dans les mouvements

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py CORRECTION_STOCK_REEL_MOUVEMENTS.md

echo ""
echo "📝 Création du commit..."
git commit -m "Fix: Calcul du stock réel à partir des mouvements + formatage quantités

🐛 PROBLÈME
- Erreur: 'Stock insuffisant (disponible: 0, requis: 1.994)' alors qu'il y a du stock
- Quantité affichée incorrecte (1.994 au lieu de 2)
- DepotStock désynchronisé avec les mouvements réels

🔍 CAUSES
- DepotStock peut être désynchronisé avec StockMovement
- Pas de recalcul du stock réel à partir des mouvements
- Problèmes de précision décimale dans l'affichage

✅ SOLUTION
- Calcul du stock réel à partir de l'historique des mouvements
- Synchronisation automatique de DepotStock avec le stock réel
- Formatage des quantités pour éviter les décimales inutiles
- Arrondi pour la comparaison (évite problèmes de précision)

📋 MODIFICATIONS
- stocks.py (lignes 985-1045)
  * Calcul du stock réel depuis StockMovement
  * Synchronisation automatique DepotStock
  * Formatage quantités pour affichage
  * Arrondi pour comparaison

✅ RÉSULTAT
- Stock disponible correctement détecté
- Quantités correctement formatées (2 au lieu de 1.994)
- DepotStock toujours synchronisé avec les mouvements"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Correction poussée avec succès!"
echo ""
echo "📋 Documentation disponible dans: CORRECTION_STOCK_REEL_MOUVEMENTS.md"

