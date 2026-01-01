#!/bin/bash
# Script pour pousser les corrections d'affichage du prix d'achat

cd "$(dirname "$0")"

echo "🔄 Ajout des fichiers modifiés..."
git add templates/referentiels/stock_items_list.html scripts/verifier_prix_articles_stock.py

echo "📝 Commit des corrections..."
git commit -m "Fix: Amélioration de l'affichage du prix d'achat dans la liste des articles de stock

- Gestion des valeurs None pour le prix d'achat
- Affichage conditionnel avec formatage approprié
- Ajout d'un script de vérification des prix dans la base de données"

echo "🚀 Push vers le dépôt distant..."
git push origin main

echo "✅ Corrections poussées avec succès!"

