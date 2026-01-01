#!/bin/bash
# Script pour vérifier le dernier commit et ajouter les scripts shell non suivis

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📋 Vérification du dernier commit..."
echo ""
git log -1 --oneline

echo ""
echo "📝 Fichiers modifiés dans le dernier commit:"
git show --name-only --pretty=format: HEAD | head -20

echo ""
echo "🔍 Vérification si les corrections d'import sont dans le dernier commit..."
if git log -1 --grep="import stock-items" --oneline > /dev/null 2>&1; then
    echo "   ✅ Les corrections d'import sont dans le dernier commit"
    git log -1 --grep="import stock-items" --oneline
else
    echo "   ⚠️  Les corrections d'import ne sont pas dans le dernier commit"
    echo "   📝 Recherche dans les 10 derniers commits..."
    git log --oneline --grep="import" -10 | head -5
fi

echo ""
echo "📦 Scripts shell non suivis détectés:"
git status --short | grep "^??" | grep "\.sh$" || echo "   Aucun script shell non suivi"

echo ""
read -p "Voulez-vous ajouter tous les scripts shell au dépôt Git? (o/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Oo]$ ]]; then
    echo "📦 Ajout des scripts shell..."
    git add *.sh
    
    echo ""
    echo "💾 Création du commit pour les scripts shell..."
    git commit -m "chore: Ajout des scripts shell de déploiement et maintenance

Scripts ajoutés:
- push_corrections_import.sh: Script pour pousser les corrections d'import
- push_autorisations_flotte.sh: Script pour pousser les autorisations flotte
- push_changes.sh: Script générique pour pousser les modifications
- push_fix_import_prix_final.sh: Script pour corriger l'import des prix
- push_fix_postgresql.sh: Script pour les corrections PostgreSQL
- push_flotte_dashboard.sh: Script pour le dashboard flotte
- push_import_export_articles.sh: Script pour l'import/export articles
- push_modules_rh.sh: Script pour les modules RH
- push_stock_items_categories.sh: Script pour les catégories stock-items
- push_toutes_modifications.sh: Script pour pousser toutes les modifications
- verifier_et_ajouter_scripts.sh: Script de vérification et ajout

Ces scripts facilitent le déploiement et la maintenance de l'application."
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Commit créé avec succès"
        echo ""
        echo "🚀 Push vers origin/main..."
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Scripts shell ajoutés et poussés avec succès!"
        else
            echo ""
            echo "❌ Erreur lors du push."
        fi
    else
        echo "   ❌ Erreur lors de la création du commit"
    fi
else
    echo "   ℹ️  Ajout des scripts annulé"
fi

echo ""
echo "📊 État final:"
git status --short

