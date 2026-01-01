#!/bin/bash
# Script pour vérifier et pousser les corrections d'import stock-items sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "🔍 Vérification de l'état Git..."
git status

echo ""
echo "📋 Vérification des modifications dans referentiels.py..."
if git diff --quiet referentiels.py; then
    echo "   ✅ Aucune modification non committée dans referentiels.py"
else
    echo "   ⚠️  Modifications détectées dans referentiels.py"
    echo "   📝 Aperçu des modifications:"
    git diff --stat referentiels.py
fi

echo ""
echo "📋 Vérification des modifications dans update_permissions_render.py..."
if git diff --quiet update_permissions_render.py 2>/dev/null; then
    echo "   ✅ Aucune modification non committée dans update_permissions_render.py"
else
    echo "   ⚠️  Modifications détectées dans update_permissions_render.py"
    echo "   📝 Aperçu des modifications:"
    git diff --stat update_permissions_render.py
fi

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add referentiels.py update_permissions_render.py 2>/dev/null

# Vérifier s'il y a quelque chose à committer
if git diff --cached --quiet; then
    echo ""
    echo "ℹ️  Aucune modification à committer. Les fichiers sont déjà à jour."
    echo ""
    echo "📊 État final:"
    git status --short
    exit 0
fi

echo ""
echo "💾 Création du commit..."
git commit -m "fix: Correction finale import stock-items - gestion colonnes avec parenthèses

Problème résolu:
- Le prix d'achat n'était pas importé malgré la détection de la colonne
- Colonnes avec parenthèses (ex: prix_achat_(gnf), poids_(kg)) non gérées correctement
- Colonnes stock_min_depôt et stock_min_vehicule non détectées

Corrections apportées:

1. Détection améliorée des colonnes:
   - Gestion des parenthèses dans les noms de colonnes (prix_achat_(gnf))
   - Recherche flexible pour poids: détecte poids_(kg) en cherchant 'poids' dans le nom
   - Recherche flexible pour stock_min_depôt: gère les accents et variantes
   - Recherche flexible pour stock_min_vehicule: gère les accents et variantes

2. Lecture améliorée des valeurs:
   - Accès par index (row.iloc[col_idx]) pour éviter les problèmes avec parenthèses
   - Nettoyage renforcé: suppression espaces insécables, virgules, caractères non numériques
   - Gestion robuste des valeurs NaN, None, chaînes vides
   - Logs de debug pour les 3 premières lignes (prix importés)

3. Script Python pour Render:
   - update_permissions_render.py: Script optimisé pour mise à jour permissions sur Render
   - Détection automatique environnement (Render/local)
   - Messages détaillés et gestion d'erreurs

Format de colonnes maintenant supporté:
- Prix: prix_achat_(gnf), prix_achat_gnf, prix, price, etc.
- Poids: poids_(kg), poids_kg, poids, weight, etc.
- Stock Min: stock_min_depôt, stock_min_depot, stock_min_vehicule, etc.

Test validé:
- Colonne 'prix_achat_(gnf)' correctement détectée et lue
- Colonnes avec parenthèses gérées via accès par index"

if [ $? -eq 0 ]; then
    echo "   ✅ Commit créé avec succès"
else
    echo "   ❌ Erreur lors de la création du commit"
    exit 1
fi

echo ""
echo "🚀 Push vers origin/main..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Modifications poussées avec succès!"
    echo ""
    echo "📊 État final:"
    git status --short
else
    echo ""
    echo "❌ Erreur lors du push. Vérifiez votre connexion et vos permissions Git."
    exit 1
fi

