#!/bin/bash
# Script pour pousser la migration des fiches de prix vers stock_items

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add models.py \
    price_lists.py \
    templates/price_lists/form.html \
    templates/price_lists/detail.html \
    scripts/migrer_price_list_items_vers_stock_items_mysql.sql \
    scripts/migrer_price_list_items_vers_stock_items_postgresql.sql \
    MIGRATION_FICHES_PRIX_STOCK_ITEMS.md

echo ""
echo "💾 Création du commit..."
git commit -m "feat: Migration fiches de prix vers articles de stock (StockItem)

Objectif:
Les fiches de prix utilisent maintenant les articles de stock (StockItem) 
au lieu des articles standards (Article), conformément à la demande.

Modifications apportées:

1. Modèle PriceListItem (models.py):
   - article_id → stock_item_id
   - Relation Article → Relation StockItem
   - Contrainte unique mise à jour
   - Index mis à jour

2. Routes price_lists.py:
   - Article.query → StockItem.query
   - Groupement par Category → Groupement par Family
   - article_ids[] → stock_item_ids[]
   - Toutes les références article → stock_item

3. Templates:
   - form.html: Sélecteur d'articles de stock avec SKU
   - detail.html: Affichage groupé par famille
   - JavaScript mis à jour pour stock_items
   - Filtres par famille au lieu de catégorie

4. Scripts de migration SQL:
   - MySQL: migrer_price_list_items_vers_stock_items_mysql.sql
   - PostgreSQL: migrer_price_list_items_vers_stock_items_postgresql.sql
   - ⚠️ ATTENTION: Supprime toutes les données existantes de price_list_items

⚠️ IMPORTANT:
- Les fiches de prix existantes seront vidées de leurs articles
- Les utilisateurs devront recréer les fiches avec les articles de stock
- Migration nécessaire sur la base de données avant utilisation

Articles de stock accessibles via:
- /referentiels/stock-items

Documentation:
- MIGRATION_FICHES_PRIX_STOCK_ITEMS.md"

echo ""
echo "🚀 Push vers origin/main..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Modifications poussées avec succès!"
    echo ""
    echo "⚠️  PROCHAINES ÉTAPES:"
    echo "   1. Exécuter la migration SQL sur la base de données"
    echo "   2. Tester la création d'une nouvelle fiche de prix"
    echo "   3. Vérifier que les articles de stock s'affichent correctement"
else
    echo ""
    echo "❌ Erreur lors du push. Vérifiez votre connexion et vos permissions Git."
    exit 1
fi

