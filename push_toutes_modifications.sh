#!/bin/bash
# Script pour pousser toutes les modifications (import prix/doublons + permissions magasinier) sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout de tous les fichiers modifiés..."
git add referentiels.py \
    app.py \
    scripts/ajouter_permissions_magasinier_mysql.sql \
    scripts/ajouter_permissions_magasinier_postgresql.sql \
    scripts/mettre_a_jour_permissions_magasinier_render.py \
    mettre_a_jour_permissions_magasinier.py \
    test_permissions_magasinier.py \
    GUIDE_PERMISSIONS_MAGASINIER.md \
    GUIDE_TEST_PERMISSIONS_MAGASINIER_LOCAL.md \
    GUIDE_EXECUTER_SCRIPT_RENDER.md \
    GUIDE_RAPIDE_RENDER.md \
    GUIDE_MISE_A_JOUR_PERMISSIONS_RENDER.md \
    push_permissions_magasinier.sh \
    push_fix_import_prix_doublons.sh

echo "💾 Création du commit..."
git commit -m "fix: Amélioration import stock-items et permissions magasinier complètes

1. CORRECTION IMPORT STOCK-ITEMS:
   - Détection améliorée de la colonne de prix (plus de variantes acceptées)
   - Recherche par contenu si aucune variante exacte trouvée
   - Traitement amélioré des valeurs (nettoyage virgules/espaces)
   - Prévention des doublons (normalisation SKU, tracking dans fichier)
   - Recherche insensible à la casse pour articles existants
   - Messages de debug détaillés

2. PERMISSIONS MAGASINIER COMPLÈTES:
   - Ajout permissions manquantes: receptions, outgoings, returns, orders, stock_loading
   - Scripts SQL pour MySQL et PostgreSQL
   - Script Python pour mise à jour automatique
   - Guides complets d'exécution sur Render

Fichiers modifiés:
- referentiels.py: Import amélioré (prix + doublons)
- app.py: Permissions complètes rôle magasinier

Scripts créés:
- scripts/mettre_a_jour_permissions_magasinier_render.py: Script Python pour Render
- scripts/ajouter_permissions_magasinier_postgresql.sql: Script SQL PostgreSQL
- scripts/ajouter_permissions_magasinier_mysql.sql: Script SQL MySQL
- mettre_a_jour_permissions_magasinier.py: Script Python local
- test_permissions_magasinier.py: Script de test automatique

Documentation:
- GUIDE_PERMISSIONS_MAGASINIER.md: Guide complet permissions
- GUIDE_TEST_PERMISSIONS_MAGASINIER_LOCAL.md: Guide test local
- GUIDE_EXECUTER_SCRIPT_RENDER.md: Guide exécution SQL Render
- GUIDE_RAPIDE_RENDER.md: Guide rapide Render
- GUIDE_MISE_A_JOUR_PERMISSIONS_RENDER.md: Guide mise à jour Render"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Toutes les modifications poussées avec succès!"

