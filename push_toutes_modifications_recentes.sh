#!/bin/bash
# Script pour pousser toutes les modifications récentes sur Git

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout de tous les fichiers modifiés et nouveaux..."
git add -A

echo ""
echo "📝 Création du commit..."
git commit -m "Feat: Améliorations multiples - Mobile, Autorisations, Inventaire, Simulations

- Optimisation mobile complète du module Prévisions & Ventes
  * CSS responsive dédié pour mobile
  * Conversion automatique tableaux en cartes
  * Optimisation pour smartphones et tablettes

- Vérification complète des autorisations commercial pour /orders/
  * Documentation de toutes les routes
  * Script de vérification automatique
  * Confirmation de la sécurité et conformité

- Correction des couleurs des écarts d'inventaire
  * Écart = 0 → Vert (conforme)
  * Écart > 0 → Rouge (manquant)
  * Écart < 0 → Orange (surplus)

- Fonctionnalité de suppression des simulations pour admin
  * Route /simulations/<id>/delete
  * Boutons dans liste et détail
  * Vérification admin uniquement

- Amélioration affichage prix d'achat dans liste articles de stock
  * Gestion des valeurs None
  * Formatage conditionnel

- Scripts de migration fiches de prix vers stock_items
  * Migration MySQL et PostgreSQL
  * Script Python d'exécution"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Toutes les modifications ont été poussées avec succès!"

