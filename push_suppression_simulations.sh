#!/bin/bash
# Script pour pousser la fonctionnalité de suppression des simulations

cd "$(dirname "$0")"

echo "🔄 Ajout des fichiers modifiés..."
git add app.py templates/simulations_ultra_modern_v3.html templates/simulation_detail.html

echo "📝 Commit des modifications..."
git commit -m "Feat: Ajout de la fonctionnalité de suppression des simulations pour les administrateurs

- Création de la route /simulations/<id>/delete (POST)
- Vérification que seul l'admin peut supprimer
- Suppression en cascade des SimulationItem associés
- Ajout du bouton de suppression dans la liste des simulations
- Ajout du bouton de suppression dans la page de détail
- Confirmation avant suppression pour éviter les erreurs"

echo "🚀 Push vers le dépôt distant..."
git push origin main

echo "✅ Fonctionnalité poussée avec succès!"

