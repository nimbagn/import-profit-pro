#!/bin/bash
# Script pour pousser les révisions des autorisations du module flotte sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout des fichiers modifiés..."
git add flotte.py DOCUMENTATION_AUTORISATIONS_FLOTTE.md

echo "💾 Création du commit..."
git commit -m "fix: Revision complete des autorisations module flotte

- Ajout verification can_access_vehicle() dans toutes les routes avec vehicle_id
- Protection contre acces non autorise aux vehicules d'autres regions
- Ajout verification region pour route /users/<user_id>/vehicles
- 12 routes corrigees avec verification d'acces par region
- Documentation complete des autorisations creee
- Toutes les routes protegees avec @login_required
- Permissions vehicles.read pour consultations
- Permissions vehicles.update pour modifications
- Admin a acces a tous les vehicules (pas de filtre par region)
- Messages d'erreur clairs et explicites"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Modifications poussées avec succès!"

