#!/bin/bash
# Script pour pousser la correction du prix unitaire dans les réceptions

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py

echo ""
echo "📝 Création du commit..."
git commit -m "Fix: Correction unit_price_gnf NULL dans réceptions

🐛 PROBLÈME
- Erreur: Column 'unit_price_gnf' cannot be null
- Le code essayait d'insérer None pour unit_price_gnf
- Incohérence entre modèle Python (nullable=True) et DB (NOT NULL)

✅ SOLUTION
- Utilisation du prix d'achat du StockItem si prix non fourni
- Valeur par défaut 0 si aucun prix disponible
- Gestion des erreurs de conversion Decimal
- Import InvalidOperation pour gestion exceptions

📋 MODIFICATIONS
- stocks.py (lignes 1704-1727)
  * Récupération prix depuis formulaire avec validation
  * Fallback sur purchase_price_gnf du StockItem
  * Valeur par défaut 0 si aucun prix
  * Gestion exceptions ValueError et InvalidOperation

✅ RÉSULTAT
- Les réceptions peuvent être créées sans prix unitaire
- Le prix d'achat du StockItem est utilisé automatiquement
- Plus d'erreur IntegrityError sur unit_price_gnf"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Correction poussée avec succès!"

