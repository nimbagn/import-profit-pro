#!/bin/bash
# Script pour pousser les corrections des couleurs d'inventaire

cd "$(dirname "$0")"

echo "🔄 Ajout des fichiers modifiés..."
git add templates/inventaires/session_detail.html

echo "📝 Commit des corrections..."
git commit -m "Fix: Correction des couleurs des écarts d'inventaire

- Écart = 0 (conforme) → Vert ✅
- Écart > 0 (manquant) → Rouge ❌ (quantité système > quantité comptée)
- Écart < 0 (surplus) → Orange ⚠️ (quantité comptée > quantité système)
- Correction des graphiques et statistiques
- Mise à jour des libellés des filtres"

echo "🚀 Push vers le dépôt distant..."
git push origin main

echo "✅ Corrections poussées avec succès!"

