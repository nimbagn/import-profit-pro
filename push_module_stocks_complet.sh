#!/bin/bash
# Script pour pousser toutes les modifications du module stocks sur Git
# Date : 2 Janvier 2026

echo "🚀 PUSH COMPLET : MODULE STOCKS SUR GIT"
echo "========================================"
echo ""

# Ajouter tous les fichiers modifiés
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py
git add models.py
git add auth.py
git add analytics.py
git add flotte.py
git add templates/stocks/*.html
git add templates/analytics/dashboard.html
git add templates/flotte/vehicle_detail.html
git add scripts/fix_stock_movements_postgresql.sql
git add scripts/fix_stocks_tables_postgresql.sql
git add scripts/migration_stocks_complete_postgresql.sql
git add scripts/migration_complete_postgresql_render.sql
git add GUIDE_FIX_STOCK_MOVEMENTS_RENDER.md
git add EXECUTER_FIX_STOCK_MOVEMENTS_RENDER.txt
git add RESTRICTION_VALEURS_STOCK.md
git add GUIDE_MIGRATION_COMPLETE_RENDER.md
git add EXECUTER_MIGRATION_RENDER.txt
git add GUIDE_PUSH_COMPLET_GIT.md
git add GUIDE_PUSH_FIX_STOCK_MOVEMENTS.md
git add push_*.sh

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "fix: Correction complète module stocks pour Render

🔧 Corrections base de données :
- Script fix_stock_movements_postgresql.sql : Correction table stock_movements
- Script fix_stocks_tables_postgresql.sql : Correction depot_stocks et vehicle_stocks
- Script migration_stocks_complete_postgresql.sql : Migration complète module stocks
- Script migration_complete_postgresql_render.sql : Mis à jour avec toutes les corrections

✨ Fonctionnalités :
- Restriction d'affichage des valeurs de stock pour certains rôles
- Retours fournisseurs (mouvement inverse des réceptions)
- Notes et date modifiable pour mouvements de stock
- Solde progressif hiérarchisé dans historique stock

🔒 Restrictions valeurs stock :
- Magasinier, Superviseur, Commercial : Ne peuvent pas voir les valeurs
- Admin : Voit toutes les valeurs
- Nouvelle fonction can_view_stock_values(user)

📝 Tables corrigées :
- stock_movements : Type ENUM, colonne reference, FK, index
- depot_stocks : Création, FK, index, synchronisation depuis mouvements
- vehicle_stocks : Création, FK, index, synchronisation depuis mouvements

🎯 Objectif :
Corriger l'erreur 'Stock insuffisant' sur Render en synchronisant
les tables depot_stocks et vehicle_stocks depuis stock_movements

📚 Documentation :
- GUIDE_FIX_STOCK_MOVEMENTS_RENDER.md
- EXECUTER_FIX_STOCK_MOVEMENTS_RENDER.txt
- RESTRICTION_VALEURS_STOCK.md
- GUIDE_MIGRATION_COMPLETE_RENDER.md"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

