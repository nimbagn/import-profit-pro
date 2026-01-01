#!/bin/bash
# Script pour pousser les modifications d'import/export Excel des articles sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add app.py templates/articles_unified.html templates/articles_import.html GUIDE_TEST_IMPORT_EXPORT_ARTICLES.md test_articles_import_export.py

echo "💾 Création du commit..."
git commit -m "feat: Ajout import/export Excel pour les articles

- Route d'export Excel avec filtres appliqués (/articles/export/excel)
- Route d'import Excel/CSV avec validation (/articles/import)
- Template d'import avec interface glisser-déposer
- Boutons import/export ajoutés dans la liste des articles
- Support de 3 modes de traitement des articles existants (ignorer, mettre à jour, créer nouveau)
- Création automatique des catégories lors de l'import
- Validation des colonnes avec mapping flexible
- Gestion des erreurs avec messages clairs
- Guide de test complet créé
- Script de test pour générer fichier Excel exemple
- Permissions vérifiées (articles.read pour export, articles.create pour import)
- Support formats .xlsx, .xls, .csv"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

