#!/bin/bash
# Script pour pousser les modifications d'import/export Excel stock-items et gestion catégories sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add referentiels.py templates/referentiels/stock_items_list.html templates/referentiels/stock_items_import.html GUIDE_TEST_IMPORT_EXPORT_STOCK_ITEMS.md app.py templates/articles_unified.html templates/articles/categories_list.html templates/articles/category_form.html

echo "💾 Création du commit..."
git commit -m "feat: Ajout import/export Excel pour stock-items et gestion catégories articles

Stock Items:
- Route d'export Excel avec filtres appliqués (/referentiels/stock-items/export/excel)
- Route d'import Excel/CSV avec validation (/referentiels/stock-items/import)
- Template d'import avec interface glisser-déposer
- Boutons import/export ajoutés dans la liste des stock-items
- Support de 3 modes de traitement des articles existants (ignorer, mettre à jour, créer nouveau)
- Création automatique des familles lors de l'import
- Validation des colonnes avec mapping flexible (SKU, Nom, Famille, Prix, Poids, Seuils)
- Gestion des erreurs avec messages clairs
- Guide de test complet créé
- Permissions vérifiées (stock_items.read pour export, stock_items.create pour import)
- Support formats .xlsx, .xls, .csv

Catégories Articles:
- Route liste catégories (/articles/categories)
- Route création catégorie (/articles/categories/new)
- Route modification catégorie (/articles/categories/<id>/edit)
- Route suppression catégorie (/articles/categories/<id>/delete)
- Templates liste et formulaire catégories
- Bouton Catégories ajouté dans la page articles
- Protection contre suppression si articles associés
- Permissions vérifiées (articles.read, articles.create, articles.update, articles.delete)"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

