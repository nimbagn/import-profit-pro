#!/bin/bash
# Script pour pousser la correction de stock_summary sur Git
# Date : 3 Janvier 2026

echo "🚀 PUSH : CORRECTION stock_summary"
echo "===================================="
echo ""

# Ajouter le fichier modifié
echo "📦 Ajout du fichier modifié..."
git add stocks.py

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "fix: Correction NameError can_view_values dans stock_summary

🐛 Bug corrigé :
- NameError: name 'can_view_values' is not defined
- Ligne 4195 dans stocks.py

✅ Solution :
- Import de can_view_stock_values depuis auth
- Calcul conditionnel de total_value selon can_view_values
- Variable can_view_values définie avant utilisation

📝 Fichiers modifiés :
- stocks.py : Ajout import et définition can_view_values"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

