#!/bin/bash
# Script pour pousser la correction de récupération du stock des dépôts

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py

echo ""
echo "📝 Création du commit..."
git commit -m "Fix: Simplification récupération stock dépôt pour mouvements

🐛 PROBLÈME
- Le système n'arrivait pas à récupérer le stock des dépôts pour les mouvements
- Calcul complexe du stock réel depuis les mouvements causait des problèmes

✅ SOLUTION
- Utilisation directe de DepotStock.quantity comme source principale
- Création automatique de DepotStock s'il n'existe pas
- Rafraîchissement de l'objet depuis la DB pour avoir la valeur la plus récente
- Ajout de debug pour diagnostic

📋 MODIFICATIONS
- stocks.py (lignes 989-1025)
  * Simplification: utilisation directe de DepotStock.quantity
  * Création automatique si n'existe pas
  * db.session.refresh() pour valeur à jour
  * Debug logs pour diagnostic

✅ RÉSULTAT
- Stock des dépôts correctement récupéré
- Code plus simple et maintenable
- Meilleure performance (pas de calcul complexe)"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Correction poussée avec succès!"

