#!/bin/bash
# Script pour pousser les modifications des permissions magasinier sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add app.py \
    scripts/ajouter_permissions_magasinier_mysql.sql \
    scripts/ajouter_permissions_magasinier_postgresql.sql \
    mettre_a_jour_permissions_magasinier.py \
    test_permissions_magasinier.py \
    GUIDE_PERMISSIONS_MAGASINIER.md \
    GUIDE_TEST_PERMISSIONS_MAGASINIER_LOCAL.md

echo "💾 Création du commit..."
git commit -m "fix: Ajout permissions complètes pour le rôle magasinier

Problème résolu:
- Le magasinier n'avait pas accès à toutes les fonctionnalités du module /stocks
- Permissions manquantes: receptions, outgoings, returns, orders, stock_loading

Modifications:
- app.py: Ajout des permissions manquantes au rôle magasinier
  - receptions: ['read', 'create', 'update']
  - outgoings: ['read', 'create', 'update']
  - returns: ['read', 'create', 'update']
  - orders: ['read']
  - stock_loading: ['read', 'verify', 'load']

Scripts SQL:
- scripts/ajouter_permissions_magasinier_mysql.sql: Script complet pour MySQL
- scripts/ajouter_permissions_magasinier_postgresql.sql: Script complet pour PostgreSQL

Outils de test:
- mettre_a_jour_permissions_magasinier.py: Script Python pour mettre à jour les permissions
- test_permissions_magasinier.py: Script de test automatique des permissions

Documentation:
- GUIDE_PERMISSIONS_MAGASINIER.md: Guide complet des permissions
- GUIDE_TEST_PERMISSIONS_MAGASINIER_LOCAL.md: Guide de test local

Fonctionnalités maintenant accessibles au magasinier:
✅ Stocks: read, create, update
✅ Mouvements: read, create
✅ Réceptions: read, create, update
✅ Sorties: read, create, update
✅ Retours: read, create, update
✅ Inventaires: read, create, update
✅ Commandes: read
✅ Dashboard magasinier: read, verify, load
✅ Exports Excel/PDF pour tous les modules"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

