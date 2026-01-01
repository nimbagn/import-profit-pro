#!/bin/bash
# Script pour pousser l'ajout des modules RH sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout du fichier modifié..."
git add auth.py

echo "💾 Création du commit..."
git commit -m "feat: Ajout modules RH dans formulaire edition roles

- Ajout module employees (Employés Externes)
- Ajout module contracts (Contrats de travail)
- Ajout module trainings (Formations et certifications)
- Ajout module evaluations (Évaluations de performance)
- Ajout module absences (Absences et congés)
- Tous les modules RH sont maintenant visibles dans le formulaire d'édition des rôles
- Permet de configurer les permissions RH pour chaque rôle"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

