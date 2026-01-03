#!/bin/bash
# Script pour pousser toutes les modifications sur Git
# Date : 2 Janvier 2026

echo "🚀 PUSH COMPLET : TOUTES LES MODIFICATIONS SUR GIT"
echo "=================================================="
echo ""

# Ajouter tous les fichiers modifiés
echo "📦 Ajout de tous les fichiers modifiés..."
git add -A

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "feat: Migration complète PostgreSQL et restrictions valeurs stock

✨ Nouvelles fonctionnalités :
- Script de migration complète PostgreSQL pour Render
- Restriction d'affichage des valeurs de stock pour certains rôles
- Retours fournisseurs (mouvement inverse des réceptions)
- Notes et date modifiable pour mouvements de stock
- Solde progressif hiérarchisé dans historique stock

🔧 Modifications base de données :
- Colonne additional_permissions dans users
- Migration price_list_items : article_id → stock_item_id
- Colonne reference dans stock_movements
- unit_price_gnf nullable dans reception_details
- Retours fournisseurs : return_type, supplier_name, original_reception_id
- Type de mouvement 'reception_return' dans movement_type
- Permissions rôle magasinier (warehouse)
- Permissions rôle rh_assistant

🔒 Restrictions valeurs stock :
- Magasinier, Superviseur, Commercial : Ne peuvent pas voir les valeurs
- Admin : Voit toutes les valeurs
- Nouvelle fonction can_view_stock_values(user)

📝 Scripts SQL :
- scripts/migration_complete_postgresql_render.sql : Migration complète
- GUIDE_MIGRATION_COMPLETE_RENDER.md : Guide d'exécution
- EXECUTER_MIGRATION_RENDER.txt : Guide rapide

🎨 Modifications templates :
- Masquage des valeurs selon permissions
- Amélioration affichage notes et dates
- Solde progressif chronologique

📚 Documentation :
- RESTRICTION_VALEURS_STOCK.md
- GUIDE_MIGRATION_COMPLETE_RENDER.md
- EXECUTER_MIGRATION_RENDER.txt"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

