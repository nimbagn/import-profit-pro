#!/bin/bash
# Script pour pousser les corrections du dashboard flotte sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout du fichier modifié..."
git add flotte.py

echo "💾 Création du commit..."
git commit -m "fix: Ajout filtrage par region dans dashboard flotte et amelioration gestion erreurs

- Ajout filtrage par region pour toutes les requetes de vehicules
- Statistiques globales filtrees par region (total, actifs, inactifs, maintenance)
- Vehicules sans conducteur filtres par region
- Documents expires/expirant filtres par region
- Maintenances dues filtrees par region
- Vehicules recents filtres par region
- Maintenances recentes filtrees par region
- Optimisation: recuperation unique de accessible_vehicle_ids
- Amelioration gestion erreurs PostgreSQL avec db.session.rollback()
- Meilleur logging des erreurs avec traceback
- Les admins voient tous les vehicules, les autres utilisateurs voient uniquement leur region"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

