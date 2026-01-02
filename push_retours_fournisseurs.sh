#!/bin/bash
# Script pour pousser les modifications des retours fournisseurs sur Git
# Date : 2 Janvier 2026

echo "🚀 PUSH : RETOURS FOURNISSEURS - MOUVEMENT INVERSE DES RÉCEPTIONS"
echo "=================================================================="
echo ""

# Ajouter tous les fichiers modifiés
echo "📦 Ajout des fichiers modifiés..."
git add models.py stocks.py
git add templates/stocks/return_form.html
git add templates/stocks/movement_form.html
git add templates/stocks/movement_detail.html
git add templates/stocks/stock_history.html
git add scripts/migration_retours_fournisseurs_mysql.sql
git add scripts/migration_retours_fournisseurs_postgresql.sql
git add scripts/migration_movement_type_reception_return_mysql.sql
git add scripts/migration_movement_type_reception_return_postgresql.sql
git add scripts/migration_retours_fournisseurs.py
git add ANALYSE_RECEPTIONS_VS_RETOURS.md
git add IMPLEMENTATION_RETOURS_FOURNISSEURS.md
git add GUIDE_PUSH_RETOURS_FOURNISSEURS.md

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "feat: Implémentation retours fournisseurs et améliorations mouvements

✨ Nouvelles fonctionnalités :
- Retours fournisseurs (mouvement inverse des réceptions)
- Type de retour : client ou supplier
- Nouveau type de mouvement 'reception_return'
- Champ notes opération pour mouvements de stock
- Date d'enregistrement modifiable pour mouvements
- Solde progressif hiérarchisé dans historique stock

🔧 Modifications modèles :
- StockReturn : return_type, supplier_name, original_reception_id
- StockMovement : type 'reception_return' ajouté
- client_name rendu nullable pour retours fournisseurs

🔧 Modifications routes :
- return_new : Gestion deux types retours (client/fournisseur)
- Retours fournisseurs : quantité négative, vérification stock
- movement_new : Support notes et date modifiable

🎨 Modifications templates :
- return_form.html : Sélecteur type retour, sections conditionnelles
- movement_form.html : Champ notes et date modifiable
- movement_detail.html : Affichage amélioré notes
- stock_history.html : Solde progressif chronologique

📝 Migrations :
- Scripts SQL MySQL/PostgreSQL pour nouvelles colonnes
- Script Python automatique migration_retours_fournisseurs.py
- Migration type 'reception_return' dans enum movement_type

📚 Documentation :
- ANALYSE_RECEPTIONS_VS_RETOURS.md
- IMPLEMENTATION_RETOURS_FOURNISSEURS.md"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

