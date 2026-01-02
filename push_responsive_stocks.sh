#!/bin/bash
# Script pour pousser les améliorations responsive mobile du module stocks

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers créés..."
git add static/css/stocks_mobile_responsive.css \
    static/js/stocks_mobile_table_to_cards.js \
    templates/base_modern_complete.html \
    AMELIORATION_RESPONSIVE_STOCKS.md

echo ""
echo "💾 Création du commit..."
git commit -m "feat: Amélioration responsive mobile du module stocks

Objectif:
Rendre le module stocks entièrement responsive et facilement utilisable 
sur mobile pour les magasiniers.

Fichiers créés:
1. static/css/stocks_mobile_responsive.css
   - CSS responsive complet pour le module stocks
   - Optimisé pour smartphones et tablettes
   - Touch targets ≥ 44x44px (Apple HIG, Material Design)
   - Conversion tableaux → cartes sur mobile
   - Breakpoints: 768px (mobile), 480px (petit mobile)

2. static/js/stocks_mobile_table_to_cards.js
   - Conversion automatique des tableaux en cartes sur mobile
   - Détection responsive dynamique
   - Observer DOM pour tableaux chargés dynamiquement
   - Gestion du redimensionnement de fenêtre

3. AMELIORATION_RESPONSIVE_STOCKS.md
   - Documentation complète des améliorations
   - Guide d'utilisation pour développeurs
   - Checklist de déploiement

Modifications:
- templates/base_modern_complete.html
  - Inclusion automatique du CSS pour routes stocks.*
  - Inclusion automatique du JavaScript pour routes stocks.*

Fonctionnalités:
✅ Layout adaptatif (marges, padding)
✅ Header responsive (titres, boutons)
✅ Filtres optimisés (grille 1 colonne)
✅ Tableaux → Cartes automatique
✅ Formulaires tactiles (champs ≥ 44px)
✅ Statistiques empilées
✅ Pagination simplifiée
✅ Touch targets optimisés
✅ Support orientation paysage
✅ Très petits écrans (< 480px)

Templates affectés (automatiquement):
- Tous les templates du module stocks
- receptions_list, movements_list, outgoings_list, returns_list
- stock_summary, stock_history, warehouse_dashboard
- depot_stock, vehicle_stock, low_stock
- Et tous les autres templates stocks

Test recommandé:
- Tester sur différents appareils (iPhone, Android, iPad)
- Valider avec des magasiniers réels
- Vérifier toutes les opérations (réceptions, sorties, transferts)"

echo ""
echo "🚀 Push vers origin/main..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Modifications poussées avec succès!"
    echo ""
    echo "📱 Pour tester:"
    echo "   1. Ouvrir https://import-profit-pro.onrender.com/stocks sur mobile"
    echo "   2. Vérifier que les tableaux sont convertis en cartes"
    echo "   3. Tester les formulaires et boutons"
    echo "   4. Valider avec des magasiniers"
else
    echo ""
    echo "❌ Erreur lors du push. Vérifiez votre connexion et vos permissions Git."
    exit 1
fi

