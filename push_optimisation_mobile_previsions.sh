#!/bin/bash
# Script pour pousser l'optimisation mobile des prévisions et ventes

cd "$(dirname "$0")"

echo "🔄 Ajout des fichiers créés/modifiés..."
git add static/css/forecast_mobile_responsive.css
git add static/js/forecast_mobile_table_to_cards.js
git add templates/base_modern_complete.html
git add OPTIMISATION_MOBILE_PREVISIONS.md

echo "📝 Commit des optimisations..."
git commit -m "Feat: Optimisation mobile complète du module Prévisions & Ventes

- Création d'un CSS responsive dédié pour les prévisions
- Conversion automatique des tableaux en cartes sur mobile
- Optimisation des formulaires et boutons pour le toucher
- Adaptation des graphiques et statistiques
- Intégration conditionnelle dans le template de base
- Support complet pour smartphones et tablettes
- Amélioration de l'ergonomie pour les commerciaux mobiles"

echo "🚀 Push vers le dépôt distant..."
git push origin main

echo "✅ Optimisations poussées avec succès!"

