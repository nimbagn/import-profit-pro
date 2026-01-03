#!/bin/bash
# Script pour pousser le fix stock_movements sur Git
# Date : 2 Janvier 2026

echo "🚀 PUSH : FIX stock_movements POUR RENDER"
echo "=========================================="
echo ""

# Ajouter les fichiers
echo "📦 Ajout des fichiers..."
git add scripts/fix_stock_movements_postgresql.sql
git add GUIDE_FIX_STOCK_MOVEMENTS_RENDER.md
git add EXECUTER_FIX_STOCK_MOVEMENTS_RENDER.txt
git add scripts/migration_complete_postgresql_render.sql

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "fix: Script SQL PostgreSQL pour corriger stock_movements sur Render

🔧 Correction table stock_movements :
- Type ENUM movement_type avec toutes les valeurs (reception_return)
- Colonne reference (si manquante)
- Toutes les contraintes FK (from_depot, to_depot, from_vehicle, to_vehicle)
- Tous les index nécessaires pour les performances
- Vérifications complètes

📝 Scripts SQL :
- scripts/fix_stock_movements_postgresql.sql : Script de correction dédié
- scripts/migration_complete_postgresql_render.sql : Mis à jour avec corrections stock_movements

📚 Documentation :
- GUIDE_FIX_STOCK_MOVEMENTS_RENDER.md : Guide d'exécution
- EXECUTER_FIX_STOCK_MOVEMENTS_RENDER.txt : Guide rapide

🎯 Objectif :
Corriger la route /stocks/movements qui ne fonctionne pas sur Render"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

