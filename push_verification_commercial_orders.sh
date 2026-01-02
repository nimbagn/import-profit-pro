#!/bin/bash
# Script pour pousser la vérification des autorisations commercial

cd "$(dirname "$0")"

echo "🔄 Ajout des fichiers créés..."
git add scripts/verifier_autorisations_commercial_orders.py
git add VERIFICATION_AUTORISATIONS_COMMERCIAL_ORDERS.md
git add RAPPORT_VERIFICATION_COMMERCIAL_ORDERS.md
git add RESUME_VERIFICATION_COMMERCIAL_ORDERS.md

echo "📝 Commit de la vérification..."
git commit -m "Docs: Vérification complète des autorisations commercial pour les commandes

- Vérification de toutes les routes /orders/
- Confirmation des permissions du rôle commercial
- Vérification de la sécurité et du filtrage
- Documentation complète des routes accessibles/inaccessibles
- Script de vérification automatique
- Rapport détaillé de conformité"

echo "🚀 Push vers le dépôt distant..."
git push origin main

echo "✅ Vérification poussée avec succès!"

