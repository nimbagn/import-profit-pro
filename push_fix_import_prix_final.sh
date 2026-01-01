#!/bin/bash
# Script pour pousser les corrections finales d'import stock-items sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add referentiels.py \
    update_permissions_render.py

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

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

