#!/bin/bash
# Script pour pousser les corrections d'import (prix et doublons) sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add referentiels.py

echo "💾 Création du commit..."
git commit -m "fix: Amélioration import stock-items - détection prix et prévention doublons

Problèmes résolus:
- Le prix d'achat était ignoré lors de l'import
- Risque de création de doublons lors de l'import

Corrections apportées:

1. Détection améliorée de la colonne de prix:
   - Ajout de nombreuses variantes de noms de colonnes (prix_achat_gnf, prix_gnf, prix_unitaire, etc.)
   - Recherche par contenu si aucune variante exacte trouvée (cherche colonnes contenant 'prix' ou 'price')
   - Messages de debug pour identifier la colonne détectée

2. Traitement amélioré des valeurs de prix:
   - Nettoyage automatique (suppression espaces, remplacement virgules par points)
   - Gestion robuste des erreurs de conversion
   - Messages d'erreur détaillés dans les logs

3. Prévention des doublons:
   - Normalisation du SKU (uppercase, trim) avant vérification
   - Détection des doublons dans le fichier Excel avant traitement
   - Tracking des SKUs traités dans la session d'import (set)
   - Recherche insensible à la casse pour détecter les articles existants
   - Message d'avertissement si doublons détectés dans le fichier
   - Ignore automatiquement les doublons dans le fichier (traite uniquement la première occurrence)

4. Messages de debug:
   - Affichage des colonnes détectées
   - Messages d'erreur détaillés pour le prix
   - Avertissements pour les doublons

Format de colonnes accepté pour le prix:
- Prix, Price, Prix Achat, Prix d'achat, Prix Achat GNF
- Prix Unitaire, Purchase Price GNF
- Toute colonne contenant 'prix' ou 'price'"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

