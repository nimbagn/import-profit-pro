#!/bin/bash
# Script pour pousser les modifications du dashboard admin sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add app.py templates/index_hapag_lloyd.html

echo "💾 Création du commit..."
git commit -m "feat: Actualisation dashboard admin avec toutes les donnees reelles de la base de donnees

- Ajout statistiques commandes commerciales (total, en attente, validées, annulées)
- Ajout statistiques promotion (équipes, membres, ventes du jour, retours en attente)
- Ajout statistiques RH supplémentaires (formations en cours)
- Affichage commandes récentes dans le dashboard
- Affichage ventes promotion récentes dans le dashboard
- Suppression données de démonstration en fallback (affichage zéros à la place)
- Toutes les données proviennent directement de la base de données
- Filtrage par région respecté pour l'admin (voit tout)"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

