#!/bin/bash
# Script pour pousser les modifications de restriction des valeurs de stock sur Git
# Date : 2 Janvier 2026

echo "🚀 PUSH : RESTRICTION D'AFFICHAGE DES VALEURS DE STOCK"
echo "========================================================"
echo ""

# Ajouter tous les fichiers modifiés
echo "📦 Ajout des fichiers modifiés..."
git add auth.py
git add stocks.py
git add analytics.py
git add flotte.py
git add templates/stocks/stock_summary.html
git add templates/stocks/depot_stock.html
git add templates/stocks/vehicle_stock.html
git add templates/analytics/dashboard.html
git add templates/flotte/vehicle_detail.html
git add RESTRICTION_VALEURS_STOCK.md

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "feat: Restriction d'affichage des valeurs de stock pour certains rôles

🔒 Restrictions :
- Magasinier (warehouse) : Ne peut pas voir les valeurs monétaires
- Superviseur (supervisor) : Ne peut pas voir les valeurs monétaires
- Commercial (commercial) : Ne peut pas voir les valeurs monétaires
- Admin : Voit toutes les valeurs (tous les droits)

✨ Nouvelle fonction :
- can_view_stock_values(user) : Vérifie si l'utilisateur peut voir les valeurs

🔧 Modifications routes :
- stocks.py : depot_stock, vehicle_stock, stock_summary
- analytics.py : dashboard
- flotte.py : vehicle_detail

🎨 Modifications templates :
- templates/stocks/stock_summary.html : Masquage colonne et statistique valeur
- templates/stocks/depot_stock.html : Masquage colonne valeur
- templates/stocks/vehicle_stock.html : Masquage colonne et statistique valeur
- templates/analytics/dashboard.html : Masquage KPI valeur stock
- templates/flotte/vehicle_detail.html : Masquage colonnes prix et valeur

📝 Notes :
- Les quantités restent toujours visibles pour tous les rôles
- Seules les valeurs monétaires (GNF) sont masquées
- Les calculs sont toujours effectués côté serveur"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

