#!/bin/bash
# Script pour pousser la correction unit_price_gnf et la vérification des transferts

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py VERIFICATION_LOGIQUE_TRANSFERTS.md EXEMPLE_TRANSFERT_GRAND_HANGAR.md push_fix_unit_price_reception.sh

echo ""
echo "📝 Création du commit..."
git commit -m "Fix: Correction unit_price_gnf NULL + Vérification logique transferts

🐛 PROBLÈME 1: unit_price_gnf NULL dans réceptions
- Erreur: Column 'unit_price_gnf' cannot be null
- Le code essayait d'insérer None pour unit_price_gnf
- Incohérence entre modèle Python (nullable=True) et DB (NOT NULL)

✅ SOLUTION 1
- Utilisation du prix d'achat du StockItem si prix non fourni
- Valeur par défaut 0 si aucun prix disponible
- Gestion des erreurs de conversion Decimal
- Import InvalidOperation pour gestion exceptions

📋 MODIFICATIONS stocks.py
- Lignes 1704-1727: Récupération prix avec validation
  * Fallback sur purchase_price_gnf du StockItem
  * Valeur par défaut 0 si aucun prix
  * Gestion exceptions ValueError et InvalidOperation

✅ VÉRIFICATION 2: Logique des transferts
- Documentation de la logique de conservation du stock global
- Exemple concret: Grand Hangar → Amadou
- Vérification que les transferts respectent:
  * Stock global constant (10 cartons)
  * Grand Hangar: 5 (10 - 5)
  * Amadou: 5 (0 + 5)
  * Mouvements: SORTIE (-5) + ENTRÉE (+5)

📄 DOCUMENTS CRÉÉS
- VERIFICATION_LOGIQUE_TRANSFERTS.md: Analyse technique complète
- EXEMPLE_TRANSFERT_GRAND_HANGAR.md: Exemple concret avec calculs

✅ RÉSULTAT
- Les réceptions peuvent être créées sans prix unitaire
- Le prix d'achat du StockItem est utilisé automatiquement
- Plus d'erreur IntegrityError sur unit_price_gnf
- Logique des transferts vérifiée et documentée"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Mise à jour poussée avec succès!"

